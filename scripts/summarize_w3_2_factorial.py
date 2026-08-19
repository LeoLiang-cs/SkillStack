"""Bind the five factorial runs and compute the RQ3 interaction measure.

I = Y11 - Y10 - Y01 + Y00, computed on success rate, mean steps, and total
cost. Verdict: synergy (I>0 on success), independent (I~0), redundancy or
interference (I<0 on success).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skillstack.tasks import load_task_manifest

CELL_NAMES = ("b00", "b10", "b01", "b11", "control")
SUCCESS_TOLERANCE = 1e-9


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-manifest", type=Path, default=ROOT / "configs" / "p0_tasks_picktwo9.json")
    parser.add_argument("--b00-run", type=Path, required=True)
    parser.add_argument("--b10-run", type=Path, required=True)
    parser.add_argument("--b01-run", type=Path, required=True)
    parser.add_argument("--b11-run", type=Path, required=True)
    parser.add_argument("--control-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "week3_2" / "w3_2_factorial_summary.json")
    return parser.parse_args()


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def cell_metrics(traces: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    trace_list = list(traces)
    actions = [len(trace.get("actions", [])) for trace in trace_list]
    calls = [len(trace.get("executor_report", {}).get("llm_calls", [])) for trace in trace_list]
    costs = [
        sum(call["cost_estimate_usd"] for call in trace.get("executor_report", {}).get("llm_calls", []))
        for trace in trace_list
    ]
    return {
        "episode_count": len(trace_list),
        "success_count": sum(trace["success"] for trace in trace_list),
        "success_rate": round(sum(trace["success"] for trace in trace_list) / len(trace_list), 4),
        "mean_steps": round(sum(actions) / len(actions), 2) if actions else 0.0,
        "mean_llm_calls": round(sum(calls) / len(calls), 2) if calls else 0.0,
        "total_cost_estimate_usd": round(sum(costs), 6),
    }


def interaction(label: str, y11, y10, y01, y00) -> Dict[str, Any]:
    value = y11 - y10 - y01 + y00
    return {"metric": label, "y11": y11, "y10": y10, "y01": y01, "y00": y00, "i": round(value, 6)}


def main() -> int:
    args = parse_args()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing factorial summary: {output}")

    run_dirs = {
        "b00": args.b00_run.resolve(),
        "b10": args.b10_run.resolve(),
        "b01": args.b01_run.resolve(),
        "b11": args.b11_run.resolve(),
        "control": args.control_run.resolve(),
    }
    runs: Dict[str, Dict[str, Any]] = {}
    for cell, run_dir in run_dirs.items():
        manifest = read_json(run_dir / "run_manifest.json")
        if manifest["configuration_name"] != cell:
            raise ValueError(f"{run_dir} does not identify cell {cell}")
        traces = read_jsonl(run_dir / "episodes.jsonl")
        expected_task_ids = {task["task_id"] for task in load_task_manifest(args.task_manifest)}
        if {trace["task_id"] for trace in traces} != expected_task_ids:
            raise ValueError(f"{cell} task IDs do not match the manifest")
        runs[cell] = {
            "run_id": manifest["run_id"],
            "run_directory": relative_path(run_dir),
            "retriever": manifest["retriever"],
            "structured_skills": manifest["structured_skills"],
            "traces": traces,
        }

    metrics = {cell: cell_metrics(runs[cell]["traces"]) for cell in CELL_NAMES}

    i_success = interaction("success_rate", *[metrics[cell]["success_rate"] for cell in ("b11", "b01", "b10", "b00")])
    i_steps = interaction("mean_steps", *[metrics[cell]["mean_steps"] for cell in ("b11", "b01", "b10", "b00")])
    i_cost = interaction("total_cost_estimate_usd", *[metrics[cell]["total_cost_estimate_usd"] for cell in ("b11", "b01", "b10", "b00")])

    if i_success["i"] > SUCCESS_TOLERANCE:
        verdict = "synergy"
    elif i_success["i"] < -SUCCESS_TOLERANCE:
        verdict = "redundancy_or_interference"
    else:
        verdict = "approximately_independent"

    summary = {
        "experiment_id": "w3_2_factorial",
        "phase": "3c_factorial",
        "pilot_type": "RQ3 retrieval x composition factorial",
        "design": {
            "retrievers": {"R0": "lexical", "R1": "task_semantic"},
            "executors": {"E0": "flat ReAct", "E1": "structured ReAct"},
            "cells": {
                "b00": "R0 x E0",
                "b10": "R1 x E0",
                "b01": "R0 x E1",
                "b11": "R1 x E1",
                "control": "no-skill x E0 (ablation, excluded from I)",
            },
            "task_manifest": str(args.task_manifest.resolve().relative_to(ROOT)),
            "max_steps": 20,
            "seed": 42,
        },
        "raw_runs": {
            cell: {
                "run_id": runs[cell]["run_id"],
                "run_directory": runs[cell]["run_directory"],
                "retriever": runs[cell]["retriever"],
                "structured_skills": runs[cell]["structured_skills"],
            }
            for cell in CELL_NAMES
        },
        "cell_metrics": metrics,
        "interactions": {
            "success_rate": i_success,
            "mean_steps": i_steps,
            "total_cost": i_cost,
        },
        "verdict_on_success": verdict,
        "interpretation": (
            "I = Y11 - Y10 - Y01 + Y00 with A=retriever (R1 vs R0) and B=executor "
            "(E1 vs E0). Positive I on success = synergy; near zero = independent; "
            "negative = redundancy or interference. Success tolerance: ±1e-9."
        ),
        "interpretation_limits": [
            "n=9 pick_two tasks; raw counts only.",
            "Single seed at temperature 0; sampling nondeterminism across providers applies.",
            "Control cell is an ablation reference and is excluded from I.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
