"""Opt-in first-handoff BLM capture and intervention for the C1 boundary.

This module deliberately implements one small, deterministic boundary rather
than a general intervention framework.  The request can only copy a value from
another adapter output after the donor and replay state have been checked.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from typing import Any, Dict, List, Mapping, Optional, Tuple

from skillstack.adapters.retrieval_to_execution import adapt_retrieval_for_execution
from skillstack.contracts import (
    NATIVE_SKILL_FIELDS,
    RETRIEVAL_CANDIDATE_FIELDS,
    RETRIEVAL_RESPONSE_FIELDS,
    require_fields,
)
from skillstack.execution.skillplan import (
    GENERIC_NO_SKILL_PLAN,
    PLAN_STEPS_BY_SKILL,
    RECEPTACLE_TYPE_ORDER,
)
from skillstack.retrieval import OracleSkillRetriever, RandomSkillRetriever
from skillstack.task_semantics import APPLIANCE_BY_SKILL, SYNONYMS, TRANSFORM_VERB_BY_SKILL


BLM_INTERVENTION_SCHEMA = "skillstack-blm-intervention-v1"
BLM_INTERVENTION_SCHEMA_V2 = "skillstack-blm-intervention-v2"
BLM_INTERVENTION_SCHEMA_V3 = "skillstack-blm-intervention-v3"
BLM_BOUNDARY_SCHEMA = "skillstack-blm-boundary-v1"
BLM_BOUNDARY_SCHEMA_V2 = "skillstack-blm-boundary-v2"
BLM_BOUNDARY_SCHEMA_V3 = "skillstack-blm-boundary-v3"
BOUNDARY_ID = "r1_00_c1_skillplan"
STATE_SCOPE = "first_handoff_reconstructed_fixture_v1"
INTERVENTION_POSITION = "post_adapter_pre_consumer_read"

_EXECUTION_FIELDS = (
    "selected_skill_ids",
    "selected_scores",
    "selected_native_skills",
    "flat_skill_context",
)
_REQUEST_FIELDS = {
    "schema_version",
    "arm_id",
    "operation",
    "atom",
    "expected_state_sha256",
    "donor",
}
_DONOR_FIELDS = {"kind", "task_id", "task_family", "state_sha256", "retrieval_response"}
_ATOMS = {
    "selected_skill_ids[0]",
    "selected_scores[0]",
    "selected_native_skills[0]",
    "flat_skill_context",
}
_GROUP_ATOMS = {"reference_handoff_group"}
_UNREAD_ATOMS = {
    "selected_scores[0]",
    "selected_native_skills[0]",
    "flat_skill_context",
}
_READ_MAP_IDS = {
    None: "r1_00_c1.skillplan.execution_input",
    "selected_skill_ids[0]": "r1_00_c1.skillplan.semantic.selected_skill_ids[0]",
    "selected_scores[0]": "r1_00_c1.skillplan.validation.selected_scores[0]",
    "selected_native_skills[0]": "r1_00_c1.skillplan.validation.selected_native_skills[0]",
    "flat_skill_context": "r1_00_c1.skillplan.validation.flat_skill_context",
    "reference_handoff_group": "r1_00_c1.skillplan.group.reference_handoff",
}
_FORBIDDEN_KEYS = {
    "action",
    "actions",
    "reward",
    "rewards",
    "done",
    "success",
    "trajectory",
    "trajectories",
    "future_observation",
    "future_observations",
}
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class _BoundaryValidationError(ValueError):
    """Expected request/donor validation failure with a stable public reason."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def apply_boundary_intervention(
    execution_input: Mapping[str, Any],
    request: Any,
    context: Mapping[str, Any],
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """Validate an opt-in request and return the effective first-handoff input.

    Known invalid requests are represented in the returned sidecar instead of
    being raised, so the Runner can stop before invoking the Consumer.  A
    programming error in the context still raises normally.
    """

    state_sha256 = boundary_state_sha256(context)
    original = copy.deepcopy(dict(execution_input))
    request_schema = (
        request.get("schema_version")
        if isinstance(request, Mapping)
        else BLM_BOUNDARY_SCHEMA
    )
    boundary_schema = (
        BLM_BOUNDARY_SCHEMA_V2
        if request_schema == BLM_INTERVENTION_SCHEMA_V2
        else BLM_BOUNDARY_SCHEMA
    )
    record = {
        "schema_version": boundary_schema,
        "boundary_id": BOUNDARY_ID,
        "state_scope": STATE_SCOPE,
        "arm_id": request.get("arm_id") if isinstance(request, Mapping) else None,
        "operation": request.get("operation") if isinstance(request, Mapping) else None,
        "atom": request.get("atom") if isinstance(request, Mapping) else None,
        "read_map_id": None,
        "state_sha256": state_sha256,
        "original_input_sha256": _hash_json(original),
        "effective_input_sha256": None,
        "changed": False,
        "donor_provenance": None,
        "intervention_position": INTERVENTION_POSITION,
        "validity": "invalid",
        "validity_reason": "invalid_request",
        "consumer_branch": None,
        "outcome_observation": None,
    }
    if boundary_schema == BLM_BOUNDARY_SCHEMA_V2:
        record["consumer_reads"] = []
    if isinstance(request, Mapping):
        atom = request.get("atom")
        if atom is None or isinstance(atom, str):
            record["read_map_id"] = _READ_MAP_IDS.get(atom)

    try:
        _validate_request(request)
        _validate_context(context)
        _validate_execution_input(original, "current execution input")
        arm_id = request["arm_id"]
        operation = request["operation"]
        atom = request["atom"]
        record["read_map_id"] = _READ_MAP_IDS.get(atom)
        _validate_arm(arm_id, operation, atom, request["schema_version"])

        expected_state = request["expected_state_sha256"]
        if operation == "capture":
            if expected_state is not None:
                raise _BoundaryValidationError("invalid_capture_state_field")
            effective = copy.deepcopy(original)
            record["validity_reason"] = "capture"
        else:
            if not _is_sha256(expected_state) or expected_state != state_sha256:
                raise _BoundaryValidationError("invalid_donor_state")
            donor = request["donor"]
            donor_input, provenance = _validate_donor(
                donor, context, arm_id, request["schema_version"]
            )
            effective = _copy_atom(original, donor_input, atom)
            record["donor_provenance"] = provenance
            record["validity_reason"] = "intervention_applied"

        record["effective_input_sha256"] = _hash_json(effective)
        record["changed"] = effective != original
        record["validity"] = "valid"
        return effective, record
    except _BoundaryValidationError as error:
        record["validity_reason"] = error.reason
        return None, record


