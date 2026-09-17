"""Small, deterministic R1 BLM calibration fixture and replay helpers.

This module is intentionally scoped to the frozen C1 heat fixture.  It is not
a general snapshot/replay framework and is never imported from the package
root or the public CLI.
"""

from __future__ import annotations

import copy
import hashlib
import json
import platform
import subprocess
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple

from skillstack.adapters.retrieval_to_execution import adapt_retrieval_for_execution
from skillstack.blm import (
    BLM_INTERVENTION_SCHEMA,
    BLM_INTERVENTION_SCHEMA_V2,
    BLM_BOUNDARY_SCHEMA_V2,
    STATE_SCOPE,
    _consumer_registry,
    boundary_state_sha256,
)
from skillstack.execution import SkillPlanExecutor
from skillstack.library import load_static_library
from skillstack.retrieval import NoSkillRetriever, OracleSkillRetriever, RandomSkillRetriever
from skillstack.runner import EpisodeRunner


ENVELOPE_SCHEMA = "skillstack-blm-first-handoff-envelope-v1"
REPLAY_SCHEMA = "skillstack-blm-replay-result-v1"
FIXTURE_ID = "r1_00_heat_calibration"
FIXTURE_SCOPE = "first_handoff_reconstructed_fixture_v1"
BOUNDARY_ID = "r1_00_c1_skillplan"
TOP_K = 1
MAX_STEPS = 12
STEP_BUDGET_PER_PLAN_STEP = 24
CALIBRATION_ARMS = (
    "reference",
    "crossed",
    "crossed_noop",
    "crossed_single_atom",
    "matched_carrier_control",
    "crossed_full_reference_restoration",
)
ATOM_CENSUS_SCHEMA = "skillstack-blm-atom-census-v1"
VERDICT_SCHEMA = "skillstack-blm-verdict-v1"
_MEASUREMENT_STATUSES = {"valid", "invalid", "abstained"}
_CONTRACT_VERDICTS = {"falsified", "not_falsified", "abstained"}
UNREAD_ATOMS = (
    "selected_scores[0]",
    "selected_native_skills[0]",
    "flat_skill_context",
)

TASK: Dict[str, Any] = {
    "task_id": "r1_00_heat_calibration",
    "task_family": "pick_heat_then_place_in_recep",
    "task_instruction": "heat a mug and put it in desk",
    "game_file": "deterministic://r1-00-heat",
    "expected_skill_id": "skill_heat_then_place",
}

INITIAL_OBSERVATION = (
    "You are in the middle of a room.\n"
    "Your task is to: heat a mug and put it in desk."
)
INITIAL_INFO = {
    "admissible_commands": [
        "go to shelf 1",
        "go to microwave 1",
        "go to desk 1",
        "look",
    ]
}

# A declarative digest of the fixture's observable transition surface.  The
# implementation remains deliberately narrow and is only used to detect
# accidental fixture drift before a replay reaches the Consumer.
FIXTURE_SPEC: Dict[str, Any] = {
    "id": FIXTURE_ID,
    "version": "heat-v1",
    "initial_state": {"heated": False, "closed": False},
    "initial_observation": INITIAL_OBSERVATION,
    "initial_info": INITIAL_INFO,
    "terminal": {
        "action": "move mug 1 to desk 1",
        "done": True,
        "success": "reward > 0",
    },
    "transition_actions": [
        "go to shelf 1",
        "take mug 1 from shelf 1",
        "go to microwave 1",
        "heat mug 1 with microwave 1",
        "go to desk 1",
        "move mug 1 to desk 1",
        "look",
    ],
}


class HeatCalibrationEnvironment:
    """Deterministic first-handoff fixture; success requires the heat branch."""

    initial_observation = INITIAL_OBSERVATION
    initial_info = INITIAL_INFO

    def __init__(self) -> None:
        self.heated = False
        self.closed = False
        self._last_observation = self.initial_observation
        self._last_admissible = list(self.initial_info["admissible_commands"])

    def step(self, actions):
        action = actions[0]
        if action == "look":
            # The real executor may use look while exploring a carrier.  Keep
            # it a deterministic, state-preserving observation so a control
            # arm can terminate normally without adding task knowledge.
            return [self._last_observation], [0.0], [False], {
                "admissible_commands": [list(self._last_admissible)]
            }
        transitions = {
            "go to shelf 1": (
                "You arrive at shelf 1. On the shelf 1, you see a mug 1.",
                ["take mug 1 from shelf 1", "go to microwave 1", "go to desk 1", "look"],
            ),
            "take mug 1 from shelf 1": (
                "You pick up the mug 1 from the shelf 1.",
                ["go to microwave 1", "go to desk 1", "look"],
            ),
            "go to microwave 1": (
                "You arrive at microwave 1.",
                ["heat mug 1 with microwave 1", "go to desk 1", "look"],
            ),
            "heat mug 1 with microwave 1": (
                "You heat the mug 1 with the microwave 1.",
                ["go to desk 1", "look"],
            ),
            "go to desk 1": (
                "You arrive at desk 1.",
                ["move mug 1 to desk 1", "look"],
            ),
        }
        if action == "heat mug 1 with microwave 1":
            self.heated = True
        if action == "move mug 1 to desk 1":
            reward = 1.0 if self.heated else 0.0
            self._last_observation = "You move the mug 1 to the desk 1."
            self._last_admissible = []
            return ["You move the mug 1 to the desk 1."], [reward], [True], {
                "admissible_commands": [[]]
            }
        try:
            observation, admissible = transitions[action]
        except KeyError as error:
            raise ValueError(f"Unknown fixture action: {action}") from error
        self._last_observation = observation
        self._last_admissible = list(admissible)
        return [observation], [0.0], [False], {"admissible_commands": [admissible]}

    def close(self) -> None:
        self.closed = True


