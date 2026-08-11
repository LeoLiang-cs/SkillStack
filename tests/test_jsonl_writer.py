from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from skillstack.tracing import JsonlTraceWriter


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


if __name__ == "__main__":
    unittest.main()

