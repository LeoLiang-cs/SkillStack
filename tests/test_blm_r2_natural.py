from __future__ import annotations

import copy
import unittest
from pathlib import Path

from skillstack.execution import ReActExecutor
from skillstack.library import load_static_library
from skillstack.retrieval import DebugLexicalRetriever, TaskSemanticRetriever
from skillstack.runner import EpisodeRunner
from skillstack.experiments.blm_natural import (
    NATURAL_ENVELOPE_SCHEMA,
    materialize_natural_envelope,
    replay_natural_envelope,
)


SCHEMA = "skillstack-blm-intervention-v3"


class FakeBackend:
    name = "fake_backend"
    model = "fake-model"
    prices = {"input": 0.0, "cached_input": 0.0, "output": 0.0}


class FakeClient:
    def __init__(self, replies=None):
        self.backend = FakeBackend()
        self.replies = list(replies or ["Thought: finish.\nAction: done"])
        self.calls = 0

    def chat(self, messages, max_tokens=None, temperature=None):
        reply = self.replies[min(self.calls, len(self.replies) - 1)]
        self.calls += 1
        return {
            "content": reply,
            "usage": {"prompt_tokens": 7, "completion_tokens": 2, "cached_prompt_tokens": 0},
            "latency_seconds": 0.0,
        }

    def estimate_cost_usd(self, usage):
        return 0.0


class NoStepEnvironment:
    def close(self):
        return None

    def step(self, actions):
        return [f"executed {actions[0]}"], [0.0], [True], {"admissible_commands": [[]]}


TASK = {
    "task_id": "r2-test-task",
    "task_family": "pick_and_place_simple",
    "task_instruction": "put a mug in desk",
    "game_file": "deterministic://r2-test",
    "expected_skill_id": "skill_pick_and_place",
}


def environment_factory(_root, _task):
    return (
        NoStepEnvironment(),
        "You are in the middle of a room. Your task is: put a mug in desk.",
        {"admissible_commands": ["look"]},
    )