def create_environment(_data_root: Path, _task_record: Mapping[str, Any]):
    env = HeatCalibrationEnvironment()
    return env, env.initial_observation, copy.deepcopy(env.initial_info)


def materialize_first_handoff_envelope(
    arm_id: str,
    *,
    top_k: int = TOP_K,
    max_steps: int = MAX_STEPS,
) -> Dict[str, Any]:
    """Materialize one frozen C1 first-handoff input, including real outputs."""

    if arm_id not in {"reference", "crossed", "crossed_noop"}:
        raise ValueError(f"R1-02 only materializes reference/crossed/crossed_noop: {arm_id}")
    native_skills = load_static_library()
    retriever, producer_config = _producer_for_arm(arm_id)
    env, initial_observation, initial_info = create_environment(Path("."), TASK)
    try:
        retrieval_response = retriever.retrieve(
            TASK, initial_observation, native_skills, top_k
        )
        execution_input, adapter_event = adapt_retrieval_for_execution(retrieval_response)
        context = _context(
            env,
            initial_observation,
            initial_info,
            native_skills,
            top_k=top_k,
            max_steps=max_steps,
            retrieval_response=retrieval_response,
        )
        state_sha256 = boundary_state_sha256(context)
        request = _capture_request(arm_id)
        if arm_id == "crossed_noop":
            request = {
                "schema_version": BLM_INTERVENTION_SCHEMA,
                "arm_id": "crossed_noop",
                "operation": "copy_atom_from_donor",
                "atom": "selected_skill_ids[0]",
                "expected_state_sha256": state_sha256,
                "donor": {
                    "kind": "producer_output",
                    "task_id": TASK["task_id"],
                    "task_family": TASK["task_family"],
                    "state_sha256": state_sha256,
                    "retrieval_response": copy.deepcopy(retrieval_response),
                },
            }
        envelope: Dict[str, Any] = {
            "schema_version": ENVELOPE_SCHEMA,
            "envelope_id": f"{FIXTURE_ID}:{arm_id}",
            "boundary_id": BOUNDARY_ID,
            "state_scope": FIXTURE_SCOPE,
            "code_revision": _code_revision(),
            "task": copy.deepcopy(TASK),
            "producer": {
                "name": getattr(retriever, "name", type(retriever).__name__),
                "config": producer_config,
                "output": copy.deepcopy(retrieval_response),
            },
            "adapter": {
                "name": "skillstack.adapters.retrieval_to_execution.adapt_retrieval_for_execution",
                "execution_input": copy.deepcopy(execution_input),
                "event": copy.deepcopy(adapter_event),
            },
            "environment": {
                "fixture_id": FIXTURE_ID,
                "fixture_spec": copy.deepcopy(FIXTURE_SPEC),
                "fixture_sha256": _hash_json(FIXTURE_SPEC),
                "class_identity": f"{type(env).__module__}.{type(env).__qualname__}",
                "initial_observation": initial_observation,
                "initial_info": copy.deepcopy(initial_info),
                "constructor_state": {"heated": False, "closed": False},
            },
            "consumer": {
                "name": "skill_plan_executor",
                "step_budget_per_plan_step": STEP_BUDGET_PER_PLAN_STEP,
                "max_steps": max_steps,
                "registry": copy.deepcopy(_consumer_registry()),
                "registry_sha256": _hash_json(_consumer_registry()),
            },
            "native_library": {
                "sha256": _hash_json(native_skills),
                "artifacts": [
                    {
                        "skill_id": artifact["skill_id"],
                        "source_path": artifact["source_path"],
                        "native_payload_sha256": _hash_text(artifact["native_payload"]),
                    }
                    for artifact in native_skills
                ],
            },
            "seed": producer_config.get("seed", "none"),
            "budget": {
                "top_k": top_k,
                "max_steps": max_steps,
                "step_budget_per_plan_step": STEP_BUDGET_PER_PLAN_STEP,
            },
            "oracle": {
                "id": "heat_environment_oracle_v1",
                "type": "environment_task_oracle",
                "success_rule": "done and terminal reward > 0",
            },
            "intervention_request": request,
            "hashes": {
                "state_sha256": state_sha256,
                "producer_output_sha256": _hash_json(retrieval_response),
                "adapter_input_sha256": _hash_json(execution_input),
                "adapter_event_sha256": _hash_json(adapter_event),
            },
        }
        envelope["hashes"]["oracle_sha256"] = _hash_json(envelope["oracle"])
        envelope["hashes"]["envelope_sha256"] = _hash_envelope(envelope)
        return envelope
    finally:
        env.close()


