from __future__ import annotations

import unittest
from types import SimpleNamespace

from skillstack.execution.react import ReActExecutor, parse_reasoning_action


class FakeBackend:
    name = "fake_backend"
    model = "fake-model"
    prices = {"input": 0.10, "cached_input": 0.02, "output": 0.40}


class FakeClient:
    """Scripted client: one reply per chat() call, in order."""

    def __init__(self, replies):
        self.backend = FakeBackend()
        self.replies = list(replies)
        self.calls = 0

    def chat(self, messages, max_tokens=None, temperature=None):
        content = self.replies[min(self.calls, len(self.replies) - 1)]
        self.calls += 1
        return {
            "content": content,
            "usage": {"prompt_tokens": 20, "completion_tokens": 5, "cached_prompt_tokens": 2},
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


class ParseReasoningActionTests(unittest.TestCase):
    def test_extracts_last_thought_and_action(self):
        content = "Thought: first idea\nAction: look\nThought: better idea\nAction: go to desk 1"
        self.assertEqual(("better idea", "go to desk 1"), parse_reasoning_action(content))

    def test_missing_action_returns_none(self):
        self.assertEqual((None, None), parse_reasoning_action("Just some text."))

    def test_done_action(self):
        self.assertEqual(("finished", "done"), parse_reasoning_action("Thought: finished\nAction: done"))


class ReActExecutorTests(unittest.TestCase):
    def setUp(self):
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
            "selected_native_skills": ["# Pick and place"],
            "flat_skill_context": "# Pick and place an object",
        }

    def test_executes_valid_actions_to_success(self):
        replies = [
            "Thought: find the mug.\nAction: go to shelf 1",
            "Thought: take it.\nAction: take mug 1 from shelf 1",
            "Thought: go to the desk.\nAction: go to desk 1",
            "Thought: place it.\nAction: move mug 1 to desk 1",
        ]
        executor = ReActExecutor(FakeClient(replies))
        report = executor.execute(
            ScriptedEnvironment(),
            self.initial_observation,
            self.initial_info,
            self.execution_input,
            task_record=self.task_record,
            max_steps=10,
        )
        self.assertTrue(report["success"])
        self.assertEqual("environment_done", report["stop_reason"])
        self.assertEqual(
            ["go to shelf 1", "take mug 1 from shelf 1", "go to desk 1", "move mug 1 to desk 1"],
            report["actions"],
        )
        self.assertEqual(4, len(report["action_rationales"]))
        self.assertEqual(4, len(report["llm_calls"]))
        self.assertEqual(0.004, report["total_cost_estimate_usd"])

    def test_invalid_action_retries_once_then_executes(self):
        replies = [
            "Thought: try something.\nAction: fly away",
            "Thought: be careful.\nAction: go to shelf 1",
            "Thought: take it.\nAction: take mug 1 from shelf 1",
            "Thought: go.\nAction: go to desk 1",
            "Thought: place.\nAction: move mug 1 to desk 1",
        ]
        executor = ReActExecutor(FakeClient(replies))
        report = executor.execute(
            ScriptedEnvironment(),
            self.initial_observation,
            self.initial_info,
            self.execution_input,
            task_record=self.task_record,
            max_steps=10,
        )
        self.assertTrue(report["success"])
        self.assertEqual([1, 2, 1, 1, 1], [call["attempt"] for call in report["llm_calls"]])
        self.assertTrue(any("Invalid action" in warning for warning in report["warnings"]))

    def test_two_invalid_replies_stop_without_env_step(self):
        replies = [
            "Thought: nonsense.\nAction: fly away",
            "Thought: nonsense.\nAction: teleport",
        ]
        executor = ReActExecutor(FakeClient(replies))
        report = executor.execute(
            ScriptedEnvironment(),
            self.initial_observation,
            self.initial_info,
            self.execution_input,
            task_record=self.task_record,
            max_steps=10,
        )
        self.assertEqual("invalid_action_retries_exhausted", report["stop_reason"])
        self.assertEqual([], report["actions"])
        self.assertFalse(report["success"])

    def test_agent_declared_done_stops(self):
        replies = ["Thought: it is done.\nAction: done"]
        executor = ReActExecutor(FakeClient(replies))
        report = executor.execute(
            ScriptedEnvironment(),
            self.initial_observation,
            self.initial_info,
            self.execution_input,
            task_record=self.task_record,
            max_steps=10,
        )
        self.assertEqual("agent_declared_done", report["stop_reason"])
        self.assertFalse(report["success"])

    def test_skill_context_injected_into_system_prompt(self):
        replies = ["Thought: done.\nAction: done"]
        executor = ReActExecutor(FakeClient(replies))
        report = executor.execute(
            ScriptedEnvironment(),
            self.initial_observation,
            self.initial_info,
            self.execution_input,
            task_record=self.task_record,
            max_steps=10,
        )
        self.assertIn("# Pick and place an object", report["system_prompt"])
        self.assertIn("put a mug in desk", report["system_prompt"])


if __name__ == "__main__":
    unittest.main()
