from __future__ import annotations

import unittest

from skillstack.execution import RecordedActionExecutor


class FakeEnvironment:
    def step(self, actions):
        self.last_actions = actions
        return ["after action"], [1], [True], {"admissible_commands": [["look"]]}


class RecordedActionExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.executor = RecordedActionExecutor()
        self.execution_input = {
            "selected_skill_ids": [],
            "selected_scores": [],
            "selected_native_skills": [],
            "flat_skill_context": "",
        }

    def test_executes_admissible_recorded_action(self) -> None:
        report = self.executor.execute(
            FakeEnvironment(), "initial", {"admissible_commands": ["look"]}, self.execution_input, ["look"]
        )
        self.assertEqual(["look"], report["actions"])
        self.assertTrue(report["success"])
        self.assertEqual("environment_done", report["stop_reason"])

    def test_rejects_non_admissible_recorded_action(self) -> None:
        report = self.executor.execute(
            FakeEnvironment(), "initial", {"admissible_commands": ["look"]}, self.execution_input, ["take apple"]
        )
        self.assertEqual([], report["actions"])
        self.assertFalse(report["success"])
        self.assertEqual("action_not_admissible", report["stop_reason"])


if __name__ == "__main__":
    unittest.main()

