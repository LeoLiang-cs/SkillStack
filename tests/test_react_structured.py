from __future__ import annotations

import unittest
from types import SimpleNamespace

from skillstack.execution.react import (
    ReActExecutor,
    _ground_action_step,
    extract_procedure_steps,
)


class FakeBackend:
    name = "fake_backend"
    model = "fake-model"
    prices = {"input": 0.10, "cached_input": 0.02, "output": 0.40}


class FakeClient:
    def __init__(self, replies):
        self.backend = FakeBackend()
        self.replies = list(replies)
        self.calls = 0

    def chat(self, messages, max_tokens=None, temperature=None):
        content = self.replies[min(self.calls, len(self.replies) - 1)]
        self.calls += 1
        return {
            "content": content,
            "usage": {"prompt_tokens": 10, "completion_tokens": 3, "cached_prompt_tokens": 0},
            "latency_seconds": 0.1,
        }

    def estimate_cost_usd(self, usage):
        return 0.001


class ScriptedEnvironment:
    def __init__(self):
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

    def step(self, actions):
        action = actions[0]
        if action not in self.script:
            raise AssertionError(f"Unexpected action: {action}")
        obs, reward, done, admissible = self.script[action]
        return [obs], [reward], [done], {"admissible_commands": [admissible]}


NATIVE_PAYLOAD_WITH_PROCEDURE = """# Pick and place an object

**Task family:** `pick_and_place_simple`

## Purpose

Move one object to a destination.

## Procedure

1. Read the task to identify the object and destination.
2. Explore the scene until the object is visible.
3. Navigate to the object and take it.
4. Navigate to the destination.
5. Put the object in or on the destination.
"""


class StructuredStepExtractionTests(unittest.TestCase):
    def test_extracts_numbered_procedure_steps(self) -> None:
        steps = extract_procedure_steps(
            {
                "selected_native_skills": [NATIVE_PAYLOAD_WITH_PROCEDURE],
            }
        )
        self.assertEqual(5, len(steps))
        self.assertIn("take", steps[2])

    def test_empty_without_native_payload(self) -> None:
        self.assertEqual([], extract_procedure_steps({"selected_native_skills": []}))

    def test_grounds_action_to_step(self) -> None:
        steps = extract_procedure_steps({"selected_native_skills": [NATIVE_PAYLOAD_WITH_PROCEDURE]})
        self.assertEqual(3, _ground_action_step("take mug 1 from shelf 1", steps))
        self.assertEqual(5, _ground_action_step("move mug 1 to desk 1", steps))
        self.assertIsNone(_ground_action_step("look", steps))


class StructuredReActExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.task_record = {
            "task_id": "t0",
            "task_family": "pick_and_place_simple",
            "task_instruction": "put a mug in desk",
            "game_file": "ignored",
        }
        self.initial_observation = (
            "You are in the middle of a room.\nYour task is to: put a mug in desk."
        )
        self.initial_info = {"admissible_commands": ["go to shelf 1", "go to desk 1", "look"]}
        self.execution_input = {
            "selected_skill_ids": ["skill_pick_and_place"],
            "selected_scores": [1.0],
            "selected_native_skills": [NATIVE_PAYLOAD_WITH_PROCEDURE],
            "flat_skill_context": NATIVE_PAYLOAD_WITH_PROCEDURE,
        }

    def test_structured_mode_injects_numbered_steps(self) -> None:
        replies = [
            "Thought: find the mug.\nAction: go to shelf 1",
            "Thought: take it.\nAction: take mug 1 from shelf 1",
            "Thought: go.\nAction: go to desk 1",
            "Thought: place.\nAction: move mug 1 to desk 1",
        ]
        executor = ReActExecutor(FakeClient(replies), structured_skills=True)
        report = executor.execute(
            ScriptedEnvironment(),
            self.initial_observation,
            self.initial_info,
            self.execution_input,
            task_record=self.task_record,
            max_steps=10,
        )
        self.assertTrue(report["success"])
        self.assertIn("numbered steps; follow them in order", report["system_prompt"])
        self.assertIn("1. Read the task to identify the object and destination.", report["system_prompt"])
        self.assertTrue(report["structured_skills"])
        grounded = [r["grounded_step"] for r in report["action_rationales"]]
        self.assertEqual([2, 3, 2, 5], grounded)

    def test_flat_mode_has_no_steps_block(self) -> None:
        replies = ["Thought: done.\nAction: done"]
        executor = ReActExecutor(FakeClient(replies), structured_skills=False)
        report = executor.execute(
            ScriptedEnvironment(),
            self.initial_observation,
            self.initial_info,
            self.execution_input,
            task_record=self.task_record,
            max_steps=10,
        )
        self.assertNotIn("numbered steps", report["system_prompt"])
        self.assertFalse(report["structured_skills"])
        self.assertEqual([], report["grounded_steps"])


if __name__ == "__main__":
    unittest.main()
