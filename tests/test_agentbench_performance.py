from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from skillstack.experiments.agentbench_performance import (
    atomic_write_json,
    checkpoint_name,
    execution_budget,
    sanitize_tool_history,
    with_effectiveness_sensitivity,
)
from skillstack.llm import BackendConfig, LlmClient


class AgentBenchPerformanceTests(unittest.TestCase):
    def test_budget_counts_fresh_baseline_for_every_candidate(self) -> None:
        budget = execution_budget(candidate_cap=3, cell_count=2)
        self.assertEqual(26, budget["shared_initial_total_episodes"])
        self.assertEqual(26, budget["fresh_probe_episodes_per_candidate"])
        self.assertEqual(78, budget["maximum_probe_episodes_per_cell"])
        self.assertEqual(182, budget["maximum_total_task_episodes"])

    def test_effectiveness_sensitivity_exposes_zero_fix_native_admission(self) -> None:
        result = with_effectiveness_sensitivity({"decision": "accepted", "fixes": 0})
        self.assertTrue(result["native_admitted"])
        self.assertFalse(result["effectiveness_admitted"])
        self.assertEqual(
            "native_accepts_without_observed_fix", result["sensitivity_disagreement"]
        )

    def test_effectiveness_sensitivity_accepts_real_fix(self) -> None:
        result = with_effectiveness_sensitivity({"decision": "accepted", "fixes": 1})
        self.assertTrue(result["effectiveness_admitted"])

    def test_atomic_checkpoint_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "checkpoint.json"
            atomic_write_json(path, {"status": "ok", "values": {3, 1}})
            loaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual("ok", loaded["status"])
            self.assertEqual({1, 3}, set(loaded["values"]))

    def test_checkpoint_name_is_path_safe(self) -> None:
        self.assertEqual("a-b-c", checkpoint_name("a/b c"))

    def test_llm_client_preserves_native_tool_calls(self) -> None:
        backend = BackendConfig(
            "test",
            {"base_url": "http://unused", "model": "m", "api_key_env": "K"},
            {},
        )
        client = LlmClient(backend, api_key="dummy")
        body = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "act", "arguments": "{\"action\":\"look\"}"},
                    }],
                }
            }],
            "usage": {"prompt_tokens": 8, "completion_tokens": 3},
        }
        with mock.patch.object(client, "_post", return_value=body) as post:
            result = client.chat(
                [{"role": "user", "content": "go"}],
                tools=[{"type": "function", "function": {"name": "act"}}],
            )
        self.assertEqual("call_1", result["message"]["tool_calls"][0]["id"])
        self.assertEqual("act", post.call_args.args[0]["tools"][0]["function"]["name"])

    def test_sanitize_tool_history_drops_only_orphan_tool_message(self) -> None:
        messages = [
            {"role": "tool", "tool_call_id": "truncated", "content": "old"},
            {"role": "assistant", "content": "", "tool_calls": [{"id": "kept"}]},
            {"role": "tool", "tool_call_id": "kept", "content": "observation"},
            {"role": "user", "content": "continue"},
        ]
        sanitized, events = sanitize_tool_history(messages)
        self.assertEqual(["assistant", "tool", "user"], [m["role"] for m in sanitized])
        self.assertEqual("dropped_orphan_tool_message", events[0]["action"])


if __name__ == "__main__":
    unittest.main()
