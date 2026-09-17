from __future__ import annotations

import copy
import unittest
from pathlib import Path
from unittest.mock import patch

from skillstack.adapters.retrieval_to_execution import adapt_retrieval_for_execution
from skillstack.execution import SkillPlanExecutor
from skillstack.library import load_static_library
from skillstack.retrieval import NoSkillRetriever, OracleSkillRetriever
from skillstack.runner import EpisodeRunner
from skillstack.experiments.blm_calibration import TASK, create_environment


def stable_projection(trace):
    return {
        "retrieval_response": trace["retrieval_response"],
        "selected_skill_ids": trace["selected_skill_ids"],
        "selected_native_payloads": trace["selected_native_payloads"],
        "adapter_events": trace["adapter_events"],
        "actions": trace["actions"],
        "stop_reason": trace["stop_reason"],
        "success": trace["success"],
        "plan_skill_id": trace["executor_report"]["plan_skill_id"],
        "plan_steps": trace["executor_report"]["plan_steps"],
    }


class R100ReplayFeasibilityTests(unittest.TestCase):
    def run_episode(self, retriever):
        return EpisodeRunner(
            data_root=Path("."),
            native_skills=load_static_library(),
            retriever=retriever,
            executor=SkillPlanExecutor(),
            environment_factory=create_environment,
        ).run(TASK, top_k=1, max_steps=12)

    def test_primary_boundary_reconstructs_exactly_three_times(self) -> None:
        projections = [
            stable_projection(self.run_episode(OracleSkillRetriever()))
            for _ in range(3)
        ]
        self.assertEqual(projections[0], projections[1])
        self.assertEqual(projections[0], projections[2])
        self.assertEqual("environment_done", projections[0]["stop_reason"])
        self.assertTrue(projections[0]["success"])

    def test_noop_adapter_observation_matches_uninstrumented_baseline(self) -> None:
        baseline = stable_projection(self.run_episode(OracleSkillRetriever()))
        observed_inputs = []

        def observe_without_modifying(retrieval_response):
            execution_input, event = adapt_retrieval_for_execution(retrieval_response)
            observed_inputs.append(copy.deepcopy(execution_input))
            return execution_input, event

        with patch(
            "skillstack.runner.adapt_retrieval_for_execution",
            side_effect=observe_without_modifying,
        ):
            instrumented = stable_projection(self.run_episode(OracleSkillRetriever()))

        self.assertEqual(baseline, instrumented)
        self.assertEqual(["skill_heat_then_place"], observed_inputs[0]["selected_skill_ids"])

    def test_outcome_is_sensitive_to_actual_producer_output(self) -> None:
        reference = stable_projection(self.run_episode(OracleSkillRetriever()))
        no_skill = stable_projection(self.run_episode(NoSkillRetriever()))

        self.assertTrue(reference["success"])
        self.assertFalse(no_skill["success"])
        self.assertNotEqual(reference["actions"], no_skill["actions"])


if __name__ == "__main__":
    unittest.main()
