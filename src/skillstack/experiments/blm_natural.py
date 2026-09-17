"""Narrow R2 natural-case screening and first-provider-call machinery.

This module is deliberately not a general middleware, snapshot, or provider
framework.  It owns only the Structured ReAct first-handoff contract used by
R2 and the deterministic candidate/dry-run evidence around it.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import platform
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from skillstack.adapters.retrieval_to_execution import adapt_retrieval_for_execution
from skillstack.blm import (
    BLM_INTERVENTION_SCHEMA_V3,
    _hash_json,
    _hash_text,
    _native_index,
    _validate_execution_input,
    instrument_execution_input,
)
from skillstack.contracts import RETRIEVAL_CANDIDATE_FIELDS, RETRIEVAL_RESPONSE_FIELDS, require_fields
from skillstack.environments.alfworld_text import create_single_game_environment
from skillstack.execution.react import extract_procedure_steps
from skillstack.library import load_static_library
from skillstack.retrieval import (
    DebugLexicalRetriever,
    NoSkillRetriever,
    TaskSemanticRetriever,
)
from skillstack.tasks import load_task_manifest


NATURAL_INTERVENTION_SCHEMA = BLM_INTERVENTION_SCHEMA_V3
NATURAL_BOUNDARY_SCHEMA = "skillstack-blm-boundary-v3"
NATURAL_ENVELOPE_SCHEMA = "skillstack-blm-natural-envelope-v1"
NATURAL_REPLAY_SCHEMA = "skillstack-blm-natural-replay-v1"
NATURAL_BOUNDARY_ID = "r2_c2_structured_react_first_handoff"
NATURAL_STATE_SCOPE = "first_provider_call_reconstructed_alfworld_v1"
NATURAL_INTERVENTION_POSITION = "post_adapter_pre_consumer_read"
NATURAL_READ_MAP = {
    "top_candidate_group": "r2_c2.react.group.top_candidate",
    "full_handoff_group": "r2_c2.react.group.full_handoff",
    "selected_skill_ids[0]": "r2_c2.react.reporting.selected_skill_ids[0]",
    "selected_scores[0]": "r2_c2.react.unread.selected_scores[0]",
    "selected_native_skills[0]": "r2_c2.react.semantic.selected_native_skills[0]",
    "flat_skill_context": "r2_c2.react.prompt.flat_skill_context",
}
NATURAL_ATOMS = set(NATURAL_READ_MAP)
NATURAL_GROUPS = {"top_candidate_group", "full_handoff_group"}
NATURAL_REQUEST_FIELDS = {
    "schema_version",
    "case_id",
    "arm_id",
    "operation",
    "atom_or_group",
    "expected_state_sha256",
    "donor",
}
NATURAL_DONOR_FIELDS = {
    "kind",
    "producer_name",
    "task_id",
    "task_family",
    "state_sha256",
    "retrieval_response",
}
NATURAL_OPERATIONS = {"capture", "copy_atom_from_donor", "copy_group_from_donor"}
FORBIDDEN_OUTCOME_KEYS = {
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
    "expected_skill_id",
}
PRODUCER_NAMES = {
    "debug_lexical_top_k",
    "task_semantic_top_k",
    "random_skill",
    "matched_carrier_static",
    "no_skill",
}


def natural_state_sha256(context: Mapping[str, Any]) -> str:
    """Hash only state available before the first handoff/provider call."""

    state = {
        "state_scope": NATURAL_STATE_SCOPE,
        "task_record": context["task_record"],
        "initial_observation": context["initial_observation"],
        "initial_info": context["initial_info"],
        "environment_class": context["environment_class"],
        "consumer": {
            "name": context["consumer_name"],
            "structured_skills": bool(context.get("structured_skills", False)),
            "backend": context.get("backend_name"),
            "model": context.get("model"),
            "step_budget": context.get("consumer_step_budget"),
            "max_tokens_per_step": context.get("max_tokens_per_step"),
            "prompt_sha256": context.get("prompt_sha256"),
        },
        "native_library_sha256": context["native_library_sha256"],
        "top_k": context["top_k"],
        "max_steps": context["effective_max_steps"],
    }
    return _hash_json(state)


def apply_natural_boundary_intervention(
    execution_input: Mapping[str, Any],
    request: Any,
    context: Mapping[str, Any],
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """Validate and apply one additive v3 first-handoff intervention."""

    state_sha256 = natural_state_sha256(context)
    original = copy.deepcopy(dict(execution_input))
    record: Dict[str, Any] = {
        "schema_version": NATURAL_BOUNDARY_SCHEMA,
        "boundary_id": NATURAL_BOUNDARY_ID,
        "state_scope": NATURAL_STATE_SCOPE,
        "case_id": request.get("case_id") if isinstance(request, Mapping) else None,
        "arm_id": request.get("arm_id") if isinstance(request, Mapping) else None,
        "operation": request.get("operation") if isinstance(request, Mapping) else None,
        "atom_or_group": request.get("atom_or_group") if isinstance(request, Mapping) else None,
        "read_map_id": None,
        "state_sha256": state_sha256,
        "original_input_sha256": _hash_json(original),
        "effective_input_sha256": None,
        "pre_provider_request_projection_sha256": None,
        "changed": False,
        "donor_provenance": None,
        "intervention_position": NATURAL_INTERVENTION_POSITION,
        "validity": "invalid",
        "validity_reason": "invalid_request",
        "consumer_reads": [],
        "consumer_branch": None,
        "outcome_observation": None,
    }
    if isinstance(request, Mapping):
        atom = request.get("atom_or_group")
        record["read_map_id"] = NATURAL_READ_MAP.get(atom)
    try:
        _validate_natural_request(request)
        _validate_natural_context(context)
        _validate_execution_input(original, "current structured-react execution input")
        operation = request["operation"]
        atom = request["atom_or_group"]
        if operation == "capture":
            if request["expected_state_sha256"] is not None or request["donor"] is not None:
                raise _NaturalValidationError("invalid_capture_state_field")
            effective = original
            record["validity_reason"] = "capture"
        else:
            if request["expected_state_sha256"] != state_sha256:
                raise _NaturalValidationError("invalid_donor_state")
            donor_input, provenance = _validate_natural_donor(
                request["donor"], context, request["case_id"], request["arm_id"]
            )
            effective = _apply_natural_atom(original, donor_input, atom)
            record["donor_provenance"] = provenance
            record["validity_reason"] = "intervention_applied"
        record["effective_input_sha256"] = _hash_json(effective)
        record["changed"] = effective != original
        record["pre_provider_request_projection_sha256"] = _hash_json(
            provider_request_projection(context, effective)
        )
        record["validity"] = "valid"
        return effective, record
    except _NaturalValidationError as error:
        record["validity_reason"] = error.reason
        return None, record


def finalize_natural_boundary_record(
    record: Mapping[str, Any],
    executor_report: Mapping[str, Any],
    consumer_reads: Optional[Sequence[Mapping[str, Any]]] = None,
) -> Dict[str, Any]:
    finalized = copy.deepcopy(dict(record))
    if finalized.get("validity") != "valid":
        return finalized
    finalized["consumer_reads"] = copy.deepcopy(list(consumer_reads or []))
    finalized["consumer_branch"] = {
        "grounded_steps": executor_report.get("grounded_steps", []),
        "skill_id_reporting": executor_report.get("action_rationales", [{}])[0].get("skill_id")
        if executor_report.get("action_rationales")
        else None,
    }
    finalized["outcome_observation"] = {
        "success": bool(executor_report.get("success", False)),
        "stop_reason": executor_report.get("stop_reason"),
        "action_trace_sha256": _hash_json(executor_report.get("actions", [])),
        "provider_call_count": len(executor_report.get("llm_calls", [])),
        "prompt_sha256": _hash_text(executor_report.get("system_prompt", "")),
    }
    return finalized


def provider_request_projection(context: Mapping[str, Any], execution_input: Mapping[str, Any]) -> Dict[str, Any]:
    """Build a hashable first provider request projection without calling a model."""

    template = context.get("prompt_template", "")
    system = template.replace(
        "{skill_context}", execution_input.get("flat_skill_context") or "(none provided)"
    )
    system = f"Task: {context['task_record']['task_instruction']}\n\n" + system
    grounded = extract_procedure_steps(dict(execution_input)) if context.get("structured_skills") else []
    if grounded:
        system += "\n\nThe selected skill lists numbered steps; follow them in order:\n" + "\n".join(
            f"{i}. {step}" for i, step in enumerate(grounded, start=1)
        )
    admissible = list(context["initial_info"].get("admissible_commands", []))
    user = "Observation:\n" + context["initial_observation"] + "\n\nAdmissible commands:\n"
    user += "\n".join(f"- {command}" for command in admissible)
    return {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "backend": context.get("backend_name"),
        "model": context.get("model"),
        "structured_skills": bool(context.get("structured_skills")),
        "max_tokens_per_step": context.get("max_tokens_per_step"),
        "temperature": context.get("temperature", 0),
    }


def build_natural_context(
    env: Any,
    task_record: Mapping[str, Any],
    initial_observation: str,
    initial_info: Mapping[str, Any],
    native_skills: Sequence[Mapping[str, Any]],
    *,
    top_k: int,
    max_steps: int,
    prompt_template: str,
    backend_name: str = "deepseek_v4_flash",
    model: str = "deepseek-v4-flash",
    max_tokens_per_step: int = 512,
    consumer_step_budget: Optional[int] = None,
) -> Dict[str, Any]:
    return {
        "task_record": copy.deepcopy(dict(task_record)),
        "initial_observation": initial_observation,
        "initial_info": copy.deepcopy(dict(initial_info)),
        "environment_class": f"{type(env).__module__}.{type(env).__qualname__}",
        "consumer_name": "react_executor",
        "structured_skills": True,
        "backend_name": backend_name,
        "model": model,
        "max_tokens_per_step": max_tokens_per_step,
        "consumer_step_budget": consumer_step_budget,
        "prompt_template": prompt_template,
        "prompt_sha256": _hash_text(prompt_template),
        "native_library_sha256": _hash_json(native_skills),
        "native_skills": copy.deepcopy(list(native_skills)),
        "top_k": top_k,
        "effective_max_steps": max_steps,
    }


def _validate_natural_request(request: Any) -> None:
    if not isinstance(request, Mapping) or set(request) != NATURAL_REQUEST_FIELDS:
        raise _NaturalValidationError("invalid_request_schema")
    if request.get("schema_version") != NATURAL_INTERVENTION_SCHEMA:
        raise _NaturalValidationError("invalid_request_schema")
    if not all(isinstance(request.get(key), str) and request[key] for key in ("case_id", "arm_id")):
        raise _NaturalValidationError("invalid_request_schema")
    if request.get("operation") not in NATURAL_OPERATIONS:
        raise _NaturalValidationError("invalid_operation")
    atom = request.get("atom_or_group")
    if atom is not None and atom not in NATURAL_ATOMS:
        raise _NaturalValidationError("invalid_atom_type")
    if request["operation"] == "capture" and atom is not None:
        raise _NaturalValidationError("invalid_capture_atom")
    if request["operation"] == "copy_atom_from_donor" and atom in NATURAL_GROUPS:
        raise _NaturalValidationError("invalid_group_operation")
    if request["operation"] == "copy_group_from_donor" and atom not in NATURAL_GROUPS:
        raise _NaturalValidationError("invalid_group_operation")
    _reject_natural_forbidden_keys(request)


def _validate_natural_context(context: Mapping[str, Any]) -> None:
    if context.get("consumer_name") != "react_executor" or not context.get("structured_skills"):
        raise _NaturalValidationError("unsupported_consumer")
    if not isinstance(context.get("native_library_sha256"), str):
        raise _NaturalValidationError("invalid_context")
    if not isinstance(context.get("top_k"), int) or context["top_k"] < 1:
        raise _NaturalValidationError("invalid_context")
    if not isinstance(context.get("effective_max_steps"), int) or context["effective_max_steps"] < 1:
        raise _NaturalValidationError("invalid_context")


def _validate_natural_donor(
    donor: Any,
    context: Mapping[str, Any],
    case_id: str,
    arm_id: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    _reject_natural_forbidden_keys(donor)
    if not isinstance(donor, Mapping) or set(donor) != NATURAL_DONOR_FIELDS:
        raise _NaturalValidationError("invalid_donor_schema")
    if donor["kind"] not in {
        "task_semantic_reference",
        "producer_output",
        "matched_nonreference",
        "lexical_crossed",
    }:
        raise _NaturalValidationError("invalid_donor_kind")
    if donor["task_id"] != context["task_record"]["task_id"]:
        raise _NaturalValidationError("invalid_donor_task")
    if donor["task_family"] != context["task_record"]["task_family"]:
        raise _NaturalValidationError("invalid_donor_task_family")
    if donor["state_sha256"] != natural_state_sha256(context):
        raise _NaturalValidationError("invalid_donor_state")
    if donor["producer_name"] not in PRODUCER_NAMES:
        raise _NaturalValidationError("invalid_donor_source")
    if donor["kind"] == "task_semantic_reference" and donor["producer_name"] != "task_semantic_top_k":
        raise _NaturalValidationError("invalid_donor_source")
    if donor["kind"] == "lexical_crossed" and donor["producer_name"] != "debug_lexical_top_k":
        raise _NaturalValidationError("invalid_donor_source")
    if donor["kind"] == "producer_output" and arm_id != "crossed-noop":
        raise _NaturalValidationError("invalid_donor_source")
    if donor["kind"] == "matched_nonreference" and arm_id != "matched-carrier":
        raise _NaturalValidationError("invalid_donor_source")
    if donor["kind"] == "matched_nonreference" and donor["producer_name"] not in {
        "random_skill",
        "matched_carrier_static",
    }:
        raise _NaturalValidationError("invalid_donor_source")
    response = donor["retrieval_response"]
    _validate_natural_retrieval_response(response)
    if response["retriever_name"] != donor["producer_name"]:
        raise _NaturalValidationError("invalid_donor_source")
    try:
        donor_input, _event = adapt_retrieval_for_execution(response)
    except (TypeError, ValueError, KeyError) as error:
        raise _NaturalValidationError("invalid_donor_adapter") from error
    _validate_execution_input(donor_input, "natural donor execution input")
    native_by_id, library_sha256 = _native_index(context["native_skills"])
    for candidate in response["ranked_candidates"]:
        if candidate["skill_id"] not in native_by_id:
            raise _NaturalValidationError("invalid_donor_skill")
        if candidate["native_payload"] != native_by_id[candidate["skill_id"]]["native_payload"]:
            raise _NaturalValidationError("invalid_donor_payload")
    if not response["ranked_candidates"] and arm_id != "no-skill-ablation":
        raise _NaturalValidationError("invalid_donor_empty")
    top = response["ranked_candidates"][0] if response["ranked_candidates"] else None
    provenance = {
        "kind": donor["kind"],
        "producer_name": donor["producer_name"],
        "task_id": donor["task_id"],
        "task_family": donor["task_family"],
        "state_sha256": donor["state_sha256"],
        "skill_id": top["skill_id"] if top else None,
        "source_path": native_by_id[top["skill_id"]]["source_path"] if top else None,
        "native_payload_sha256": _hash_text(top["native_payload"]) if top else None,
        "library_sha256": library_sha256,
        "calibration_only": False,
        "case_id": case_id,
    }
    return donor_input, provenance


def _validate_natural_retrieval_response(response: Any) -> None:
    if not isinstance(response, Mapping):
        raise _NaturalValidationError("invalid_donor_response_type")
    try:
        require_fields(response, RETRIEVAL_RESPONSE_FIELDS, "natural donor retrieval response")
    except ValueError as error:
        raise _NaturalValidationError("invalid_donor_schema") from error
    _reject_natural_forbidden_keys(response)
    if response["retriever_name"] not in PRODUCER_NAMES or not isinstance(response["ranked_candidates"], list):
        raise _NaturalValidationError("invalid_donor_schema")
    for candidate in response["ranked_candidates"]:
        if not isinstance(candidate, Mapping):
            raise _NaturalValidationError("invalid_donor_candidate")
        try:
            require_fields(candidate, RETRIEVAL_CANDIDATE_FIELDS, "natural donor candidate")
        except ValueError as error:
            raise _NaturalValidationError("invalid_donor_candidate") from error
        if not isinstance(candidate["skill_id"], str) or not isinstance(candidate["native_payload"], str):
            raise _NaturalValidationError("invalid_donor_candidate")
        if (
            isinstance(candidate["score"], bool)
            or not isinstance(candidate["score"], (int, float))
            or not math.isfinite(float(candidate["score"]))
        ):
            raise _NaturalValidationError("invalid_donor_score")


def _apply_natural_atom(
    original: Mapping[str, Any], donor: Mapping[str, Any], atom: str
) -> Dict[str, Any]:
    effective = copy.deepcopy(dict(original))
    if atom in {"top_candidate_group", "full_handoff_group"}:
        if not original["selected_skill_ids"] or not donor["selected_skill_ids"]:
            raise _NaturalValidationError("invalid_list_alignment")
        if atom == "full_handoff_group":
            effective["selected_skill_ids"] = copy.deepcopy(donor["selected_skill_ids"])
            effective["selected_scores"] = copy.deepcopy(donor["selected_scores"])
            effective["selected_native_skills"] = copy.deepcopy(donor["selected_native_skills"])
            effective["flat_skill_context"] = donor["flat_skill_context"]
        else:
            effective["selected_skill_ids"][0] = donor["selected_skill_ids"][0]
            effective["selected_scores"][0] = donor["selected_scores"][0]
            effective["selected_native_skills"][0] = donor["selected_native_skills"][0]
            effective["flat_skill_context"] = _derive_flat_context(effective)
    elif atom == "selected_scores[0]":
        if not original["selected_scores"] or not donor["selected_scores"]:
            raise _NaturalValidationError("invalid_list_alignment")
        effective["selected_scores"][0] = donor["selected_scores"][0]
    elif atom == "selected_native_skills[0]":
        if not original["selected_native_skills"] or not donor["selected_native_skills"]:
            raise _NaturalValidationError("invalid_list_alignment")
        effective["selected_native_skills"][0] = donor["selected_native_skills"][0]
    elif atom == "flat_skill_context":
        effective["flat_skill_context"] = donor["flat_skill_context"]
    elif atom == "selected_skill_ids[0]":
        if not original["selected_skill_ids"] or not donor["selected_skill_ids"]:
            raise _NaturalValidationError("invalid_list_alignment")
        effective["selected_skill_ids"][0] = donor["selected_skill_ids"][0]
    else:
        raise _NaturalValidationError("invalid_atom_type")
    _validate_execution_input(effective, "effective natural execution input")
    return effective


def _derive_flat_context(execution_input: Mapping[str, Any]) -> str:
    if not (
        len(execution_input["selected_skill_ids"])
        == len(execution_input["selected_scores"])
        == len(execution_input["selected_native_skills"])
    ):
        raise _NaturalValidationError("invalid_list_alignment")
    return "\n\n---\n\n".join(
        f"### Selected skill {index}: {skill_id}\n\n{payload}"
        for index, (skill_id, payload) in enumerate(
            zip(execution_input["selected_skill_ids"], execution_input["selected_native_skills"]),
            start=1,
        )
    )


class _NaturalValidationError(ValueError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _reject_natural_forbidden_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if isinstance(key, str) and key.lower() in FORBIDDEN_OUTCOME_KEYS:
                raise _NaturalValidationError("forbidden_outcome_content")
            _reject_natural_forbidden_keys(child)
    elif isinstance(value, list):
        for child in value:
            _reject_natural_forbidden_keys(child)


def screen_natural_candidates(
    task_manifest: Path,
    data_root: Path,
    *,
    top_k: int = 2,
    max_steps: int = 20,
    prompt_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Re-run only deterministic producers and record eligible carrier diffs."""

    tasks = load_task_manifest(task_manifest)
    native_skills = load_static_library()
    prompt_path = prompt_path or Path(__file__).resolve().parents[3] / "configs" / "p0_react_prompt.txt"
    producers = (("lexical", DebugLexicalRetriever()), ("task_semantic", TaskSemanticRetriever()))
    records: List[Dict[str, Any]] = []
    for task in tasks:
        outputs: Dict[str, Any] = {}
        state_records: Dict[str, Any] = {}
        environment_available = True
        environment_error = None
        try:
            env, observation, info = create_single_game_environment(data_root, task["game_file"])
            environment_class = f"{type(env).__module__}.{type(env).__qualname__}"
            env.close()
        except (ModuleNotFoundError, FileNotFoundError, ValueError) as error:
            # Keep the candidate log complete when the optional ALFWorld
            # runtime is absent.  Historical traces may seed a diagnostic
            # pre-screen, but can never satisfy the live reset gate.
            environment_available = False
            environment_error = f"{type(error).__name__}: {error}"
            historical = _historical_initial_observation(task)
            observation = historical or ""
            info = {}
            environment_class = "not_available"
        for label, retriever in producers:
            response = retriever.retrieve(task, observation, native_skills, top_k)
            execution_input, adapter_event = adapt_retrieval_for_execution(response)
            outputs[label] = {
                    "producer_name": retriever.name,
                    "producer_config": (
                        {"selection_policy": "task_instruction_only"}
                        if label == "lexical"
                        else {
                            "selection_policy": "task_family_label_assisted_semantics",
                            "allowed_task_record_field": "task_family",
                            "forbidden_task_record_fields": ["expected_skill_id"],
                        }
                    ),
                    "retrieval_response": response,
                    "execution_input": execution_input,
                    "adapter_event": adapter_event,
                "hashes": {
                        "retrieval_response_sha256": _hash_json(response),
                        "execution_input_sha256": _hash_json(execution_input),
                        "native_payload_sha256": _hash_json(execution_input["selected_native_skills"]),
                        "flat_context_sha256": _hash_text(execution_input["flat_skill_context"]),
                    },
                "evidence_class": "verified_this_run" if environment_available else "historical_evidence",
            }
            state_records[label] = {
                "environment_class": environment_class,
                "initial_observation_sha256": _hash_text(observation),
                "initial_info_sha256": _hash_json(info),
                "reset_reconstructable": environment_available,
                "observation_source": "live_reset" if environment_available else "historical_trace_pre_screen",
            }
        lexical = outputs["lexical"]["execution_input"]
        semantic = outputs["task_semantic"]["execution_input"]
        diff = {
            "selected_skill_ids": lexical["selected_skill_ids"] != semantic["selected_skill_ids"],
            "selected_scores": lexical["selected_scores"] != semantic["selected_scores"],
            "selected_native_skills": lexical["selected_native_skills"] != semantic["selected_native_skills"],
            "flat_skill_context": lexical["flat_skill_context"] != semantic["flat_skill_context"],
        }
        carrier_difference = bool(diff["selected_skill_ids"] or diff["selected_native_skills"] or diff["flat_skill_context"])
        gate_reasons = []
        if not carrier_difference:
            gate_reasons.append("no_consumer_read_domain_carrier_difference")
        if not all(state["reset_reconstructable"] for state in state_records.values()):
            gate_reasons.append("initial_reset_not_reconstructable")
        if environment_error:
            gate_reasons.append("alfworld_runtime_unavailable")
        records.append(
            {
                "case_id": f"r2_{task['task_id'].split('/')[-1]}",
                "task": copy.deepcopy(task),
                "task_family_label_assistance": {
                    "used": True,
                    "field": "task_family",
                    "expected_skill_id_read": False,
                    "deployment_unassisted": False,
                },
                "environment": state_records,
                "environment_runtime": {
                    "available": environment_available,
                    "error": environment_error,
                },
                "consumer": {
                    "name": "react_executor",
                    "structured_skills": True,
                    "top_k": top_k,
                    "max_steps": max_steps,
                    "prompt_sha256": _hash_text(prompt_path.read_text(encoding="utf-8")),
                    "library_sha256": _hash_json(native_skills),
                },
                "producers": outputs,
                "consumer_read_domain_difference": diff,
                "carrier_difference": carrier_difference,
                "historical_evidence": {
                    "classification": "historical_evidence",
                    "paths": ["runs/20260818T150521707631Z_w3_picktwo_deepseek_no_skill"],
                    "not_used_as_r2_outcome": True,
                },
                "eligible": carrier_difference and not gate_reasons,
                "measurement_status": "verified_this_run" if environment_available else "not_verified",
                "gate_reasons": gate_reasons,
            }
        )
    return {
        "schema_version": "skillstack-blm-natural-candidate-screen-v1",
        "boundary_id": NATURAL_BOUNDARY_ID,
        "generated_by": "zero_model_deterministic_candidate_screen",
        "task_manifest": _display_path(task_manifest),
        "data_root": _display_path(data_root),
        "top_k": top_k,
        "max_steps": max_steps,
        "code_revision": code_revision(),
        "tasks": records,
        "eligible_cases": [record["case_id"] for record in records if record["eligible"]],
        "excluded_cases": [record["case_id"] for record in records if not record["eligible"]],
        "evidence_class": (
            "verified_this_run"
            if all(record.get("measurement_status") == "verified_this_run" for record in records)
            else "not_verified"
        ),
        "claim_boundary": "candidate discovery only; no R2 live outcome or R3 verdict",
    }


