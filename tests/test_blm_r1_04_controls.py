from __future__ import annotations

import copy
import unittest
from pathlib import Path

from skillstack.adapters.retrieval_to_execution import adapt_retrieval_for_execution
from skillstack.blm import apply_boundary_intervention, boundary_state_sha256
from skillstack.execution import SkillPlanExecutor
from skillstack.library import load_static_library
from skillstack.retrieval import OracleSkillRetriever, RandomSkillRetriever
from skillstack.runner import EpisodeRunner
from skillstack.experiments.blm_calibration import (
    TASK,
    STEP_BUDGET_PER_PLAN_STEP,
    build_v2_intervention_request,
    create_environment,
    run_v2_calibration_arm,
)


class _SpyExecutor(SkillPlanExecutor):
    def __init__(self) -> None:
        super().__init__(step_budget_per_plan_step=STEP_BUDGET_PER_PLAN_STEP)
        self.calls = 0

    def execute(self, *args, **kwargs):
        self.calls += 1
        return super().execute(*args, **kwargs)


class R104RestorationControlTests(unittest.TestCase):
    def test_all_main_arms_and_unread_probes_are_three_times_exact(self) -> None:
        arms = (
            "reference",
            "crossed",
            "crossed_noop",
            "crossed_single_atom",
            "matched_carrier_control",
            "crossed_full_reference_restoration",
            "irrelevant_unread_information:selected_scores[0]",
            "irrelevant_unread_information:selected_native_skills[0]",
            "irrelevant_unread_information:flat_skill_context",
        )
        for arm in arms:
            traces = [run_v2_calibration_arm(arm) for _ in range(3)]
            projection = [
                {
                    "actions": trace["actions"],
                    "raw_observations": trace["raw_observations"],
                    "rewards": trace["rewards"],
                    "success": trace["success"],
                    "stop_reason": trace["stop_reason"],
                    "branch": trace["blm_boundary"]["consumer_branch"],
                }
                for trace in traces
            ]
            self.assertEqual(projection[0], projection[1], arm)
            self.assertEqual(projection[0], projection[2], arm)
            self.assertEqual("valid", traces[0]["blm_boundary"]["validity"], arm)

    def test_single_atom_restoration_keeps_crossed_carriers(self) -> None:
        crossed = run_v2_calibration_arm("crossed")
        restored = run_v2_calibration_arm("crossed_single_atom")
        self.assertEqual(crossed["selected_native_payloads"], restored["selected_native_payloads"])
        self.assertEqual(crossed["retrieval_response"], restored["retrieval_response"])
        self.assertEqual("skill_heat_then_place", restored["selected_skill_ids"][0])
        self.assertTrue(restored["blm_boundary"]["changed"])
        self.assertTrue(restored["blm_boundary"]["donor_provenance"]["calibration_only"])

    def test_matched_carrier_is_nonreference_and_does_not_reach_oracle_success(self) -> None:
        trace = run_v2_calibration_arm("matched_carrier_control")
        boundary = trace["blm_boundary"]
        self.assertEqual("skill_light_inspection", boundary["consumer_branch"])
        self.assertFalse(trace["success"])
        self.assertNotEqual("skill_heat_then_place", boundary["consumer_branch"])
        self.assertFalse(boundary["donor_provenance"]["calibration_only"])

    def test_full_group_restoration_matches_reference_input_hash(self) -> None:
        reference = run_v2_calibration_arm("reference")
        full = run_v2_calibration_arm("crossed_full_reference_restoration")
        self.assertEqual(
            reference["blm_boundary"]["original_input_sha256"],
            reference["blm_boundary"]["effective_input_sha256"],
        )
        self.assertEqual(
            reference["blm_boundary"]["effective_input_sha256"],
            full["blm_boundary"]["effective_input_sha256"],
        )
        self.assertEqual(reference["actions"], full["actions"])

    def test_invalid_group_and_donor_are_rejected_before_consumer(self) -> None:
        native = load_static_library()
        retriever = RandomSkillRetriever(seed=1)
        env, observation, info = create_environment(Path("."), TASK)
        try:
            response = retriever.retrieve(TASK, observation, native, 1)
            execution_input, _event = adapt_retrieval_for_execution(response)
            context = {
                "task_record": TASK,
                "initial_observation": observation,
                "initial_info": info,
                "environment_class": f"{type(env).__module__}.{type(env).__qualname__}",
                "consumer_name": "skill_plan_executor",
                "consumer_step_budget": STEP_BUDGET_PER_PLAN_STEP,
                "native_skills": native,
                "top_k": 1,
                "effective_max_steps": 12,
                "state_scope": "first_handoff_reconstructed_fixture_v1",
                "retrieval_response": response,
            }
            state = boundary_state_sha256(context)
        finally:
            env.close()
        oracle = OracleSkillRetriever().retrieve(TASK, observation, native, 1)
        base = {
            "schema_version": "skillstack-blm-intervention-v2",
            "arm_id": "crossed_full_reference_restoration",
            "operation": "copy_group_from_donor",
            "atom": "reference_handoff_group",
            "expected_state_sha256": state,
            "donor": {
                "kind": "calibration_oracle",
                "task_id": TASK["task_id"],
                "task_family": TASK["task_family"],
                "state_sha256": state,
                "retrieval_response": oracle,
            },
        }
        malformed = copy.deepcopy(base)
        malformed["donor"]["retrieval_response"]["ranked_candidates"].append(
            copy.deepcopy(response["ranked_candidates"][0])
        )
        effective, record = apply_boundary_intervention(execution_input, malformed, context)
        self.assertIsNone(effective)
        self.assertEqual("invalid_donor_source", record["validity_reason"])

        misaligned = copy.deepcopy(base)
        misaligned["donor"]["retrieval_response"] = copy.deepcopy(oracle)
        malformed_input = copy.deepcopy(execution_input)
        malformed_input["selected_scores"] = []
        effective, record = apply_boundary_intervention(malformed_input, misaligned, context)
        self.assertIsNone(effective)
        self.assertEqual("invalid_list_alignment", record["validity_reason"])

    def test_v2_invalid_state_and_forbidden_content_stop_before_consumer(self) -> None:
        crossed = run_v2_calibration_arm("crossed")
        state = crossed["blm_boundary"]["state_sha256"]
        request = build_v2_intervention_request("crossed_single_atom", state)
        request["expected_state_sha256"] = "0" * 64
        spy = _SpyExecutor()
        trace = EpisodeRunner(
            Path("."), load_static_library(), RandomSkillRetriever(seed=1), spy,
            environment_factory=create_environment,
        ).run(TASK, top_k=1, max_steps=12, blm_intervention=request)
        self.assertEqual("invalid_input", trace["stop_reason"])
        self.assertEqual("invalid_donor_state", trace["blm_boundary"]["validity_reason"])
        self.assertEqual(0, spy.calls)

        forbidden = build_v2_intervention_request("crossed_single_atom", state)
        forbidden["donor"]["retrieval_response"]["raw_output"]["trajectory"] = []
        trace = EpisodeRunner(
            Path("."), load_static_library(), RandomSkillRetriever(seed=1), _SpyExecutor(),
            environment_factory=create_environment,
        ).run(TASK, top_k=1, max_steps=12, blm_intervention=forbidden)
        self.assertEqual("invalid_input", trace["stop_reason"])
        self.assertEqual("forbidden_outcome_content", trace["blm_boundary"]["validity_reason"])


if __name__ == "__main__":
    unittest.main()
