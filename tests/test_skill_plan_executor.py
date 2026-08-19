from __future__ import annotations

import unittest

from skillstack.execution.skillplan import SkillPlanExecutor
from skillstack.task_semantics import parse_task_semantics


class ScriptedEnvironment:
    """Fake ALFWorld env replaying a hard-coded pick-and-place episode."""

    def __init__(self) -> None:
        self.script = {
            "go to shelf 1": (
                "You arrive at shelf 1. On the shelf 1, you see a mug 1.",
                0.0,
                False,
                ["take mug 1 from shelf 1", "go to desk 1", "look"],
            ),
            "take mug 1 from shelf 1": (
                "You pick up the mug 1 from the shelf 1.",
                0.0,
                False,
                ["go to desk 1", "look"],
            ),
            "go to desk 1": (
                "You arrive at desk 1. On the desk 1, you see nothing.",
                0.0,
                False,
                ["move mug 1 to desk 1", "look"],
            ),
            "move mug 1 to desk 1": (
                "You move the mug 1 to the desk 1.",
                1.0,
                True,
                ["look"],
            ),
        }
        self.current_admissible = ["go to shelf 1", "go to desk 1", "look"]

    def step(self, actions):
        action = actions[0]
        if action == "look":
            return ["You look around and see nothing new."], [0.0], [False], {
                "admissible_commands": [list(self.current_admissible)]
            }
        if action not in self.script:
            raise AssertionError(f"Unexpected action in scripted environment: {action}")
        obs, reward, done, admissible = self.script[action]
        self.current_admissible = admissible
        return [obs], [reward], [done], {"admissible_commands": [admissible]}


class SkillPlanExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.executor = SkillPlanExecutor()
        self.task_record = {
            "task_id": "t0",
            "task_family": "pick_and_place_simple",
            "task_instruction": "put a mug in desk",
            "game_file": "ignored",
        }
        self.initial_observation = (
            "You are in the middle of a room.\nYour task is to: put a mug in desk."
        )
        self.initial_info = {
            "admissible_commands": ["go to shelf 1", "go to desk 1", "look"]
        }
        self.execution_input = {
            "selected_skill_ids": ["skill_pick_and_place"],
            "selected_scores": [1.0],
            "selected_native_skills": ["# skill"],
            "flat_skill_context": "# skill",
        }

    def test_executes_skill_plan_to_success(self) -> None:
        report = self.executor.execute(
            ScriptedEnvironment(),
            self.initial_observation,
            self.initial_info,
            self.execution_input,
            task_record=self.task_record,
            max_steps=20,
        )
        self.assertTrue(report["success"])
        self.assertEqual("environment_done", report["stop_reason"])
        self.assertEqual(
            ["go to shelf 1", "take mug 1 from shelf 1", "go to desk 1", "move mug 1 to desk 1"],
            report["actions"],
        )
        executed_rationales = [
            rationale for rationale in report["action_rationales"] if rationale["chosen_action"] is not None
        ]
        self.assertEqual(len(report["actions"]), len(executed_rationales))
        for rationale in executed_rationales:
            self.assertEqual("skill_pick_and_place", rationale["skill_id"])

    def test_no_skill_plan_on_light_task_stops_without_appliance_step(self) -> None:
        task_record = dict(
            self.task_record,
            task_family="look_at_obj_in_light",
            task_instruction="examine the alarmclock with the desklamp",
        )
        initial_observation = (
            "You are in the middle of a room.\n"
            "Your task is to: examine the alarmclock with the desklamp."
        )
        report = self.executor.execute(
            ScriptedEnvironment(),
            initial_observation,
            self.initial_info,
            {
                "selected_skill_ids": [],
                "selected_scores": [],
                "selected_native_skills": [],
                "flat_skill_context": "",
            },
            task_record=task_record,
            max_steps=20,
        )
        # Generic no-skill plan cannot bind a destination for a lamp task, so
        # the executor must stop with an explicit unavailable-step reason
        # instead of acting randomly.
        self.assertFalse(report["success"])
        self.assertIn(report["stop_reason"], ("plan_step_unavailable", "plan_step_budget_exhausted"))


class TaskBindingTests(unittest.TestCase):
    def test_env_task_line_binding_for_pick_and_place(self) -> None:
        binding = parse_task_semantics(
            {"task_family": "pick_and_place_simple", "task_instruction": "ignored"},
            "Your task is to: put a mug in desk.",
        )
        self.assertEqual("mug", binding["object"])
        self.assertEqual("desk", binding["destination"])

    def test_env_task_line_binding_for_cool_with_adjective(self) -> None:
        binding = parse_task_semantics(
            {"task_family": "pick_cool_then_place_in_recep", "task_instruction": "ignored"},
            "Your task is to: put a cool bread in countertop.",
        )
        self.assertEqual("bread", binding["object"])
        self.assertEqual("countertop", binding["destination"])

    def test_env_task_line_binding_for_light(self) -> None:
        binding = parse_task_semantics(
            {"task_family": "look_at_obj_in_light", "task_instruction": "ignored"},
            "Your task is to: examine the alarmclock with the desklamp.",
        )
        self.assertEqual("alarmclock", binding["object"])
        self.assertEqual("desklamp", binding["appliance"])


if __name__ == "__main__":
    unittest.main()
