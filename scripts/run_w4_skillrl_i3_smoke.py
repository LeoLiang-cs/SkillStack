"""Run or explicitly retain a blocked released-SkillRL I3 source smoke."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skillstack.adapters.skillrl_to_grasp import adapt_skillrl_output
from skillstack.experiments.skillrl_source import run_released_skillrl_once
from skillstack.tracing import JsonlTraceWriter


DEFAULT_FIXTURE = ROOT / "fixtures/week4/skillrl_i3_failure_fixture.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skillrl-root", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--output-root", type=Path, default=ROOT / "runs")
    args = parser.parse_args()
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    result = run_released_skillrl_once(
        args.skillrl_root,
        fixture["failed_trajectories"],
        fixture["current_skills"],
    )
    adapter_batch = None
    if result["call_executed"] and isinstance(result["native_return"], list):
        adapter_batch = adapt_skillrl_output(
            result["native_return"],
            task_type=fixture["failed_trajectories"][0]["task_type"],
            triggering_evidence_ids=[fixture["source_task_id"]],
            writer_model="o3",
        )

    writer = JsonlTraceWriter(args.output_root, "w4_skillrl_i3_source_smoke")
    writer.write_manifest({
        "experiment_id": "w4_skillrl_i3_source_smoke",
        "run_id": writer.run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "fixture_path": str(args.fixture.resolve()),
        "fixture": fixture,
        "source_commit": result["prepared_request"]["source_commit"],
        "source_sha256": result["prepared_request"]["source_sha256"],
        "credential_status": result["credential_status"],
        "claim_boundary": "One released updater compatibility smoke; no performance claim.",
    })
    completed = result["status"] == "completed"
    blocked = result["status"] == "blocked_credentials"
    trace = {
        "run_id": writer.run_id,
        "episode_id": f"{writer.run_id}_i3_00",
        "task_id": fixture["source_task_id"],
        "retriever_name": "not_applicable_local",
        "executor_name": "skillrl_released_updater",
        "fixture_id": fixture["fixture_id"],
        "source_result": result,
        "adapter_batch": adapter_batch,
        "success": completed,
        "stop_reason": result["status"],
        "warnings": (["Required Azure credentials are unavailable; no API call was made."] if blocked else []),
    }
    writer.append_episode(trace)
    writer.write_summary({
        "experiment_id": "w4_skillrl_i3_source_smoke",
        "run_id": writer.run_id,
        "i3_status": result["status"],
        "call_executed": result["call_executed"],
        "native_candidate_count": (
            len(result["native_return"]) if isinstance(result["native_return"], list) else None
        ),
        "adapter_status": adapter_batch["parse_status"] if adapter_batch else "not_run",
        "model_call_count": int(result["call_executed"]),
        "alfworld_episode_calls": 0,
    })
    print(json.dumps({
        "run_id": writer.run_id,
        "run_directory": str(writer.run_dir),
        "i3_status": result["status"],
        "call_executed": result["call_executed"],
        "adapter_status": adapter_batch["parse_status"] if adapter_batch else "not_run",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