class R2NaturalBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.native_skills = load_static_library()
        self.task = copy.deepcopy(TASK)

    def _runner(self, retriever, client=None):
        return EpisodeRunner(
            Path("."),
            self.native_skills,
            retriever,
            ReActExecutor(client or FakeClient(), structured_skills=True),
            environment_factory=environment_factory,
        )

    @staticmethod
    def _capture(arm_id):
        return {
            "schema_version": SCHEMA,
            "case_id": "r2-test-case",
            "arm_id": arm_id,
            "operation": "capture",
            "atom_or_group": None,
            "expected_state_sha256": None,
            "donor": None,
        }

    @staticmethod
    def _donor(kind, producer_name, task, state_sha, response):
        return {
            "kind": kind,
            "producer_name": producer_name,
            "task_id": task["task_id"],
            "task_family": task["task_family"],
            "state_sha256": state_sha,
            "retrieval_response": copy.deepcopy(response),
        }

    @staticmethod
    def _projection(trace):
        report = trace.get("executor_report", {})
        boundary = trace.get("blm_boundary", {})
        return {
            "actions": trace.get("actions", []),
            "stop_reason": trace.get("stop_reason"),
            "success": trace.get("success"),
            "system_prompt": report.get("system_prompt"),
            "consumer_reads": boundary.get("consumer_reads"),
            "provider_hash": boundary.get("pre_provider_request_projection_sha256"),
        }

    def test_default_off_and_capture_have_no_sidecar_drift(self):
        baseline = self._runner(DebugLexicalRetriever()).run(self.task, top_k=2, max_steps=1)
        captured = self._runner(DebugLexicalRetriever()).run(
            self.task, top_k=2, max_steps=1, blm_intervention=self._capture("crossed")
        )
        self.assertNotIn("blm_boundary", baseline)
        self.assertEqual(self._projection(baseline)["system_prompt"], self._projection(captured)["system_prompt"])
        self.assertEqual("skillstack-blm-boundary-v3", captured["blm_boundary"]["schema_version"])
        self.assertEqual("post_adapter_pre_consumer_read", captured["blm_boundary"]["intervention_position"])

    def test_v3_read_tracker_records_host_reads(self):
        trace = self._runner(DebugLexicalRetriever()).run(
            self.task, top_k=2, max_steps=1, blm_intervention=self._capture("crossed")
        )
        reads = trace["blm_boundary"]["consumer_reads"]
        self.assertEqual(["flat_skill_context", "selected_native_skills", "selected_native_skills[0]"], [event["path"] for event in reads])
        self.assertEqual(["prompt_exposure", "host_semantic_read", "semantic_read"], [event["read_type"] for event in reads])

    def test_skill_id_read_is_reporting_not_strategy_read(self):
        client = FakeClient(["Thought: inspect.\nAction: look"])
        trace = self._runner(DebugLexicalRetriever(), client).run(
            self.task, top_k=2, max_steps=1, blm_intervention=self._capture("crossed")
        )
        id_events = [
            event for event in trace["blm_boundary"]["consumer_reads"]
            if event["path"] == "selected_skill_ids[0]"
        ]
        self.assertEqual(1, len(id_events))
        self.assertEqual("reporting_read", id_events[0]["read_type"])

    def test_score_negative_control_keeps_first_request_projection(self):
        client = FakeClient()
        crossed = self._runner(DebugLexicalRetriever(), client).run(self.task, top_k=2, max_steps=1, blm_intervention=self._capture("crossed"))
        state_sha = crossed["blm_boundary"]["state_sha256"]
        semantic_response = TaskSemanticRetriever().retrieve(
            self.task,
            environment_factory(None, self.task)[1],
            self.native_skills,
            2,
        )
        request = {
            "schema_version": SCHEMA,
            "case_id": "r2-test-case",
            "arm_id": "score-negative-control",
            "operation": "copy_atom_from_donor",
            "atom_or_group": "selected_scores[0]",
            "expected_state_sha256": state_sha,
            "donor": self._donor("task_semantic_reference", "task_semantic_top_k", self.task, state_sha, semantic_response),
        }
        probe = self._runner(DebugLexicalRetriever()).run(self.task, top_k=2, max_steps=1, blm_intervention=request)
        self.assertTrue(probe["blm_boundary"]["validity"] == "valid")
        self.assertEqual(crossed["blm_boundary"]["pre_provider_request_projection_sha256"], probe["blm_boundary"]["pre_provider_request_projection_sha256"])

    def test_top_group_regenerates_coherent_flat_context(self):
        crossed = self._runner(DebugLexicalRetriever()).run(self.task, top_k=2, max_steps=1, blm_intervention=self._capture("crossed"))
        state_sha = crossed["blm_boundary"]["state_sha256"]
        semantic_response = TaskSemanticRetriever().retrieve(self.task, environment_factory(None, self.task)[1], self.native_skills, 2)
        request = {
            "schema_version": SCHEMA,
            "case_id": "r2-test-case",
            "arm_id": "crossed+top-candidate",
            "operation": "copy_group_from_donor",
            "atom_or_group": "top_candidate_group",
            "expected_state_sha256": state_sha,
            "donor": self._donor("task_semantic_reference", "task_semantic_top_k", self.task, state_sha, semantic_response),
        }
        restored = self._runner(DebugLexicalRetriever()).run(self.task, top_k=2, max_steps=1, blm_intervention=request)
        boundary = restored["blm_boundary"]
        self.assertEqual("valid", boundary["validity"])
        self.assertTrue(boundary["changed"])
        self.assertEqual(restored["selected_skill_ids"][0], semantic_response["ranked_candidates"][0]["skill_id"])
        self.assertIn("### Selected skill 1:", restored["executor_report"]["system_prompt"])

    def test_invalid_donor_stops_before_provider(self):
        client = FakeClient()
        trace = self._runner(DebugLexicalRetriever(), client).run(
            self.task,
            top_k=2,
            max_steps=1,
            blm_intervention={
                **self._capture("crossed"),
                "donor": {"actions": ["done"]},
            },
        )
        self.assertEqual("invalid_input", trace["stop_reason"])
        self.assertEqual(0, client.calls)
        self.assertEqual("forbidden_outcome_content", trace["blm_boundary"]["validity_reason"])

    def test_natural_envelope_round_trip_stops_before_provider(self):
        prompt = (Path(__file__).resolve().parents[1] / "configs" / "p0_react_prompt.txt").read_text(encoding="utf-8")
        envelope = materialize_natural_envelope(
            self.task,
            DebugLexicalRetriever(),
            self.native_skills,
            Path("."),
            prompt,
            case_id="r2-test-case",
            arm_id="crossed",
            environment_factory=environment_factory,
        )
        self.assertEqual(NATURAL_ENVELOPE_SCHEMA, envelope["schema_version"])
        replay = replay_natural_envelope(
            envelope, Path("."), prompt, environment_factory=environment_factory
        )
        self.assertEqual("valid", replay["measurement_status"])
        self.assertFalse(replay["provider_called"])
        tampered = copy.deepcopy(envelope)
        tampered["producer"]["output"]["warnings"] = ["drift"]
        drift = replay_natural_envelope(
            tampered, Path("."), prompt, environment_factory=environment_factory
        )
        self.assertEqual("abstained", drift["measurement_status"])
        self.assertIn("replay_state_incomplete", drift["reason"])


if __name__ == "__main__":
    unittest.main()
