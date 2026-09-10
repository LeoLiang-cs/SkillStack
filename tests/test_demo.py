from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from skillstack.demo import run_demo
from skillstack.environments import DeterministicFixtureEnv
from skillstack.cli import main


ROOT = Path(__file__).resolve().parents[1]


class DeterministicFixtureTests(unittest.TestCase):
    def test_reset_and_valid_step_are_deterministic(self) -> None:
        first = DeterministicFixtureEnv("demo/task", seed=9)
        second = DeterministicFixtureEnv("demo/task", seed=9)
        self.assertEqual(first.reset(), second.reset())
        self.assertEqual(first.step(["look"]), second.step(["look"]))
        first.close()
        second.close()

    def test_invalid_action_is_logged_without_external_side_effects(self) -> None:
        env = DeterministicFixtureEnv("demo/task")
        _observations, infos = env.reset()
        observations, rewards, dones, next_infos = env.step(["open portal"])
        self.assertTrue(observations[0].endswith("state=invalid_action; step=1; seed=42."))
        self.assertEqual([0.0], rewards)
        self.assertEqual([False], dones)
        self.assertEqual(["open portal"], next_infos["invalid_actions"][0])
        self.assertEqual(["open portal"], env.invalid_actions)
        env.close()


class DemoRunTests(unittest.TestCase):
    def test_all_cells_share_pipeline_and_change_only_selection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run_demo(ROOT, Path(directory), run_id_prefix="test")
            comparison = result["comparison"]
            self.assertTrue(comparison["selection_changed"])
            self.assertTrue(comparison["action_sequence_equal"])
            self.assertTrue(comparison["fixture_outcome_equal"])
            self.assertTrue(comparison["adapter_lossless_all"])
            self.assertEqual(0, result["network_calls"])
            self.assertEqual(0, result["model_calls"])
            self.assertEqual(
                (ROOT / "examples" / "demo" / "expected_fingerprint.txt")
                .read_text(encoding="utf-8")
                .strip(),
                result["comparison_fingerprint"],
            )
            self.assertEqual(2, len(result["runs"]))
            for record in result["runs"]:
                summary = record["summary"]
                self.assertEqual(1, summary["episode_count"])
                self.assertEqual(1, summary["completed_count"])
                self.assertEqual(1, summary["fixture_success_count"])
                self.assertFalse(summary["benchmark_success_claim"])
                episode_path = Path(record["run_directory"]) / "episodes.jsonl"
                self.assertEqual(1, len(episode_path.read_text(encoding="utf-8").splitlines()))
                episode = json.loads(episode_path.read_text(encoding="utf-8").splitlines()[0])
                self.assertEqual("zero_model_composability_demo", episode["experiment_id"])
                self.assertEqual("deterministic_fixture", episode["environment_kind"])

    def test_no_skill_and_lexical_selection_is_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run_demo(ROOT, Path(directory), run_id_prefix="selection")
            summaries = {record["configuration_name"]: record["summary"] for record in result["runs"]}
            self.assertEqual([], summaries["c0_no_skill"]["selected_skill_ids"])
            self.assertEqual(
                ["skill_light_inspection", "skill_clean_then_place"],
                summaries["c1_debug_lexical"]["selected_skill_ids"],
            )
            self.assertEqual(1, summaries["c0_no_skill"]["lossless_adapter_event_count"])
            self.assertEqual(1, summaries["c1_debug_lexical"]["lossless_adapter_event_count"])

    def test_existing_run_id_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            run_demo(ROOT, output_root, configuration="c1_debug_lexical", run_id_prefix="immutable")
            with self.assertRaises(FileExistsError):
                run_demo(ROOT, output_root, configuration="c1_debug_lexical", run_id_prefix="immutable")

    def test_cli_runs_one_cell_and_returns_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = main(
                    [
                        "demo",
                        "--root",
                        str(ROOT),
                        "--output-root",
                        directory,
                        "--configuration",
                        "c1_debug_lexical",
                        "--run-id-prefix",
                        "cli",
                    ]
                )
            self.assertEqual(0, exit_code)
            payload = json.loads(output.getvalue())
            self.assertEqual("c1_debug_lexical", payload["configuration"])
            self.assertEqual(1, len(payload["runs"]))

    def test_missing_demo_fixture_fails_before_creating_a_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                run_demo(Path(directory), Path(directory))


if __name__ == "__main__":
    unittest.main()
