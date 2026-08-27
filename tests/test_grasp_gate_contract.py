from __future__ import annotations

import unittest

from skillstack.experiments.grasp_gate_contract import run_grasp_gate_contract


def _run(reference, baseline, candidate):
    return run_grasp_gate_contract(
        reference,
        baseline_runner=lambda: baseline,
        candidate_runner=lambda: candidate,
    )


class GRASPGateContractTests(unittest.TestCase):
    def test_new_fix_without_regression_is_admitted(self) -> None:
        result = _run(
            {"failed": True, "passing": False},
            {"failed": {"success": False, "status": "completed"},
             "passing": {"success": True, "status": "completed"}},
            {"failed": {"success": True, "status": "completed"},
             "passing": {"success": True, "status": "completed"}},
        )
        self.assertEqual("accepted", result["decision"])
        self.assertEqual(1, result["adjusted_score"])
        self.assertEqual(0, result["regressions"])

    def test_ordinary_regression_exceeds_budget(self) -> None:
        result = _run(
            {"passing": False},
            {"passing": {"success": True, "status": "completed"}},
            {"passing": {"success": False, "status": "completed"}},
        )
        self.assertEqual("no_op", result["decision"])
        self.assertEqual("L.REJECTED_REGRESSION_BUDGET", result["reason"])
        self.assertEqual(-1, result["adjusted_score"])

    def test_invalid_action_regression_receives_double_total_penalty(self) -> None:
        result = _run(
            {"passing": False},
            {"passing": {"success": True, "status": "completed"}},
            {"passing": {"success": False, "status": "agent invalid action"}},
        )
        self.assertEqual(1, result["invalid_action_regressions"])
        self.assertEqual(-2, result["raw_score"])
        self.assertEqual(-2, result["adjusted_score"])

    def test_preexisting_error_is_excluded_with_source_adjustment(self) -> None:
        result = _run(
            {"passing": False},
            {"passing": {"success": False, "status": "error"}},
            {"passing": {"success": False, "status": "error"}},
        )
        self.assertEqual(["passing"], result["baseline_error_ids"])
        self.assertTrue(
            result["probe_transitions"]["passing"]["candidate_error_excluded_as_preexisting"]
        )
        self.assertEqual(1, result["adjusted_score"])
        self.assertEqual("accepted", result["decision"])

    def test_no_change_is_retained_as_noop(self) -> None:
        result = _run(
            {"failed": True, "passing": False},
            {"failed": {"success": False, "status": "completed"},
             "passing": {"success": True, "status": "completed"}},
            {"failed": {"success": False, "status": "completed"},
             "passing": {"success": True, "status": "completed"}},
        )
        self.assertEqual("no_op", result["decision"])
        self.assertEqual(0, result["adjusted_score"])

    def test_probe_population_mismatch_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "task IDs must match"):
            _run(
                {"one": True},
                {"one": {"success": False, "status": "completed"}},
                {"two": {"success": True, "status": "completed"}},
            )


if __name__ == "__main__":
    unittest.main()