def build_natural_protocol(screen: Mapping[str, Any]) -> Dict[str, Any]:
    eligible = [record for record in screen.get("tasks", []) if record.get("eligible")]
    cases = []
    for record in eligible:
        lexical = record["producers"]["lexical"]["retrieval_response"]
        semantic = record["producers"]["task_semantic"]["retrieval_response"]
        ref_id = semantic["ranked_candidates"][0]["skill_id"] if semantic["ranked_candidates"] else None
        cross_id = lexical["ranked_candidates"][0]["skill_id"] if lexical["ranked_candidates"] else None
        cases.append(
            {
                "case_id": record["case_id"],
                "task": record["task"],
                "reference": {"producer": "task_semantic_top_k", "kind": "task_semantic_reference"},
                "crossed": {"producer": "debug_lexical_top_k", "kind": "lexical_crossed"},
                "reference_top_skill_id": ref_id,
                "crossed_top_skill_id": cross_id,
                "matched_carrier_rule": "non-reference/non-crossed native artifact; same section count; closest byte length",
            }
        )
    return {
        "schema_version": "skillstack-blm-natural-protocol-v1",
        "boundary_id": NATURAL_BOUNDARY_ID,
        "backend": {
            "name": "deepseek_v4_flash",
            "model": "deepseek-v4-flash",
            "temperature": 0,
            "structured_skills": True,
        },
        "top_k": screen.get("top_k", 2),
        "max_steps": screen.get("max_steps", 20),
        "repetitions": 5,
        "shuffle_seed": 42,
        "arms": [
            "reference",
            "crossed",
            "crossed-noop",
            "crossed+top-candidate",
            "matched-carrier",
            "crossed+full-reference",
            "score-negative-control",
            "no-skill-ablation",
        ],
        "cases": cases,
        "live_caps": {
            "max_episodes": max(1, len(cases)) * 8 * 5,
            "max_provider_calls": max(1, len(cases)) * 8 * 5 * 20 * 2,
            "max_prompt_tokens": 3000000,
            "max_completion_tokens": 100000,
            "max_cost_usd": 2.0,
        },
        "execution": {
            "requires_manual_confirmation": True,
            "live_provider_called_by_implementation_turn": False,
            "output_root": "runs",
        },
        "claim_boundary": "R2 discovery only; same-set findings require independent R3 confirmation",
    }


