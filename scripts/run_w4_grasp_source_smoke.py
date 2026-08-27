"""Run the model-free Week-4 source smoke against a pinned GRASP checkout."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skillstack.adapters.proposal_to_grasp import envelope_to_grasp_add
from skillstack.adapters.skillrl_to_grasp import adapt_skillrl_output
from skillstack.experiments.grasp_source import (
    EXPECTED_GRASP_COMMIT,
    load_grasp_alfworld_manifest,
    run_native_repository_smoke,
)
from skillstack.tracing import JsonlTraceWriter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grasp-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=ROOT / "runs")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_manifest = load_grasp_alfworld_manifest(args.grasp_root)
    skillrl_fixture = [{
        "skill_id": "dyn_source_smoke_001",
        "title": "Systematic Container Search",
        "principle": "Open plausible closed containers before leaving the current room.",
        "when_to_apply": "When the target object is not visible in the current room.",
    }]
    envelope = adapt_skillrl_output(
        skillrl_fixture,
        task_type="pick_and_place",
        triggering_evidence_ids=[source_manifest["strict_dev_split"]["proposal_task_ids"][0]],
        writer_model=None,
        decoding=None,
        call_usage=None,
    )["proposals"][0]
    native_proposal = envelope_to_grasp_add(envelope)

    writer = JsonlTraceWriter(args.output_root, "w4_grasp_repository_source_smoke")
    writer.write_manifest({
        "experiment_id": "w4_grasp_repository_source_smoke",
        "run_id": writer.run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": "Model-free source integration only; no task-performance claim.",
        "grasp_expected_commit": EXPECTED_GRASP_COMMIT,
        "source_manifest": source_manifest,
        "handcrafted_native_input": skillrl_fixture,
        "host": {"platform": platform.system(), "architecture": platform.machine()},
        "model_calls": 0,
        "alfworld_episode_calls": 0,
    })

    try:
        smoke = run_native_repository_smoke(args.grasp_root, native_proposal)
        success = bool(smoke["boundary_success"])
        warning = []
        stop_reason = "source_boundary_complete" if success else "source_boundary_failed"
    except Exception as error:
        smoke = {"exception_type": type(error).__name__, "exception_message": str(error)}
        success = False
        warning = [f"{type(error).__name__}: {error}"]
        stop_reason = "source_boundary_exception"

    trace = {
        "run_id": writer.run_id,
        "episode_id": f"{writer.run_id}_source_boundary_00",
        "task_id": "grasp_repository_source_boundary",
        "retriever_name": "not_applicable_local",
        "executor_name": "grasp_native_repository",
        "proposal_envelope": envelope,
        "native_proposal": native_proposal,
        "source_smoke": smoke,
        "success": success,
        "stop_reason": stop_reason,
        "warnings": warning,
    }
    writer.append_episode(trace)
    writer.write_summary({
        "experiment_id": "w4_grasp_repository_source_smoke",
        "run_id": writer.run_id,
        "boundary_success": success,
        "model_calls": 0,
        "alfworld_episode_calls": 0,
        "stop_reason": stop_reason,
        "interpretation": "Checks source data and native repository compatibility only.",
    })
    print(json.dumps({
        "run_id": writer.run_id,
        "run_directory": str(writer.run_dir),
        "boundary_success": success,
        "history_probe_task_ids": source_manifest["strict_dev_split"]["history_probe_task_ids"],
        "proposal_task_ids": source_manifest["strict_dev_split"]["proposal_task_ids"],
        "stop_reason": stop_reason,
    }, indent=2, ensure_ascii=False))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
