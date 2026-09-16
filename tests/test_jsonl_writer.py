from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from skillstack.tracing import JsonlTraceWriter, status_counts


class JsonlTraceWriterTests(unittest.TestCase):
    def test_writes_immutable_manifest_and_append_only_episode_trace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = JsonlTraceWriter(Path(directory), "unit", run_id="fixed-run")
            writer.write_manifest({"run_id": "fixed-run"})
            writer.append_episode(
                {
                    "run_id": "fixed-run",
                    "episode_id": "episode-0",
                    "task_id": "task-0",
                    "retriever_name": "no_skill",
                    "executor_name": "recorded_action_executor",
                }
            )
            writer.write_summary({"run_id": "fixed-run", "episode_count": 1})

            lines = writer.episodes_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(1, len(lines))
            self.assertEqual("episode-0", json.loads(lines[0])["episode_id"])
            self.assertTrue((writer.run_dir / "run_manifest.json").exists())
            self.assertTrue((writer.run_dir / "summary.json").exists())
            summary = json.loads((writer.run_dir / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(
                writer.manifest["run_identity_sha256"], summary["run_identity_sha256"]
            )
            self.assertTrue(summary["generated_at_utc"])
            self.assertFalse(list(writer.run_dir.glob("*.tmp")))

    def test_manifest_identity_and_resume_reject_drift_or_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            writer = JsonlTraceWriter(output_root, "unit", run_id="fixed-run")
            writer.write_manifest({"run_id": "fixed-run", "config": {"top_k": 2}})
            manifest = json.loads(
                (writer.run_dir / "run_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual("skillstack-run-manifest-v1", manifest["schema_version"])
            self.assertTrue(manifest["run_identity_sha256"])
            self.assertEqual("unavailable", manifest["repo_dirty"])
            self.assertEqual("unavailable", manifest["external_checkout_commit"])
            episode = {
                "run_id": "fixed-run",
                "episode_id": "episode-0",
                "task_id": "task-0",
                "retriever_name": "no_skill",
                "executor_name": "recorded_action_executor",
                "success": True,
                "stop_reason": "environment_done",
                "benchmark_success_claim": True,
            }
            writer.append_episode(episode)
            self.assertEqual(1, writer.recompute_status_counts()["success"])
            resumed = JsonlTraceWriter.resume(
                output_root,
                "fixed-run",
                {"run_id": "fixed-run", "config": {"top_k": 2}},
            )
            self.assertEqual(manifest["run_identity_sha256"], resumed.manifest["run_identity_sha256"])
            self.assertEqual(1, resumed.recompute_status_counts()["completed"])
            with self.assertRaises(ValueError):
                resumed.append_episode(episode)
            with self.assertRaises(ValueError):
                JsonlTraceWriter.resume(
                    output_root,
                    "fixed-run",
                    {"run_id": "fixed-run", "config": {"top_k": 3}},
                )

    def test_run_id_cannot_escape_output_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            with self.assertRaises(ValueError):
                JsonlTraceWriter(output_root, "unit", run_id="../escape")
            with self.assertRaises(ValueError):
                JsonlTraceWriter(output_root, "unit", run_id=str(output_root / "escape"))

    def test_status_counts_separate_error_from_task_failure(self) -> None:
        failed_task = status_counts({"success": False, "stop_reason": "action_not_admissible"})
        self.assertEqual(1, failed_task["completed"])
        self.assertEqual(1, failed_task["task_failure"])
        error = status_counts({"success": False, "stop_reason": "runner_exception"})
        self.assertEqual(1, error["error"])
        self.assertEqual(0, error["task_failure"])
        timeout = status_counts({"success": False, "stop_reason": "timeout"})
        self.assertEqual(1, timeout["timeout"])
        abstained = status_counts(
            {
                "success": False,
                "stop_reason": "abstained",
                "benchmark_success_claim": True,
            }
        )
        self.assertEqual(1, abstained["abstained"])
        self.assertEqual(0, abstained["task_failure"])

    def test_unknown_task_success_is_not_counted_as_failure(self) -> None:
        counts = status_counts(
            {
                "stop_reason": "environment_done",
                "benchmark_success_claim": True,
            }
        )
        self.assertEqual(1, counts["completed"])
        self.assertEqual(1, counts["valid"])
        self.assertEqual(0, counts["success"])
        self.assertEqual(0, counts["task_failure"])

    def test_rejects_unknown_trace_or_summary_schema(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = JsonlTraceWriter(Path(directory), "unit", run_id="fixed-run")
            with self.assertRaises(ValueError):
                writer.write_manifest(
                    {"run_id": "fixed-run", "schema_version": "future-manifest"}
                )
            with self.assertRaises(ValueError):
                writer.append_episode(
                    {
                        "schema_version": "future-trace",
                        "run_id": "fixed-run",
                        "episode_id": "episode-0",
                        "task_id": "task-0",
                        "retriever_name": "no_skill",
                        "executor_name": "recorded_action_executor",
                    }
                )
            with self.assertRaises(ValueError):
                writer.write_summary(
                    {"run_id": "fixed-run", "schema_version": "future-summary"}
                )

    def test_refuses_mismatched_run_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = JsonlTraceWriter(Path(directory), "unit", run_id="fixed-run")
            with self.assertRaises(ValueError):
                writer.append_episode(
                    {
                        "run_id": "other-run",
                        "episode_id": "episode-0",
                        "task_id": "task-0",
                        "retriever_name": "no_skill",
                        "executor_name": "recorded_action_executor",
                    }
                )

    def test_cancelled_episode_is_retained_and_malformed_tail_is_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            writer = JsonlTraceWriter(output_root, "unit", run_id="cancel-run")
            writer.write_manifest({"run_id": "cancel-run", "config": {"budget": 1}})
            writer.append_episode(
                {
                    "run_id": "cancel-run",
                    "episode_id": "episode-0",
                    "task_id": "task-0",
                    "retriever_name": "no_skill",
                    "executor_name": "recorded_action_executor",
                    "stop_reason": "cancelled",
                }
            )
            self.assertEqual(1, writer.recompute_status_counts()["cancelled"])
            with writer.episodes_path.open("a", encoding="utf-8") as handle:
                handle.write('{"episode_id":')
            with self.assertRaises(ValueError):
                writer.recompute_status_counts()
            with self.assertRaises(ValueError):
                writer.append_episode(
                    {
                        "run_id": "cancel-run",
                        "episode_id": "episode-1",
                        "task_id": "task-1",
                        "retriever_name": "no_skill",
                        "executor_name": "recorded_action_executor",
                    }
                )

    def test_resume_allows_missing_summary_then_freezes_append(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            writer = JsonlTraceWriter(output_root, "unit", run_id="summary-run")
            manifest = {"run_id": "summary-run", "config": {"top_k": 1}}
            writer.write_manifest(manifest)
            writer.append_episode(
                {
                    "run_id": "summary-run",
                    "episode_id": "episode-0",
                    "task_id": "task-0",
                    "retriever_name": "no_skill",
                    "executor_name": "recorded_action_executor",
                }
            )
            resumed = JsonlTraceWriter.resume(output_root, "summary-run", manifest)
            self.assertFalse((resumed.run_dir / "summary.json").exists())
            resumed.write_summary({"run_id": "summary-run"})
            with self.assertRaises(ValueError):
                resumed.append_episode(
                    {
                        "run_id": "summary-run",
                        "episode_id": "episode-1",
                        "task_id": "task-1",
                        "retriever_name": "no_skill",
                        "executor_name": "recorded_action_executor",
                    }
                )

    def test_summary_rejects_identity_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = JsonlTraceWriter(Path(directory), "unit", run_id="identity-run")
            writer.write_manifest({"run_id": "identity-run", "config": {"seed": 1}})
            with self.assertRaises(ValueError):
                writer.write_summary(
                    {
                        "run_id": "identity-run",
                        "run_identity_sha256": "different",
                    }
                )


if __name__ == "__main__":
    unittest.main()