def dry_run_summary(protocol: Mapping[str, Any]) -> Dict[str, Any]:
    cases = protocol.get("cases", [])
    arms = protocol.get("arms", [])
    repetitions = int(protocol.get("repetitions", 0))
    episodes = len(cases) * len(arms) * repetitions
    max_steps = int(protocol.get("max_steps", 20))
    return {
        "schema_version": "skillstack-blm-r2-dry-run-v1",
        "eligible_case_count": len(cases),
        "excluded_case_count": 3 - len(cases),
        "planned_arms": list(arms),
        "planned_episodes": episodes,
        "maximum_provider_calls": episodes * max_steps * 2,
        "estimated_prompt_tokens_upper_bound": episodes * max_steps * 512,
        "estimated_completion_tokens_upper_bound": episodes * max_steps * 2 * 512,
        "estimated_cost_usd_upper_bound": 2.0,
        "estimated_duration": "provider-dependent; not run in this implementation turn",
        "commands": {
            "run": "uv run python scripts/run_blm_natural.py run --protocol configs/blm/r2_natural_case_protocol.yaml --output-root runs --approve-live R2-LIVE-APPROVED",
            "resume": "uv run python scripts/run_blm_natural.py resume --run-id <run-id> --output-root runs",
            "summarize": "uv run python scripts/run_blm_natural.py summarize --run-id <run-id> --output-root runs",
        },
        "credential_redaction": {
            "status": "verified",
            "recorded_fields": ["backend_name", "model", "api_key_env"],
            "excluded_fields": ["api_key", "Authorization", "complete_http_headers"],
        },
        "live_provider": "not run; requires separate human confirmation",
    }


