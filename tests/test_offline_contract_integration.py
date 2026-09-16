from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from skillstack.demo import run_demo
from skillstack.tracing import JsonlTraceWriter


ROOT = Path(__file__).resolve().parents[1]


class OfflineContractIntegrationTests(unittest.TestCase):
    """Exercise the maintained zero-model fixture through the public trace contract."""

    def test_demo_summary_recomputes_from_raw_trace_after_resume(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            result = run_demo(ROOT, output_root, run_id_prefix="contract")
            for record in result["runs"]:
                run_dir = Path(record["run_directory"])
                manifest = json.loads(
                    (run_dir / "run_manifest.json").read_text(encoding="utf-8")
                )
                summary = json.loads(
                    (run_dir / "summary.json").read_text(encoding="utf-8")
                )
                trace = json.loads(
                    (run_dir / "episodes.jsonl").read_text(encoding="utf-8")
                )
                writer = JsonlTraceWriter.resume(
                    output_root / "demo", run_dir.name, expected_manifest=manifest
                )
                self.assertEqual(summary["status_counts"], writer.recompute_status_counts())
                self.assertEqual("skillstack-run-manifest-v1", manifest["schema_version"])
                self.assertEqual("skillstack-episode-trace-v1", trace["schema_version"])
                self.assertEqual("skillstack-run-summary-v1", summary["schema_version"])
                for field in (
                    "raw_observations",
                    "selected_native_payloads",
                    "adapter_events",
                    "actions",
                    "warnings",
                    "executor_report",
                    "task_source",
                ):
                    self.assertIn(field, trace)
                self.assertEqual(0, trace["model_calls"])
                self.assertEqual(0, trace["network_calls"])


if __name__ == "__main__":
    unittest.main()
