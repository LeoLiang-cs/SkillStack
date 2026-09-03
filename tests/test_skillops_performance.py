from __future__ import annotations

import unittest

from skillstack.experiments.skillops_performance import (
    bootstrap_mean_ci,
    merge_accountings,
    parse_csv,
    parse_seeds,
    summarize_run,
)


class SkillOpsPerformanceTests(unittest.TestCase):
    def test_parse_frozen_cells_and_seed(self):
        self.assertEqual(["raw_stress", "maintained_stress"], parse_csv("raw_stress,maintained_stress"))
        self.assertEqual([42], parse_seeds("42"))

    def test_parse_csv_rejects_duplicates(self):
        with self.assertRaises(ValueError):
            parse_csv("raw_stress,raw_stress")

    def test_merge_accounting(self):
        merged = merge_accountings(
            [
                {"call_count": 2, "usage": {"prompt_tokens": 10}, "estimated_cost_usd": 0.1},
                {"call_count": 3, "usage": {"completion_tokens": 4}, "estimated_cost_usd": 0.2},
            ]
        )
        self.assertEqual(5, merged["call_count"])
        self.assertEqual(10, merged["usage"]["prompt_tokens"])
        self.assertEqual(4, merged["usage"]["completion_tokens"])
        self.assertAlmostEqual(0.3, merged["estimated_cost_usd"])

    def test_run_summary_requires_all_48_error_free(self):
        summaries = [
            {"total": 24, "errors": 0, "accounting": {}},
            {"total": 24, "errors": 0, "accounting": {}},
        ]
        result = summarize_run(summaries, [{}] * 24, ["raw", "maintained"], [42])
        self.assertEqual("complete", result["status"])
        self.assertEqual(48, result["declared_episode_count"])

    def test_bootstrap_zero_differences_has_zero_interval(self):
        low, high = bootstrap_mean_ci([0] * 24, iterations=100, seed=1)
        self.assertEqual((0.0, 0.0), (low, high))

    def test_bootstrap_is_deterministic(self):
        first = bootstrap_mean_ci([-1, 0, 1, 1], iterations=200, seed=7)
        second = bootstrap_mean_ci([-1, 0, 1, 1], iterations=200, seed=7)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
