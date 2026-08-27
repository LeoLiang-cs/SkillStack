from __future__ import annotations

import copy
import unittest

from skillstack.adapters.skillrl_to_grasp import adapt_skillrl_output
from skillstack.experiments.proposal_gate import evaluate_add_candidate


def _proposal(title: str = "Useful Rule"):
    raw = [{
        "skill_id": "dyn_001",
        "title": title,
        "principle": "Use the new rule.",
        "when_to_apply": "When the fixture requests it.",
    }]
    return adapt_skillrl_output(
        raw, task_type="fixture", triggering_evidence_ids=["failure-1"]
    )["proposals"][0]


class ProposalGateFixtureTests(unittest.TestCase):
    def test_positive_no_regression_candidate_is_admitted_on_an_isolated_fork(self) -> None:
        starting_library = {"base-rule": "base"}
        original = copy.deepcopy(starting_library)

        def probe_runner(library):
            has_candidate = "useful_rule" in library
            return {"probe-a": has_candidate, "probe-b": True}

        result = evaluate_add_candidate(
            starting_library, _proposal(), capacity=2, probe_runner=probe_runner
        )
        self.assertEqual("accepted", result["decision"])
        self.assertEqual(1, result["fixes"])
        self.assertEqual(0, result["regressions"])
        self.assertEqual(original, starting_library)
        self.assertNotEqual(result["starting_library_hash"], result["result_library_hash"])

    def test_no_gain_candidate_is_rejected_and_transition_is_retained(self) -> None:
        result = evaluate_add_candidate(
            {"base-rule": "base"},
            _proposal(),
            capacity=2,
            probe_runner=lambda library: {"probe-a": False, "probe-b": True},
        )
        self.assertEqual("rejected", result["decision"])
        self.assertEqual("L.REJECTED_NO_POSITIVE_SAFE_GAIN", result["reason"])
        self.assertEqual(
            {"baseline_success": False, "candidate_success": False},
            result["probe_transitions"]["probe-a"],
        )
        self.assertEqual(result["starting_library_hash"], result["result_library_hash"])

    def test_full_capacity_and_duplicate_are_explicit_without_probe_calls(self) -> None:
        calls = []

        def probe_runner(library):
            calls.append(library)
            return {}

        capacity_result = evaluate_add_candidate(
            {"base-rule": "base"}, _proposal(), capacity=1, probe_runner=probe_runner
        )
        duplicate_result = evaluate_add_candidate(
            {"useful_rule": "existing"}, _proposal(), capacity=2, probe_runner=probe_runner
        )
        self.assertEqual("L.ADD_BLOCKED_CAPACITY", capacity_result["reason"])
        self.assertEqual("L.DUPLICATE_NAME", duplicate_result["reason"])
        self.assertEqual([], calls)

    def test_invalid_adapter_candidate_is_retained_as_gate_rejection(self) -> None:
        invalid = adapt_skillrl_output(
            [{"skill_id": "dyn_001", "title": "Bad", "principle": "Missing trigger"}],
            task_type="fixture",
            triggering_evidence_ids=[],
        )["proposals"][0]
        result = evaluate_add_candidate(
            {}, invalid, capacity=2, probe_runner=lambda library: {}
        )
        self.assertEqual("rejected", result["decision"])
        self.assertEqual("A.SKILLRL_MISSING_WHEN_TO_APPLY", result["reason"])

    def test_probe_population_mismatch_fails(self) -> None:
        calls = 0

        def probe_runner(library):
            nonlocal calls
            calls += 1
            return {"before": True} if calls == 1 else {"after": True}

        with self.assertRaisesRegex(ValueError, "task IDs differ"):
            evaluate_add_candidate({}, _proposal(), capacity=2, probe_runner=probe_runner)


if __name__ == "__main__":
    unittest.main()