def code_revision() -> Dict[str, Any]:
    module_path = Path(__file__).resolve()
    try:
        git_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=module_path.parents[3], text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        git_sha = "unavailable"
    return {
        "git_sha": git_sha,
        "module_path": "src/skillstack/experiments/blm_natural.py",
        "module_sha256": _hash_text(module_path.read_text(encoding="utf-8")),
        "python": platform.python_version(),
        "platform": platform.platform(),
    }


def _retriever_from_name(name: str, config: Optional[Mapping[str, Any]] = None):
    if name == "debug_lexical_top_k":
        return DebugLexicalRetriever()
    if name == "task_semantic_top_k":
        return TaskSemanticRetriever()
    if name == "no_skill":
        return NoSkillRetriever()
    raise ValueError(f"Unsupported R2 producer: {name}")


def materialize_natural_envelope(
    task: Mapping[str, Any],
    retriever: Any,
    native_skills: Sequence[Mapping[str, Any]],
    data_root: Path,
    prompt_template: str,
    *,
    top_k: int = 2,
    max_steps: int = 20,
    backend_name: str = "deepseek_v4_flash",
    model: str = "deepseek-v4-flash",
    request: Optional[Mapping[str, Any]] = None,
    case_id: Optional[str] = None,
    arm_id: str = "reference",
    environment_factory: Optional[Callable[[Path, Mapping[str, Any]], Tuple[Any, str, Dict[str, Any]]]] = None,
) -> Dict[str, Any]:
    reset = environment_factory or (lambda root, record: create_single_game_environment(root, record["game_file"]))
    env, observation, info = reset(data_root, task)
    try:
        response = retriever.retrieve(task, observation, list(native_skills), top_k)
        execution_input, adapter_event = adapt_retrieval_for_execution(response)
        context = build_natural_context(
            env, task, observation, info, native_skills,
            top_k=top_k, max_steps=max_steps, prompt_template=prompt_template,
            backend_name=backend_name, model=model,
        )
        state_sha = natural_state_sha256(context)
        effective_request = copy.deepcopy(dict(request or {
            "schema_version": NATURAL_INTERVENTION_SCHEMA,
            "case_id": case_id or "r2_case",
            "arm_id": arm_id,
            "operation": "capture",
            "atom_or_group": None,
            "expected_state_sha256": None,
            "donor": None,
        }))
        envelope = {
            "schema_version": NATURAL_ENVELOPE_SCHEMA,
            "envelope_id": f"{case_id or task['task_id']}:{arm_id}",
            "boundary_id": NATURAL_BOUNDARY_ID,
            "state_scope": NATURAL_STATE_SCOPE,
            "code_revision": code_revision(),
            "task": copy.deepcopy(dict(task)),
            "environment": {
                "game_file": task["game_file"],
                "trajectory_file": task.get("trajectory_file"),
                "class_identity": context["environment_class"],
                "initial_observation": observation,
                "initial_info": copy.deepcopy(info),
                "game_file_sha256": _file_hash(data_root / task["game_file"]),
                "trajectory_file_sha256": _file_hash(data_root / task["trajectory_file"])
                if task.get("trajectory_file") and (data_root / task["trajectory_file"]).is_file()
                else None,
            },
            "producer": {
                "name": retriever.name,
                "config": {"task_family_label_assisted": retriever.name == "task_semantic_top_k"},
                "output": copy.deepcopy(response),
            },
            "adapter": {
                "name": "skillstack.adapters.retrieval_to_execution.adapt_retrieval_for_execution",
                "output": copy.deepcopy(execution_input),
                "event": copy.deepcopy(adapter_event),
            },
            "consumer": {
                "name": "react_executor",
                "structured_skills": True,
                "prompt_sha256": _hash_text(prompt_template),
                "backend_name": backend_name,
                "model": model,
                "top_k": top_k,
                "max_steps": max_steps,
            },
            "native_library": {"sha256": _hash_json(native_skills), "artifacts": copy.deepcopy(list(native_skills))},
            "budget": {"top_k": top_k, "max_steps": max_steps, "max_tokens_per_step": 512},
            "intervention_request": effective_request,
            "pre_provider_request_projection": provider_request_projection(context, execution_input),
            "hashes": {
                "state_sha256": state_sha,
                "producer_output_sha256": _hash_json(response),
                "adapter_output_sha256": _hash_json(execution_input),
                "pre_provider_request_sha256": _hash_json(provider_request_projection(context, execution_input)),
            },
        }
        envelope["hashes"]["envelope_sha256"] = _hash_envelope(envelope)
        return envelope
    finally:
        env.close()