def finalize_boundary_record(
    record: Mapping[str, Any],
    executor_report: Mapping[str, Any],
    consumer_reads: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Attach Consumer-only observations after a valid intervention executes."""

    finalized = copy.deepcopy(dict(record))
    if finalized.get("validity") != "valid":
        return finalized
    if finalized.get("schema_version") == BLM_BOUNDARY_SCHEMA_V2:
        finalized["consumer_reads"] = copy.deepcopy(consumer_reads or [])
    finalized["consumer_branch"] = executor_report.get("plan_skill_id")
    finalized["outcome_observation"] = {
        "success": bool(executor_report.get("success", False)),
        "stop_reason": executor_report.get("stop_reason"),
        "action_trace_sha256": _hash_json(executor_report.get("actions", [])),
    }
    return finalized


def boundary_state_sha256(context: Mapping[str, Any]) -> str:
    """Return the canonical first-handoff state identity used by C1."""

    state = {
        "state_scope": STATE_SCOPE,
        "task_record": context["task_record"],
        "initial_observation": context["initial_observation"],
        "initial_info": context["initial_info"],
        "environment_class": context["environment_class"],
        "consumer": {
            "name": context["consumer_name"],
            "step_budget_per_plan_step": context["consumer_step_budget"],
            "registry_sha256": _hash_json(_consumer_registry()),
        },
        "top_k": context["top_k"],
        "max_steps": context["effective_max_steps"],
    }
    return _hash_json(state)


def _validate_request(request: Any) -> None:
    if not isinstance(request, Mapping):
        raise _BoundaryValidationError("invalid_request_type")
    if request.get("schema_version") == BLM_INTERVENTION_SCHEMA_V2:
        _reject_forbidden_keys(request)
    if set(request) != _REQUEST_FIELDS:
        raise _BoundaryValidationError("invalid_request_schema")
    if request["schema_version"] not in {
        BLM_INTERVENTION_SCHEMA,
        BLM_INTERVENTION_SCHEMA_V2,
    }:
        raise _BoundaryValidationError("invalid_request_schema")
    if not isinstance(request["arm_id"], str) or not isinstance(request["operation"], str):
        raise _BoundaryValidationError("invalid_request_schema")
    allowed_operations = {"capture", "copy_atom_from_donor"}
    if request["schema_version"] == BLM_INTERVENTION_SCHEMA_V2:
        allowed_operations.add("copy_group_from_donor")
    if request["operation"] not in allowed_operations:
        raise _BoundaryValidationError("invalid_operation")
    atom = request["atom"]
    allowed_atoms = _ATOMS | (
        _GROUP_ATOMS if request["schema_version"] == BLM_INTERVENTION_SCHEMA_V2 else set()
    )
    if atom is not None and (not isinstance(atom, str) or atom not in allowed_atoms):
        raise _BoundaryValidationError("invalid_atom_type")


def _validate_context(context: Mapping[str, Any]) -> None:
    if context.get("consumer_name") != "skill_plan_executor":
        raise _BoundaryValidationError("unsupported_consumer")
    if context.get("state_scope", STATE_SCOPE) != STATE_SCOPE:
        raise _BoundaryValidationError("unsupported_state_scope")
    if not isinstance(context.get("top_k"), int) or context["top_k"] < 1:
        raise _BoundaryValidationError("invalid_context")
    if not isinstance(context.get("effective_max_steps"), int) or context["effective_max_steps"] < 1:
        raise _BoundaryValidationError("invalid_context")


def _validate_execution_input(value: Mapping[str, Any], label: str) -> None:
    try:
        require_fields(value, _EXECUTION_FIELDS, label)
    except ValueError as error:
        raise _BoundaryValidationError("invalid_current_input_schema") from error
    ids = value["selected_skill_ids"]
    scores = value["selected_scores"]
    native = value["selected_native_skills"]
    flat = value["flat_skill_context"]
    if not isinstance(ids, list) or not isinstance(scores, list) or not isinstance(native, list):
        raise _BoundaryValidationError("invalid_current_input_type")
    if not isinstance(flat, str):
        raise _BoundaryValidationError("invalid_current_input_type")
    if not (len(ids) == len(scores) == len(native)):
        raise _BoundaryValidationError("invalid_list_alignment")
    if any(not isinstance(skill_id, str) for skill_id in ids):
        raise _BoundaryValidationError("invalid_current_input_type")
    if any(not isinstance(payload, str) for payload in native):
        raise _BoundaryValidationError("invalid_current_input_type")
    if any(isinstance(score, bool) or not isinstance(score, (int, float)) for score in scores):
        raise _BoundaryValidationError("invalid_current_input_type")
    if any(not math.isfinite(float(score)) for score in scores):
        raise _BoundaryValidationError("invalid_current_input_type")


def _validate_arm(
    arm_id: str,
    operation: str,
    atom: Optional[str],
    schema_version: str = BLM_INTERVENTION_SCHEMA,
) -> None:
    if arm_id in {"reference", "crossed"}:
        if operation != "capture" or atom is not None:
            raise _BoundaryValidationError("invalid_arm_operation")
        return
    if arm_id == "crossed_noop":
        if operation != "copy_atom_from_donor" or atom != "selected_skill_ids[0]":
            raise _BoundaryValidationError("invalid_arm_operation")
        return
    if arm_id == "crossed_single_atom":
        if operation != "copy_atom_from_donor" or atom != "selected_skill_ids[0]":
            raise _BoundaryValidationError("invalid_arm_operation")
        return
    if arm_id == "irrelevant_unread_information":
        if operation != "copy_atom_from_donor" or atom not in _UNREAD_ATOMS:
            raise _BoundaryValidationError("invalid_arm_operation")
        return
    if schema_version == BLM_INTERVENTION_SCHEMA_V2:
        if arm_id == "matched_carrier_control":
            if operation != "copy_atom_from_donor" or atom != "selected_skill_ids[0]":
                raise _BoundaryValidationError("invalid_arm_operation")
            return
        if arm_id == "crossed_full_reference_restoration":
            if operation != "copy_group_from_donor" or atom != "reference_handoff_group":
                raise _BoundaryValidationError("invalid_arm_operation")
            return
    raise _BoundaryValidationError("invalid_arm")


def _validate_donor(
    donor: Any,
    context: Mapping[str, Any],
    arm_id: str,
    schema_version: str = BLM_INTERVENTION_SCHEMA,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    _reject_forbidden_keys(donor)
    if not isinstance(donor, Mapping) or set(donor) != _DONOR_FIELDS:
        raise _BoundaryValidationError("invalid_donor_schema")
    if not isinstance(donor["kind"], str) or donor["kind"] not in {
        "calibration_oracle",
        "producer_output",
        "matched_nonreference",
    }:
        raise _BoundaryValidationError("invalid_donor_kind")
    if not isinstance(donor["task_id"], str) or not isinstance(
        donor["task_family"], str
    ) or not isinstance(donor["state_sha256"], str):
        raise _BoundaryValidationError("invalid_donor_schema")
    if donor["task_id"] != context["task_record"]["task_id"]:
        raise _BoundaryValidationError("invalid_donor_task")
    if donor["task_family"] != context["task_record"]["task_family"]:
        raise _BoundaryValidationError("invalid_donor_task_family")
    if donor["state_sha256"] != boundary_state_sha256(context):
        raise _BoundaryValidationError("invalid_donor_state")
    retrieval_response = donor["retrieval_response"]
    _validate_retrieval_response(retrieval_response)
    candidates = retrieval_response["ranked_candidates"]
    if donor["kind"] == "calibration_oracle":
        if schema_version == BLM_INTERVENTION_SCHEMA_V2:
            expected = OracleSkillRetriever().retrieve(
                context["task_record"],
                context["initial_observation"],
                context["native_skills"],
                context["top_k"],
            )
        else:
            expected = None
        if expected is not None and retrieval_response != expected:
            raise _BoundaryValidationError("invalid_donor_source")
    elif donor["kind"] == "matched_nonreference":
        if arm_id != "matched_carrier_control":
            raise _BoundaryValidationError("invalid_donor_source")
        expected = RandomSkillRetriever(seed=3).retrieve(
            context["task_record"],
            context["initial_observation"],
            context["native_skills"],
            context["top_k"],
        )
        if schema_version == BLM_INTERVENTION_SCHEMA_V2 and retrieval_response != expected:
            raise _BoundaryValidationError("invalid_donor_source")
        if (
            candidates[0]["skill_id"]
            == context["retrieval_response"].get("ranked_candidates", [{}])[0].get("skill_id")
        ):
            raise _BoundaryValidationError("invalid_donor_source")
    elif arm_id != "crossed_noop":
        raise _BoundaryValidationError("invalid_donor_source")
    if arm_id == "crossed_noop" and retrieval_response != context["retrieval_response"]:
        raise _BoundaryValidationError("invalid_noop_donor")
    try:
        donor_input, _event = adapt_retrieval_for_execution(retrieval_response)
    except (TypeError, ValueError, KeyError) as error:
        raise _BoundaryValidationError("invalid_donor_adapter") from error
    _validate_execution_input(donor_input, "donor execution input")
    native_by_id, library_sha256 = _native_index(context["native_skills"])
    for candidate in candidates:
        skill_id = candidate["skill_id"]
        if skill_id not in native_by_id:
            raise _BoundaryValidationError("invalid_donor_skill")
        if candidate["native_payload"] != native_by_id[skill_id]["native_payload"]:
            raise _BoundaryValidationError("invalid_donor_payload")
    if not candidates:
        raise _BoundaryValidationError("invalid_donor_empty")
    top_skill_id = candidates[0]["skill_id"]
    artifact = native_by_id[top_skill_id]
    provenance = {
        "kind": donor["kind"],
        "producer_name": retrieval_response["retriever_name"],
        "task_id": donor["task_id"],
        "task_family": donor["task_family"],
        "state_sha256": donor["state_sha256"],
        "skill_id": top_skill_id,
        "source_path": artifact["source_path"],
        "native_payload_sha256": _hash_text(artifact["native_payload"]),
        "library_sha256": library_sha256,
        "calibration_only": donor["kind"] == "calibration_oracle",
    }
    return donor_input, provenance


def _validate_retrieval_response(response: Any) -> None:
    if not isinstance(response, Mapping):
        raise _BoundaryValidationError("invalid_donor_response_type")
    try:
        require_fields(response, RETRIEVAL_RESPONSE_FIELDS, "donor retrieval response")
    except ValueError as error:
        raise _BoundaryValidationError("invalid_donor_schema") from error
    if not isinstance(response["retriever_name"], str):
        raise _BoundaryValidationError("invalid_donor_schema")
    if not isinstance(response["ranked_candidates"], list):
        raise _BoundaryValidationError("invalid_donor_schema")
    if not isinstance(response["warnings"], list):
        raise _BoundaryValidationError("invalid_donor_schema")
    _reject_forbidden_keys(response)
    for candidate in response["ranked_candidates"]:
        if not isinstance(candidate, Mapping):
            raise _BoundaryValidationError("invalid_donor_candidate")
        try:
            require_fields(candidate, RETRIEVAL_CANDIDATE_FIELDS, "donor retrieval candidate")
        except ValueError as error:
            raise _BoundaryValidationError("invalid_donor_candidate") from error
        if not isinstance(candidate["skill_id"], str) or not isinstance(
            candidate["native_payload"], str
        ):
            raise _BoundaryValidationError("invalid_donor_candidate")
        score = candidate["score"]
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise _BoundaryValidationError("invalid_donor_score")
        if not math.isfinite(float(score)):
            raise _BoundaryValidationError("invalid_donor_score")


def _copy_atom(
    original: Mapping[str, Any], donor: Mapping[str, Any], atom: str
) -> Dict[str, Any]:
    effective = copy.deepcopy(dict(original))
    if atom == "reference_handoff_group":
        if not (original["selected_skill_ids"] and donor["selected_skill_ids"]):
            raise _BoundaryValidationError("invalid_list_alignment")
        if not (
            len(original["selected_skill_ids"])
            == len(original["selected_scores"])
            == len(original["selected_native_skills"])
            == len(donor["selected_skill_ids"])
            == len(donor["selected_scores"])
            == len(donor["selected_native_skills"])
        ):
            raise _BoundaryValidationError("invalid_list_alignment")
        effective["selected_skill_ids"] = copy.deepcopy(donor["selected_skill_ids"])
        effective["selected_scores"] = copy.deepcopy(donor["selected_scores"])
        effective["selected_native_skills"] = copy.deepcopy(donor["selected_native_skills"])
        effective["flat_skill_context"] = donor["flat_skill_context"]
    elif atom == "selected_skill_ids[0]":
        if not original["selected_skill_ids"] or not donor["selected_skill_ids"]:
            raise _BoundaryValidationError("invalid_list_alignment")
        effective["selected_skill_ids"][0] = donor["selected_skill_ids"][0]
    elif atom == "selected_scores[0]":
        if not original["selected_scores"] or not donor["selected_scores"]:
            raise _BoundaryValidationError("invalid_list_alignment")
        effective["selected_scores"][0] = donor["selected_scores"][0]
    elif atom == "selected_native_skills[0]":
        if not original["selected_native_skills"] or not donor["selected_native_skills"]:
            raise _BoundaryValidationError("invalid_list_alignment")
        effective["selected_native_skills"][0] = donor["selected_native_skills"][0]
    elif atom == "flat_skill_context":
        effective["flat_skill_context"] = donor["flat_skill_context"]
    else:  # pragma: no cover - _validate_arm closes this path.
        raise _BoundaryValidationError("invalid_atom_type")
    _validate_execution_input(effective, "effective execution input")
    return effective


def _native_index(native_skills: Any) -> Tuple[Dict[str, Dict[str, Any]], str]:
    if not isinstance(native_skills, list):
        raise _BoundaryValidationError("invalid_native_library")
    by_id: Dict[str, Dict[str, Any]] = {}
    records: List[Dict[str, Any]] = []
    for artifact in native_skills:
        if not isinstance(artifact, Mapping):
            raise _BoundaryValidationError("invalid_native_library")
        try:
            require_fields(artifact, NATIVE_SKILL_FIELDS, "native skill artifact")
        except ValueError as error:
            raise _BoundaryValidationError("invalid_native_library") from error
        skill_id = artifact["skill_id"]
        if not isinstance(skill_id, str) or skill_id in by_id:
            raise _BoundaryValidationError("invalid_native_library")
        if not isinstance(artifact["source_path"], str) or not isinstance(
            artifact["native_payload"], str
        ):
            raise _BoundaryValidationError("invalid_native_library")
        by_id[skill_id] = dict(artifact)
        records.append(
            {
                "skill_id": skill_id,
                "source_path": artifact["source_path"],
                "native_payload_sha256": _hash_text(artifact["native_payload"]),
                "local_metadata": artifact["local_metadata"],
            }
        )
    if not by_id:
        raise _BoundaryValidationError("invalid_native_library")
    return by_id, _hash_json(records)


def _consumer_registry() -> Dict[str, Any]:
    return {
        "plan_steps_by_skill": {
            skill_id: list(steps) for skill_id, steps in sorted(PLAN_STEPS_BY_SKILL.items())
        },
        "generic_no_skill_plan": list(GENERIC_NO_SKILL_PLAN),
        "appliance_by_skill": dict(sorted(APPLIANCE_BY_SKILL.items())),
        "transform_verb_by_skill": dict(sorted(TRANSFORM_VERB_BY_SKILL.items())),
        "synonyms": {
            key: list(value) if isinstance(value, (tuple, list)) else value
            for key, value in sorted(SYNONYMS.items())
        },
        "receptacle_type_order": list(RECEPTACLE_TYPE_ORDER),
    }


def _validate_forbidden_key(key: Any) -> None:
    if isinstance(key, str) and key.lower() in _FORBIDDEN_KEYS:
        raise _BoundaryValidationError("forbidden_outcome_content")


def _reject_forbidden_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            _validate_forbidden_key(key)
            _reject_forbidden_keys(child)
    elif isinstance(value, list):
        for child in value:
            _reject_forbidden_keys(child)


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(_SHA256_PATTERN.fullmatch(value))


def _hash_json(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class _ReadTracker:
    def __init__(self) -> None:
        self.events: List[Dict[str, Any]] = []
        self._sequence = 0

    def record(self, path: str, operation: str, read_type: str) -> None:
        self._sequence += 1
        self.events.append(
            {
                "sequence": self._sequence,
                "path": path,
                "operation": operation,
                "read_type": read_type,
            }
        )


class _TrackedList(list):
    def __init__(
        self,
        values: list,
        tracker: _ReadTracker,
        path: str,
        semantic_paths: Optional[set] = None,
        reporting_paths: Optional[set] = None,
    ) -> None:
        super().__init__(values)
        self._tracker = tracker
        self._path = path
        self._semantic_paths = semantic_paths or set()
        self._reporting_paths = reporting_paths or set()

    def __getitem__(self, index):
        value = super().__getitem__(index)
        if isinstance(index, int):
            if self._path in self._semantic_paths:
                read_type = "semantic_read"
            elif self._path in self._reporting_paths:
                read_type = "reporting_read"
            else:
                read_type = "value_read"
            self._tracker.record(f"{self._path}[{index}]", "index", read_type)
        return value


class _TrackedExecutionInput(dict):
    def __init__(
        self,
        values: Mapping[str, Any],
        tracker: _ReadTracker,
        track_gets: bool = False,
    ) -> None:
        super().__init__(values)
        self._tracker = tracker
        self._track_gets = track_gets

    def __contains__(self, key: object) -> bool:
        result = super().__contains__(key)
        if key in _EXECUTION_FIELDS:
            self._tracker.record(str(key), "contains", "schema_validation_read")
        return result

    def __getitem__(self, key: str) -> Any:
        value = super().__getitem__(key)
        self._tracker.record(key, "getitem", "schema_validation_read")
        return value

    def get(self, key: str, default: Any = None) -> Any:
        value = super().get(key, default)
        if self._track_gets and key in _EXECUTION_FIELDS:
            if key == "flat_skill_context":
                read_type = "prompt_exposure"
            elif key == "selected_native_skills":
                read_type = "host_semantic_read"
            elif key == "selected_skill_ids":
                read_type = "reporting_read"
            else:
                read_type = "mapping_get"
            self._tracker.record(key, "get", read_type)
        return value


def instrument_execution_input(
    execution_input: Mapping[str, Any],
    *,
    mode: str = "v2",
) -> Tuple[Mapping[str, Any], _ReadTracker]:
    """Wrap one v2 input without changing values or default behavior."""

    if mode not in {"v2", "v3"}:
        raise ValueError(f"unsupported read-tracking mode: {mode}")
    tracker = _ReadTracker()
    values: Dict[str, Any] = copy.deepcopy(dict(execution_input))
    semantic_paths = {"selected_skill_ids"}
    reporting_paths = set()
    if mode == "v3":
        semantic_paths = {"selected_native_skills"}
        reporting_paths = {"selected_skill_ids"}
    for field in ("selected_skill_ids", "selected_scores", "selected_native_skills"):
        values[field] = _TrackedList(
            values[field], tracker, field, semantic_paths, reporting_paths
        )
    return _TrackedExecutionInput(values, tracker, track_gets=mode == "v3"), tracker
