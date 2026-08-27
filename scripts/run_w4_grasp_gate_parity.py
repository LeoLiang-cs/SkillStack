"""Compare SkillStack's deterministic gate contract with released GRASP methods."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skillstack.adapters.proposal_to_grasp import envelope_to_grasp_add
from skillstack.adapters.skillrl_to_grasp import adapt_skillrl_output
from skillstack.experiments.grasp_gate_contract import run_grasp_gate_contract
from skillstack.experiments.grasp_source import run_native_gate_scenario
from skillstack.tracing import JsonlTraceWriter


SCENARIOS = {
    "positive_fix": (
        {"failed": True, "passing": False},
        {"failed": {"success": False, "status": "completed"}, "passing": {"success": True, "status": "completed"}},
        {"failed": {"success": True, "status": "completed"}, "passing": {"success": True, "status": "completed"}},
    ),
    "ordinary_regression": (
        {"passing": False},
        {"passing": {"success": True, "status": "completed"}},
        {"passing": {"success": False, "status": "completed"}},
    ),
    "invalid_action_regression": (
        {"passing": False},
        {"passing": {"success": True, "status": "completed"}},
        {"passing": {"success": False, "status": "agent invalid action"}},
    ),
    "preexisting_error": (
        {"passing": False},
        {"passing": {"success": False, "status": "error"}},
        {"passing": {"success": False, "status": "error"}},
    ),
    "no_change": (
        {"failed": True, "passing": False},
        {"failed": {"success": False, "status": "completed"}, "passing": {"success": True, "status": "completed"}},
        {"failed": {"success": False, "status": "completed"}, "passing": {"success": True, "status": "completed"}},
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grasp-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=ROOT / "runs")
    args = parser.parse_args()
    envelope = adapt_skillrl_output(
        [{"skill_id": "dyn_gate_001", "title": "Gate Parity Fixture",
          "principle": "Use the fixture rule.", "when_to_apply": "During parity checks."}],
        task_type="fixture", triggering_evidence_ids=[], writer_model=None,
    )["proposals"][0]
    native_proposal = envelope_to_grasp_add(envelope)
    writer = JsonlTraceWriter(args.output_root, "w4_grasp_gate_parity")
    writer.write_manifest({
        "experiment_id": "w4_grasp_gate_parity",
        "run_id": writer.run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scenario_names": list(SCENARIOS),
        "model_calls": 0,
        "alfworld_episode_calls": 0,
    })
    all_match = True
    comparisons = []
    compared_fields = (
        "baseline_fixes", "baseline_regressions", "baseline_error_ids", "fixes",
        "regressions", "invalid_action_regressions",
        "invalid_action_regression_penalty", "raw_score", "adjusted_score", "decision",
    )
    for index, (name, (reference, baseline, candidate)) in enumerate(SCENARIOS.items()):
        local = run_grasp_gate_contract(
            reference, baseline_runner=lambda value=baseline: value,
            candidate_runner=lambda value=candidate: value,
        )
        native = run_native_gate_scenario(
            args.grasp_root, native_proposal, reference, baseline, candidate
        )
        mismatches = {
            field: {"skillstack": local[field], "grasp": native[field]}
            for field in compared_fields if local[field] != native[field]
        }
        matches = not mismatches
        all_match = all_match and matches
        trace = {
            "run_id": writer.run_id,
            "episode_id": f"{writer.run_id}_parity_{index:02d}",
            "task_id": f"gate_scenario:{name}",
            "retriever_name": "not_applicable_local",
            "executor_name": "grasp_native_gate_parity",
            "probe_reference": reference,
            "baseline_results": baseline,
            "candidate_results": candidate,
            "skillstack_contract": local,
            "native_grasp": native,
            "mismatches": mismatches,
            "success": matches,
            "stop_reason": "parity_match" if matches else "parity_mismatch",
            "warnings": [],
        }
        writer.append_episode(trace)
        comparisons.append({"scenario": name, "matches": matches, "mismatches": mismatches})
    writer.write_summary({
        "experiment_id": "w4_grasp_gate_parity",
        "run_id": writer.run_id,
        "scenario_count": len(comparisons),
        "parity_match_count": sum(item["matches"] for item in comparisons),
        "all_match": all_match,
        "comparisons": comparisons,
        "model_calls": 0,
        "alfworld_episode_calls": 0,
    })
    print(json.dumps({"run_id": writer.run_id, "run_directory": str(writer.run_dir),
                      "all_match": all_match, "comparisons": comparisons}, indent=2))
    return 0 if all_match else 1


if __name__ == "__main__":
    raise SystemExit(main())
