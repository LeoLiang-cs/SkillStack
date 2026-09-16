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


class HeatCalibrationEnvironment:
    """Deterministic first-handoff fixture; success requires the heat plan branch."""

    initial_observation = (
        "You are in the middle of a room.\n"
        "Your task is to: heat a mug and put it in desk."
    )
    initial_info = {
        "admissible_commands": [
            "go to shelf 1",
            "go to microwave 1",
            "go to desk 1",
            "look",
        ]
    }

    def __init__(self) -> None:
        self.heated = False
        self.closed = False

    def step(self, actions):
        action = actions[0]
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
            return ["You move the mug 1 to the desk 1."], [reward], [True], {
                "admissible_commands": [[]]
            }
        observation, admissible = transitions[action]
        return [observation], [0.0], [False], {"admissible_commands": [admissible]}

    def close(self) -> None:
        self.closed = True


TASK = {
    "task_id": "r1_00_heat_calibration",
    "task_family": "pick_heat_then_place_in_recep",
    "task_instruction": "heat a mug and put it in desk",
    "game_file": "deterministic://r1-00-heat",
    "expected_skill_id": "skill_heat_then_place",
}


def create_environment(_data_root, _task_record):
    env = HeatCalibrationEnvironment()
    return env, env.initial_observation, copy.deepcopy(env.initial_info)


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