def replay_first_handoff_envelope(envelope: Mapping[str, Any]) -> Dict[str, Any]:
    """Reconstruct one envelope and execute only after every identity check."""

    try:
        _validate_envelope(envelope)
    except ValueError as error:
        return _abstained(f"replay_state_incomplete:{error}")

    native_skills = load_static_library()
    environment = envelope["environment"]
    if (
        environment["fixture_id"] != FIXTURE_ID
        or environment["fixture_spec"] != FIXTURE_SPEC
        or environment["fixture_sha256"] != _hash_json(FIXTURE_SPEC)
        or environment["initial_observation"] != INITIAL_OBSERVATION
        or environment["initial_info"] != INITIAL_INFO
    ):
        return _abstained("replay_state_incomplete:fixture_drift")
    if envelope["consumer"]["registry_sha256"] != _hash_json(_consumer_registry()):
        return _abstained("replay_state_incomplete:consumer_registry_drift")
    if envelope["native_library"]["sha256"] != _hash_json(native_skills):
        return _abstained("replay_state_incomplete:native_library_drift")
    if envelope["hashes"]["envelope_sha256"] != _hash_envelope(envelope):
        return _abstained("replay_state_incomplete:envelope_hash_mismatch")

    producer_name = envelope["producer"]["name"]
    retriever = _retriever_from_config(producer_name, envelope["producer"]["config"])
    env, initial_observation, initial_info = create_environment(Path("."), TASK)
    try:
        actual_response = retriever.retrieve(
            TASK,
            initial_observation,
            native_skills,
            envelope["budget"]["top_k"],
        )
        if actual_response != envelope["producer"]["output"]:
            return _abstained("replay_state_incomplete:producer_output_drift")
        actual_input, actual_event = adapt_retrieval_for_execution(actual_response)
        if actual_input != envelope["adapter"]["execution_input"]:
            return _abstained("replay_state_incomplete:adapter_input_drift")
        if actual_event != envelope["adapter"]["event"]:
            return _abstained("replay_state_incomplete:adapter_event_drift")
        context = _context(
            env,
            initial_observation,
            initial_info,
            native_skills,
            top_k=envelope["budget"]["top_k"],
            max_steps=envelope["budget"]["max_steps"],
            retrieval_response=actual_response,
        )
        if context["environment_class"] != environment["class_identity"]:
            return _abstained("replay_state_incomplete:environment_class_drift")
        state_sha256 = boundary_state_sha256(context)
        if state_sha256 != envelope["hashes"]["state_sha256"]:
            return _abstained("replay_state_incomplete:state_hash_mismatch")
    finally:
        env.close()

    trace = EpisodeRunner(
        data_root=Path("."),
        native_skills=native_skills,
        retriever=retriever,
        executor=SkillPlanExecutor(
            step_budget_per_plan_step=envelope["consumer"]["step_budget_per_plan_step"]
        ),
        environment_factory=create_environment,
    ).run(
        TASK,
        top_k=envelope["budget"]["top_k"],
        max_steps=envelope["budget"]["max_steps"],
        blm_intervention=copy.deepcopy(envelope["intervention_request"]),
    )
    return {
        "schema_version": REPLAY_SCHEMA,
        "measurement_status": "valid",
        "reason": "exact_replay",
        "consumer_called": True,
        "envelope_id": envelope["envelope_id"],
        "trace_projection": stable_projection(trace),
        "boundary": copy.deepcopy(trace.get("blm_boundary")),
    }


def stable_projection(trace: Mapping[str, Any]) -> Dict[str, Any]:
    """Remove timestamps and IDs while retaining the full causal projection."""

    report = trace.get("executor_report", {})
    return {
        "retrieval_response": trace.get("retrieval_response"),
        "selected_skill_ids": trace.get("selected_skill_ids"),
        "selected_native_payloads": trace.get("selected_native_payloads"),
        "adapter_events": trace.get("adapter_events"),
        "raw_observations": trace.get("raw_observations", []),
        "actions": trace.get("actions", []),
        "rewards": trace.get("rewards", []),
        "stop_reason": trace.get("stop_reason"),
        "success": trace.get("success"),
        "plan_skill_id": report.get("plan_skill_id"),
        "plan_steps": report.get("plan_steps"),
        "action_rationales": trace.get("action_rationales", []),
    }