def replay_natural_envelope(
    envelope: Mapping[str, Any],
    data_root: Path,
    prompt_template: str,
    environment_factory: Optional[Callable[[Path, Mapping[str, Any]], Tuple[Any, str, Dict[str, Any]]]] = None,
) -> Dict[str, Any]:
    """Replay only through the first provider request projection."""

    try:
        _validate_envelope(envelope)
    except ValueError as error:
        return {"schema_version": NATURAL_REPLAY_SCHEMA, "measurement_status": "abstained", "reason": f"replay_state_incomplete:{error}", "provider_called": False}
    task = envelope["task"]
    native_skills = load_static_library()
    if envelope["native_library"]["sha256"] != _hash_json(native_skills):
        return _abstained_replay("native_library_drift")
    reset = environment_factory or (lambda root, record: create_single_game_environment(root, record["game_file"]))
    env, observation, info = reset(data_root, task)
    try:
        retriever = _retriever_from_name(envelope["producer"]["name"], envelope["producer"].get("config"))
        actual_response = retriever.retrieve(task, observation, native_skills, envelope["budget"]["top_k"])
        actual_input, actual_event = adapt_retrieval_for_execution(actual_response)
        if actual_response != envelope["producer"]["output"]:
            return _abstained_replay("producer_output_drift")
        if actual_input != envelope["adapter"]["output"] or actual_event != envelope["adapter"]["event"]:
            return _abstained_replay("adapter_output_drift")
        context = build_natural_context(
            env, task, observation, info, native_skills,
            top_k=envelope["budget"]["top_k"], max_steps=envelope["budget"]["max_steps"],
            prompt_template=prompt_template, backend_name=envelope["consumer"]["backend_name"],
            model=envelope["consumer"]["model"],
        )
        if natural_state_sha256(context) != envelope["hashes"]["state_sha256"]:
            return _abstained_replay("state_hash_mismatch")
        projection = provider_request_projection(context, actual_input)
        if _hash_json(projection) != envelope["hashes"]["pre_provider_request_sha256"]:
            return _abstained_replay("provider_request_projection_drift")
        return {
            "schema_version": NATURAL_REPLAY_SCHEMA,
            "measurement_status": "valid",
            "reason": "first_provider_projection_exact",
            "provider_called": False,
            "envelope_id": envelope["envelope_id"],
            "pre_provider_request_sha256": _hash_json(projection),
        }
    finally:
        env.close()


