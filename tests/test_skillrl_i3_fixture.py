from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SkillRLI3FixtureTests(unittest.TestCase):
    def test_fixture_preserves_released_input_shape_and_last_five_steps(self) -> None:
        fixture = json.loads(
            (ROOT / "fixtures/week4/skillrl_i3_failure_fixture.json").read_text(encoding="utf-8")
        )
        self.assertEqual("historical_trace_interface_fixture", fixture["fixture_kind"])
        self.assertEqual(1, len(fixture["failed_trajectories"]))
        failure = fixture["failed_trajectories"][0]
        self.assertEqual({"task", "task_type", "trajectory"}, set(failure))
        self.assertEqual(5, len(failure["trajectory"]))
        self.assertTrue(all({"action", "observation"} == set(step) for step in failure["trajectory"]))


if __name__ == "__main__":
    unittest.main()