def run_v2_calibration_arm(
    arm_id: str,
    *,
    top_k: int = TOP_K,
    max_steps: int = MAX_STEPS,
) -> Dict[str, Any]:
    """Run one R1-03/R1-04 arm through the v2 first-handoff hook.

    This helper deliberately materializes donors from real retriever outputs at
    the same deterministic handoff.  It is an experiment-only convenience,
    not a public Runner API or a generic intervention registry.
    """

    if arm_id not in CALIBRATION_ARMS and not arm_id.startswith("irrelevant_unread_information:"):
        raise ValueError(f"Unsupported R1 calibration arm: {arm_id}")
    native_skills = load_static_library()
    # Every intervention arm except reference runs on the same crossed seed-1
    # baseline; matched-carrier is a donor source, never the current baseline.
    producer_arm = "reference" if arm_id == "reference" else "crossed"
    retriever, _config = _producer_for_v2_arm(producer_arm)
    env, observation, info = create_environment(Path("."), TASK)
    try:
        response = retriever.retrieve(TASK, observation, native_skills, top_k)
        context = _context(
            env,
            observation,
            info,
            native_skills,
            top_k=top_k,
            max_steps=max_steps,
            retrieval_response=response,
        )
        state_sha256 = boundary_state_sha256(context)
    finally:
        env.close()
    request = build_v2_intervention_request(
        arm_id, state_sha256, native_skills=native_skills, top_k=top_k
    )
    return EpisodeRunner(
        data_root=Path("."),
        native_skills=native_skills,
        retriever=retriever,
        executor=SkillPlanExecutor(step_budget_per_plan_step=STEP_BUDGET_PER_PLAN_STEP),
        environment_factory=create_environment,
    ).run(
        TASK,
        top_k=top_k,
        max_steps=max_steps,
        blm_intervention=request,
    )


def build_v2_intervention_request(
    arm_id: str,
    state_sha256: str,
    *,
    native_skills: Optional[Any] = None,
    top_k: int = TOP_K,
) -> Dict[str, Any]:
    """Build a fixed v2 request, sourcing every donor from a real retriever."""

    if native_skills is None:
        native_skills = load_static_library()
    if arm_id in {"reference", "crossed"}:
        return _v2_capture_request(arm_id)
    current_retriever, _ = _producer_for_v2_arm("crossed")
    matched_retriever, _ = _producer_for_v2_arm("matched_carrier_control")
    oracle = OracleSkillRetriever()
    def retrieve(retriever):
        env, observation, _info = create_environment(Path("."), TASK)
        try:
            return retriever.retrieve(TASK, observation, native_skills, top_k)
        finally:
            env.close()
    if arm_id == "crossed_noop":
        donor_response = retrieve(current_retriever)
        kind = "producer_output"
        operation = "copy_atom_from_donor"
        atom = "selected_skill_ids[0]"
    elif arm_id == "crossed_single_atom":
        donor_response = retrieve(oracle)
        kind = "calibration_oracle"
        operation = "copy_atom_from_donor"
        atom = "selected_skill_ids[0]"
    elif arm_id == "matched_carrier_control":
        donor_response = retrieve(matched_retriever)
        kind = "matched_nonreference"
        operation = "copy_atom_from_donor"
        atom = "selected_skill_ids[0]"
    elif arm_id == "crossed_full_reference_restoration":
        donor_response = retrieve(oracle)
        kind = "calibration_oracle"
        operation = "copy_group_from_donor"
        atom = "reference_handoff_group"
    elif arm_id.startswith("irrelevant_unread_information:"):
        donor_response = retrieve(oracle)
        kind = "calibration_oracle"
        operation = "copy_atom_from_donor"
        atom = arm_id.split(":", 1)[1]
        if atom not in UNREAD_ATOMS:
            raise ValueError(f"Unsupported unread atom: {atom}")
    else:
        raise ValueError(f"Unsupported v2 request arm: {arm_id}")
    return {
        "schema_version": BLM_INTERVENTION_SCHEMA_V2,
        "arm_id": arm_id.split(":", 1)[0],
        "operation": operation,
        "atom": atom,
        "expected_state_sha256": state_sha256,
        "donor": {
            "kind": kind,
            "task_id": TASK["task_id"],
            "task_family": TASK["task_family"],
            "state_sha256": state_sha256,
            "retrieval_response": donor_response,
        },
    }


def _v2_capture_request(arm_id: str) -> Dict[str, Any]:
    return {
        "schema_version": BLM_INTERVENTION_SCHEMA_V2,
        "arm_id": arm_id,
        "operation": "capture",
        "atom": None,
        "expected_state_sha256": None,
        "donor": None,
    }


def _producer_for_v2_arm(arm_id: str):
    if arm_id == "reference":
        return OracleSkillRetriever(), {"selection_policy": "frozen_task_family_mapping"}
    if arm_id == "matched_carrier_control":
        return RandomSkillRetriever(seed=3), {
            "selection_policy": "seeded_shuffle_per_task",
            "seed": 3,
        }
    return RandomSkillRetriever(seed=1), {
        "selection_policy": "seeded_shuffle_per_task",
        "seed": 1,
    }