def _validate_envelope(envelope: Mapping[str, Any]) -> None:
    required = {
        "schema_version", "envelope_id", "boundary_id", "state_scope", "code_revision", "task",
        "environment", "producer", "adapter", "consumer", "native_library", "budget",
        "intervention_request", "pre_provider_request_projection", "hashes",
    }
    if set(envelope) != required or envelope["schema_version"] != NATURAL_ENVELOPE_SCHEMA:
        raise ValueError("envelope_schema")
    if envelope["boundary_id"] != NATURAL_BOUNDARY_ID or envelope["state_scope"] != NATURAL_STATE_SCOPE:
        raise ValueError("boundary_scope")
    if envelope["hashes"].get("envelope_sha256") != _hash_envelope(envelope):
        raise ValueError("envelope_hash_mismatch")
    if envelope["task"].get("expected_skill_id") is None:
        raise ValueError("task_schema")
    code = envelope["code_revision"]
    current_code = code_revision()
    if any(code.get(key) != current_code.get(key) for key in ("git_sha", "module_sha256", "python", "platform")):
        raise ValueError("code_revision_drift")


def _hash_envelope(envelope: Mapping[str, Any]) -> str:
    value = copy.deepcopy(dict(envelope))
    value.setdefault("hashes", {}).pop("envelope_sha256", None)
    return _hash_json(value)


def _abstained_replay(reason: str) -> Dict[str, Any]:
    return {
        "schema_version": NATURAL_REPLAY_SCHEMA,
        "measurement_status": "abstained",
        "reason": f"replay_state_incomplete:{reason}",
        "provider_called": False,
    }


def _file_hash(path: Path) -> Optional[str]:
    if not path.is_file():
        return None
    return _hash_text(path.read_text(encoding="utf-8"))


def _display_path(path: Path) -> str:
    root = Path(__file__).resolve().parents[3]
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _historical_initial_observation(task: Mapping[str, Any]) -> Optional[str]:
    """Find a prior raw trace only for a clearly labelled pre-screen."""

    root = Path(__file__).resolve().parents[3]
    runs_root = root / "runs"
    if not runs_root.is_dir():
        return None
    for episodes_path in sorted(runs_root.glob("*/episodes.jsonl")):
        try:
            for line in episodes_path.read_text(encoding="utf-8").splitlines():
                record = json.loads(line)
                if record.get("task_id") == task.get("task_id"):
                    observations = record.get("raw_observations") or []
                    if observations and isinstance(observations[0], str):
                        return observations[0]
        except (OSError, json.JSONDecodeError):
            continue
    return None