def build_atom_census(reference_trace: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Return the frozen C1 atom census with optional runtime read evidence."""

    if reference_trace is None:
        reference_trace = run_v2_calibration_arm("reference")
    boundary = reference_trace.get("blm_boundary", {})
    events = boundary.get("consumer_reads", [])
    source_path = Path(__file__).resolve().parents[1] / "execution" / "skillplan.py"
    source_digest = _file_hash(source_path)

    def access_for(paths):
        return [event for event in events if event.get("path") in paths]

    records = [
        {
            "atom_id": "selected_skill_ids[0]",
            "carrier_path": "execution_input.selected_skill_ids[0]",
            "read_map_id": "r1_00_c1.skillplan.semantic.selected_skill_ids[0]",
            "declared_semantics": "top-ranked skill identity selects the Consumer plan skeleton",
            "transport_status": "transmitted_by_adapter",
            "static_read": {
                "file": "src/skillstack/execution/skillplan.py",
                "function": "SkillPlanExecutor.execute",
                "expression": "skill_ids = execution_input[\"selected_skill_ids\"]; top_skill_id = skill_ids[0] if skill_ids else None",
                "source_sha256": source_digest,
            },
            "runtime_access": access_for(("selected_skill_ids", "selected_skill_ids[0]")),
            "read_type": "semantic_read_after_schema_validation",
            "value_domain": "non-empty string skill id; index 0 only",
            "intervenability": "independent_atom",
            "donor_categories": ["calibration_oracle", "matched_nonreference", "producer_output_noop"],
            "trace_exposure": "top-level selected_skill_ids and v2 sidecar consumer_reads",
            "evidence_class": "verified_this_run",
            "claim_boundary": "local SkillPlanExecutor branch selection on the frozen fixture",
        },
        {
            "atom_id": "top_rank_order",
            "carrier_path": "execution_input.selected_skill_ids ordering",
            "read_map_id": "r1_00_c1.skillplan.semantic.selected_skill_ids[0]",
            "declared_semantics": "rank/order is inseparable from the selected top identity for this Consumer",
            "transport_status": "transmitted_by_adapter",
            "static_read": {
                "file": "src/skillstack/execution/skillplan.py",
                "function": "SkillPlanExecutor.execute",
                "expression": "skill_ids[0] if skill_ids else None",
                "source_sha256": source_digest,
            },
            "runtime_access": access_for(("selected_skill_ids[0]",)),
            "read_type": "semantic_read",
            "value_domain": "ordered list; top-k rank controls index 0",
            "intervenability": "inseparable_group_with_selected_skill_ids",
            "donor_categories": ["calibration_oracle", "matched_nonreference"],
            "trace_exposure": "selected_skill_ids list in top-level trace",
            "evidence_class": "calibration_only",
            "claim_boundary": "do not attribute rank independently from identity without a separate Consumer read",
        },
        {
            "atom_id": "selected_scores[0]",
            "carrier_path": "execution_input.selected_scores[0]",
            "read_map_id": "r1_00_c1.skillplan.validation.selected_scores[0]",
            "declared_semantics": "retrieval score is declared metadata but not a known Consumer decision input",
            "transport_status": "transmitted_by_adapter",
            "static_read": {
                "file": "src/skillstack/execution/skillplan.py",
                "function": "_validate_execution_input",
                "expression": "field not in execution_input (field=\"selected_scores\")",
                "source_sha256": source_digest,
            },
            "runtime_access": access_for(("selected_scores", "selected_scores[0]")),
            "read_type": "validation_only",
            "value_domain": "finite numeric list aligned with candidate lists",
            "intervenability": "independent_atom_but_unread_by_current_consumer",
            "donor_categories": ["calibration_oracle"],
            "trace_exposure": "top-level retrieval response and adapter output; no semantic Consumer read",
            "evidence_class": "verified_this_run",
            "claim_boundary": "negative control only; no claim about hidden model reads",
        },
        {
            "atom_id": "selected_native_skills[0]",
            "carrier_path": "execution_input.selected_native_skills[0]",
            "read_map_id": "r1_00_c1.skillplan.validation.selected_native_skills[0]",
            "declared_semantics": "native skill payload is transported and schema-presence validated",
            "transport_status": "transmitted_by_adapter",
            "static_read": {
                "file": "src/skillstack/execution/skillplan.py",
                "function": "_validate_execution_input",
                "expression": "field not in execution_input (field=\"selected_native_skills\")",
                "source_sha256": source_digest,
            },
            "runtime_access": access_for(("selected_native_skills", "selected_native_skills[0]")),
            "read_type": "validation_only",
            "value_domain": "opaque native payload string aligned with selected IDs",
            "intervenability": "opaque_unread_information",
            "donor_categories": ["calibration_oracle"],
            "trace_exposure": "top-level selected_native_payloads; not a semantic Consumer read",
            "evidence_class": "verified_this_run",
            "claim_boundary": "do not call this transport omission; only an unread negative control",
        },
        {
            "atom_id": "flat_skill_context",
            "carrier_path": "execution_input.flat_skill_context",
            "read_map_id": "r1_00_c1.skillplan.validation.flat_skill_context",
            "declared_semantics": "adapter-derived flat prompt-like carrier",
            "transport_status": "transmitted_by_adapter",
            "static_read": {
                "file": "src/skillstack/execution/skillplan.py",
                "function": "_validate_execution_input",
                "expression": "field not in execution_input (field=\"flat_skill_context\")",
                "source_sha256": source_digest,
            },
            "runtime_access": access_for(("flat_skill_context",)),
            "read_type": "validation_only",
            "value_domain": "derived string carrier",
            "intervenability": "opaque_unread_information",
            "donor_categories": ["calibration_oracle"],
            "trace_exposure": "not included in current top-level trace; v2 input hash only",
            "evidence_class": "verified_this_run",
            "claim_boundary": "prompt exposure is not evidence of model-internal reading",
        },
        {
            "atom_id": "consumer_local_registry",
            "carrier_path": "SkillPlanExecutor.PLAN_STEPS_BY_SKILL",
            "read_map_id": "r1_00_c1.skillplan.local_registry",
            "declared_semantics": "hard-coded skill-id to plan mapping used by the Consumer",
            "transport_status": "consumer_local_not_transport_payload",
            "static_read": {
                "file": "src/skillstack/execution/skillplan.py",
                "function": "SkillPlanExecutor.execute",
                "expression": "elif top_skill_id in PLAN_STEPS_BY_SKILL: plan = list(PLAN_STEPS_BY_SKILL[top_skill_id])",
                "source_sha256": source_digest,
            },
            "runtime_access": {
                "status": "static_verified_runtime_indirect",
                "events": [],
                "reason": "wrapper cannot observe module-level registry lookup without changing Consumer code",
            },
            "read_type": "semantic_read_static_verified_runtime_indirect",
            "value_domain": "Consumer-local mapping keyed by skill id",
            "intervenability": "environment_not_producer_atom",
            "donor_categories": [],
            "trace_exposure": "executor_report.plan_skill_id and plan_steps",
            "evidence_class": "historical_evidence_plus_verified_this_run",
            "claim_boundary": "known hand-written calibration mechanism; not a Producer payload atom",
        },
        {
            "atom_id": "task_observation_commands",
            "carrier_path": "task_record / initial_observation / initial_info.admissible_commands",
            "read_map_id": "r1_00_c1.environment_state",
            "declared_semantics": "environment/task state used to bind actions",
            "transport_status": "environment_state_not_d_to_c_payload",
            "static_read": {
                "file": "src/skillstack/execution/skillplan.py",
                "function": "SkillPlanExecutor.execute",
                "expression": "parse_task_semantics(task_record, initial_observation); current_info=initial_info",
                "source_sha256": source_digest,
            },
            "runtime_access": [],
            "read_type": "environment_state",
            "value_domain": "fixture task and observation state",
            "intervenability": "environment_not_atom",
            "donor_categories": [],
            "trace_exposure": "top-level task and raw_observations",
            "evidence_class": "verified_this_run",
            "claim_boundary": "must not be relabeled as D→C payload",
        },
    ]
    census = {
        "schema_version": ATOM_CENSUS_SCHEMA,
        "boundary_id": BOUNDARY_ID,
        "state_scope": FIXTURE_SCOPE,
        "source_consumer": "skill_plan_executor",
        "records": records,
    }
    validate_atom_census(census)
    validate_runtime_reads(census, events)
    return census


def validate_atom_census(census: Any) -> None:
    """Fail closed on duplicate/unknown/incomplete atom records."""

    records = census.get("records") if isinstance(census, Mapping) else census
    if not isinstance(records, list):
        raise ValueError("atom_census_records")
    expected = {
        "selected_skill_ids[0]",
        "top_rank_order",
        "selected_scores[0]",
        "selected_native_skills[0]",
        "flat_skill_context",
        "consumer_local_registry",
        "task_observation_commands",
    }
    ids = [record.get("atom_id") for record in records if isinstance(record, Mapping)]
    if len(ids) != len(set(ids)) or set(ids) != expected:
        raise ValueError("atom_census_atom_ids")
    for record in records:
        if not isinstance(record.get("read_map_id"), str) or not record["read_map_id"]:
            raise ValueError("atom_census_read_map_id")
        if not isinstance(record.get("carrier_path"), str):
            raise ValueError("atom_census_carrier_path")


def validate_runtime_reads(census: Mapping[str, Any], events: Any) -> None:
    """Check that the runtime tracker agrees with the frozen read classes."""

    if not isinstance(events, list):
        raise ValueError("blocked_atom_census_mismatch")
    unread_paths = {
        "selected_scores[0]",
        "selected_native_skills[0]",
        "flat_skill_context",
    }
    if any(
        event.get("path") in unread_paths and event.get("read_type") == "semantic_read"
        for event in events
        if isinstance(event, Mapping)
    ):
        raise ValueError("blocked_atom_census_mismatch")
    identity_semantic = [
        event for event in events
        if isinstance(event, Mapping)
        and event.get("path") == "selected_skill_ids[0]"
        and event.get("read_type") == "semantic_read"
    ]
    identity_record = next(
        (record for record in census.get("records", [])
         if record.get("atom_id") == "selected_skill_ids[0]"),
        None,
    )
    if identity_record is None:
        raise ValueError("blocked_atom_census_mismatch")
    expected_identity = [
        event for event in identity_record.get("runtime_access", [])
        if event.get("path") == "selected_skill_ids[0]"
        and event.get("read_type") == "semantic_read"
    ]
    if len(identity_semantic) != len(expected_identity):
        raise ValueError("blocked_atom_census_mismatch")


def evaluate_calibration_case(case_record: Mapping[str, Any]) -> Dict[str, Any]:
    """Evaluate one bounded calibration record without widening its claim."""

    if not isinstance(case_record, Mapping) or not isinstance(case_record.get("case_id"), str):
        raise ValueError("case_id_required")
    case_id = case_record["case_id"]
    measurement_status = case_record.get("measurement_status")
    if measurement_status not in _MEASUREMENT_STATUSES:
        measurement_status = "abstained"
        initial_reason = "invalid_measurement_status"
    else:
        initial_reason = None
    claim = case_record.get("claim")
    claim_id = case_record.get("claim_id")
    if claim_id is None and isinstance(claim, Mapping):
        claim_id = claim.get("claim_id")
    scope = case_record.get("verdict_scope")
    if scope is None and isinstance(claim, Mapping):
        scope = claim.get("scope")
    evidence_refs = case_record.get("evidence_refs", [])
    excluded_claims = case_record.get("excluded_claims", [])
    record: Dict[str, Any] = {
        "schema_version": VERDICT_SCHEMA,
        "case_id": case_id,
        "measurement_status": measurement_status,
        "contract_verdict": "abstained",
        "reason_code": initial_reason or "unclassified",
        "claim_id": claim_id,
        "verdict_scope": scope,
        "calibration_only": bool(case_record.get("calibration_only", True)),
        "evidence_refs": list(evidence_refs) if isinstance(evidence_refs, list) else [],
        "excluded_claims": list(excluded_claims) if isinstance(excluded_claims, list) else [],
    }
    if initial_reason is not None:
        return record
    if measurement_status != "valid":
        record["reason_code"] = case_record.get(
            "reason_code", "measurement_not_valid"
        )
        return record
    if not isinstance(claim, Mapping) or not claim.get("explicit"):
        record["reason_code"] = "no_explicit_falsifiable_claim"
        return record
    claim_type = claim.get("type")
    if claim_type not in {"conformance", "sufficiency", "synthetic_independent_sufficiency"}:
        record["reason_code"] = "claim_type_not_registered"
        return record
    if not isinstance(scope, str) or not scope:
        record["reason_code"] = "claim_scope_missing"
        return record
    if not case_record.get("gates_complete", False):
        record["reason_code"] = "incomplete_gate"
        return record
    diagnostic = case_record.get("diagnostic")
    if diagnostic in {
        "adapter_transport_nonconformance",
        "consumer_semantic_read_unverified",
        "replay_state_incomplete",
        "no_op_changed_result",
        "incomplete_arm",
        "budget_exhausted",
    }:
        record["reason_code"] = diagnostic
        return record
    observed = case_record.get("observed_relation")
    if claim_type == "synthetic_independent_sufficiency":
        if not case_record.get("synthetic_test_only", False):
            record["reason_code"] = "synthetic_claim_not_isolated"
            return record
        if observed == "joint_only":
            record["contract_verdict"] = "falsified"
            record["reason_code"] = "synthetic_independent_sufficiency_failed"
            return record
        record["reason_code"] = "synthetic_case_inconclusive"
        return record
    if observed in {"exact_match", "single_atom_exact", "no_change", "reference_exact"}:
        record["contract_verdict"] = "not_falsified"
        record["reason_code"] = case_record.get("reason_code", "bounded_case_exact")
        return record
    record["reason_code"] = "outcome_not_reconstructable"
    return record


def _producer_for_arm(arm_id: str):
    if arm_id == "reference":
        return OracleSkillRetriever(), {"selection_policy": "frozen_task_family_mapping"}
    return RandomSkillRetriever(seed=1), {
        "selection_policy": "seeded_shuffle_per_task",
        "seed": 1,
    }


def _retriever_from_config(name: str, config: Mapping[str, Any]):
    if name == "oracle_skill":
        return OracleSkillRetriever()
    if name == "random_skill" and config.get("seed") == 1:
        return RandomSkillRetriever(seed=1)
    if name == "no_skill":
        return NoSkillRetriever()
    raise ValueError(f"Unsupported R1-02 producer: {name}")


def _capture_request(arm_id: str) -> Dict[str, Any]:
    return {
        "schema_version": BLM_INTERVENTION_SCHEMA,
        "arm_id": arm_id,
        "operation": "capture",
        "atom": None,
        "expected_state_sha256": None,
        "donor": None,
    }


def _context(
    env: Any,
    initial_observation: str,
    initial_info: Mapping[str, Any],
    native_skills: Any,
    *,
    top_k: int,
    max_steps: int,
    retrieval_response: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        "task_record": TASK,
        "initial_observation": initial_observation,
        "initial_info": copy.deepcopy(dict(initial_info)),
        "environment_class": f"{type(env).__module__}.{type(env).__qualname__}",
        "consumer_name": "skill_plan_executor",
        "consumer_step_budget": STEP_BUDGET_PER_PLAN_STEP,
        "native_skills": native_skills,
        "top_k": top_k,
        "effective_max_steps": max_steps,
        "state_scope": STATE_SCOPE,
        "retrieval_response": retrieval_response,
    }


def _validate_envelope(envelope: Mapping[str, Any]) -> None:
    required = {
        "schema_version",
        "envelope_id",
        "boundary_id",
        "state_scope",
        "code_revision",
        "task",
        "producer",
        "adapter",
        "environment",
        "consumer",
        "native_library",
        "seed",
        "budget",
        "oracle",
        "intervention_request",
        "hashes",
    }
    if set(envelope) != required:
        raise ValueError("envelope_schema")
    if envelope["schema_version"] != ENVELOPE_SCHEMA:
        raise ValueError("envelope_schema")
    if envelope["boundary_id"] != BOUNDARY_ID or envelope["state_scope"] != FIXTURE_SCOPE:
        raise ValueError("boundary_scope")
    code_revision = envelope["code_revision"]
    if not isinstance(code_revision, Mapping):
        raise ValueError("code_revision")
    if code_revision.get("module_path") != "src/skillstack/experiments/blm_calibration.py":
        raise ValueError("code_revision")
    if code_revision.get("module_sha256") != _file_hash(Path(__file__).resolve()):
        raise ValueError("code_revision")
    if code_revision.get("python") != platform.python_version():
        raise ValueError("code_revision")
    if code_revision.get("platform") != platform.platform():
        raise ValueError("code_revision")
    if envelope["task"] != TASK:
        raise ValueError("task_mismatch")
    for section in ("producer", "adapter", "environment", "consumer", "native_library", "hashes"):
        if not isinstance(envelope.get(section), Mapping):
            raise ValueError(f"{section}_schema")
    if not isinstance(envelope["producer"].get("name"), str) or not isinstance(
        envelope["producer"].get("config"), Mapping
    ):
        raise ValueError("producer_schema")
    if not isinstance(envelope["adapter"].get("execution_input"), Mapping) or not isinstance(
        envelope["adapter"].get("event"), Mapping
    ):
        raise ValueError("adapter_schema")
    if envelope["environment"].get("fixture_id") != FIXTURE_ID:
        raise ValueError("fixture_schema")
    if not isinstance(envelope["consumer"].get("registry"), Mapping):
        raise ValueError("consumer_schema")
    if envelope["consumer"].get("registry_sha256") != _hash_json(
        envelope["consumer"]["registry"]
    ):
        raise ValueError("consumer_registry_hash")
    if envelope["native_library"].get("sha256") != _hash_json(
        load_static_library()
    ):
        # This is checked again by the replayer after the complete library is
        # loaded; keeping the check here prevents malformed envelopes from
        # reaching a Consumer even when their outer hash is recomputed.
        raise ValueError("native_library_hash")
    if envelope["oracle"] != {
        "id": "heat_environment_oracle_v1",
        "type": "environment_task_oracle",
        "success_rule": "done and terminal reward > 0",
    }:
        raise ValueError("oracle_mismatch")
    if envelope["hashes"].get("oracle_sha256") != _hash_json(envelope["oracle"]):
        raise ValueError("oracle_hash")
    if envelope["hashes"].get("producer_output_sha256") != _hash_json(
        envelope["producer"]["output"]
    ):
        raise ValueError("producer_hash")
    if envelope["hashes"].get("adapter_input_sha256") != _hash_json(
        envelope["adapter"]["execution_input"]
    ):
        raise ValueError("adapter_hash")
    if envelope["hashes"].get("adapter_event_sha256") != _hash_json(
        envelope["adapter"]["event"]
    ):
        raise ValueError("adapter_event_hash")
    budget = envelope["budget"]
    if budget != {
        "top_k": TOP_K,
        "max_steps": MAX_STEPS,
        "step_budget_per_plan_step": STEP_BUDGET_PER_PLAN_STEP,
    }:
        raise ValueError("budget_mismatch")
    if envelope["consumer"]["step_budget_per_plan_step"] != STEP_BUDGET_PER_PLAN_STEP:
        raise ValueError("consumer_budget")
    if envelope["environment"]["class_identity"] != (
        f"{HeatCalibrationEnvironment.__module__}.{HeatCalibrationEnvironment.__qualname__}"
    ):
        raise ValueError("environment_class")
    if not isinstance(envelope.get("intervention_request"), Mapping):
        raise ValueError("intervention_schema")


def _code_revision() -> Dict[str, Any]:
    module_path = Path(__file__).resolve()
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=module_path.parents[3],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "unavailable"
    return {
        "git_commit": commit,
        "module_path": "src/skillstack/experiments/blm_calibration.py",
        "module_sha256": _file_hash(module_path),
        "python": platform.python_version(),
        "platform": platform.platform(),
    }


def _hash_envelope(envelope: Mapping[str, Any]) -> str:
    payload = copy.deepcopy(dict(envelope))
    payload.setdefault("hashes", {}).pop("envelope_sha256", None)
    return _hash_json(payload)


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


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _abstained(reason: str) -> Dict[str, Any]:
    return {
        "schema_version": REPLAY_SCHEMA,
        "measurement_status": "abstained",
        "reason": "replay_state_incomplete",
        "reason_detail": reason,
        "consumer_called": False,
        "envelope_id": None,
        "trace_projection": None,
        "boundary": None,
    }
