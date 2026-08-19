"""Bind four immutable week-3 ReAct runs (one backend) into a pilot summary.

Refuses to overwrite. Computes the G2 gate from raw traces: C-oracle must
strictly outperform C-no-skill and C-random under the ReAct executor.
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

EXPECTED_CONDITIONS = ("no_skill", "random_skill", "lexical", "oracle")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", required=True, help="Backend name recorded in the runs.")
    parser.add_argument(
        "--task-manifest",
        type=Path,
        default=ROOT / "configs" / "p0_tasks.json",
    )
    parser.add_argument("--no-skill-run", type=Path, required=True)
    parser.add_argument("--random-skill-run", type=Path, required=True)
    parser.add_argument("--lexical-run", type=Path, required=True)
    parser.add_argument("--oracle-run", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, default=None,
        help="Default: reports/week3/w3_pilot_summary_<backend>.json",
    )
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


def run_metrics(traces: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    trace_list = list(traces)
    stop_reasons: Dict[str, int] = {}
    invalid_action_count = 0
    for trace in trace_list:
        reason = trace.get("stop_reason") or "unknown"
        stop_reasons[reason] = stop_reasons.get(reason, 0) + 1
        for call in trace.get("executor_report", {}).get("llm_calls", []):
            if call.get("attempt", 1) > 1:
                invalid_action_count += 1
    return {
        "episode_count": len(trace_list),
        "task_success_count": sum(trace["success"] for trace in trace_list),
        "runner_exception_count": sum(
            trace.get("stop_reason") == "runner_exception" for trace in trace_list
        ),
        "total_environment_actions": sum(len(trace.get("actions", [])) for trace in trace_list),
        "mean_environment_actions": (
            sum(len(trace.get("actions", [])) for trace in trace_list) / len(trace_list)
            if trace_list
            else 0.0
        ),
        "total_llm_calls": sum(
            len(trace.get("executor_report", {}).get("llm_calls", [])) for trace in trace_list
        ),
        "total_prompt_tokens": sum(
            sum(call["usage"]["prompt_tokens"] for call in trace.get("executor_report", {}).get("llm_calls", []))
            for trace in trace_list
        ),
        "total_completion_tokens": sum(
            sum(call["usage"]["completion_tokens"] for call in trace.get("executor_report", {}).get("llm_calls", []))
            for trace in trace_list
        ),
        "total_cost_estimate_usd": round(
            sum(
                sum(call["cost_estimate_usd"] for call in trace.get("executor_report", {}).get("llm_calls", []))
                for trace in trace_list
            ),
            6,
        ),
        "retry_calls_after_invalid_action": invalid_action_count,
        "stop_reasons": stop_reasons,
    }


def main() -> int:
    args = parse_args()
    output = (
        args.output.resolve()
        if args.output
        else (ROOT / "reports" / "week3" / f"w3_pilot_summary_{args.backend}.json").resolve()
    )
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing pilot summary: {output}")

    run_dirs = {
        "no_skill": args.no_skill_run.resolve(),
        "random_skill": args.random_skill_run.resolve(),
        "lexical": args.lexical_run.resolve(),
        "oracle": args.oracle_run.resolve(),
    }
    runs: Dict[str, Dict[str, Any]] = {}
    for condition, run_dir in run_dirs.items():
        manifest = read_json(run_dir / "run_manifest.json")
        if manifest["configuration_name"] != condition:
            raise ValueError(f"{run_dir} does not identify a {condition} run")
        if manifest.get("backend") != args.backend:
            raise ValueError(f"{run_dir} backend {manifest.get('backend')!r} != {args.backend!r}")
        traces = read_jsonl(run_dir / "episodes.jsonl")
        expected_task_ids = {task["task_id"] for task in load_task_manifest(args.task_manifest)}
        if {trace["task_id"] for trace in traces} != expected_task_ids:
            raise ValueError(f"{condition} task IDs do not match the frozen P0.0 manifest")
        runs[condition] = {
            "run_id": manifest["run_id"],
            "run_directory": relative_path(run_dir),
            "episodes": relative_path(run_dir / "episodes.jsonl"),
            "model": manifest.get("model"),
            "traces_by_task": {trace["task_id"]: trace for trace in traces},
        }

    task_records = load_task_manifest(args.task_manifest)
    per_task_cases = []
    for task in task_records:
        case = {
            "task_id": task["task_id"],
            "task_family": task["task_family"],
            "expected_skill_id": task["expected_skill_id"],
        }
        for condition in EXPECTED_CONDITIONS:
            trace = runs[condition]["traces_by_task"][task["task_id"]]
            case[condition] = {
                "selected_skill_ids": trace.get("selected_skill_ids", []),
                "success": trace["success"],
                "stop_reason": trace.get("stop_reason"),
                "action_count": len(trace.get("actions", [])),
                "llm_call_count": len(trace.get("executor_report", {}).get("llm_calls", [])),
            }
        per_task_cases.append(case)

    success_by_condition = {
        condition: sum(case[condition]["success"] for case in per_task_cases)
        for condition in EXPECTED_CONDITIONS
    }
    g2_passes = (
        success_by_condition["oracle"] > success_by_condition["no_skill"]
        and success_by_condition["oracle"] > success_by_condition["random_skill"]
    )

    summary = {
        "experiment_id": "w3_react_executor_swap",
        "phase": "2c_pilot",
        "pilot_type": "LLM ReAct executor swap",
        "backend": args.backend,
        "model": runs["oracle"]["model"],
        "raw_runs": {
            condition: {
                "run_id": runs[condition]["run_id"],
                "run_directory": runs[condition]["run_directory"],
                "episodes": runs[condition]["episodes"],
            }
            for condition in EXPECTED_CONDITIONS
        },
        "design": {
            "task_split": "valid_unseen",
            "fixed_task_count": len(task_records),
            "shared_executor": "ReActExecutor (zero-shot prompt, native thinking disabled)",
            "conditions": {
                "no_skill": "No-skill control; empty skill context injected into the prompt.",
                "random_skill": "Seeded per-task wrong-skill control.",
                "lexical": "Task-instruction-only IDF-weighted lexical Top-2 retrieval.",
                "oracle": "Frozen task-family to expected-skill mapping.",
            },
            "seed": 42,
            "max_steps": 50,
            "top_k": 2,
        },
        "pipeline_metrics": {
            condition: run_metrics(runs[condition]["traces_by_task"][task["task_id"]] for task in task_records)
            for condition in EXPECTED_CONDITIONS
        },
        "per_task_cases": per_task_cases,
        "g2_gate": {
            "description": (
                "C-oracle must strictly outperform C-no-skill and C-random on task "
                "success under the ReAct executor."
            ),
            "success_by_condition": success_by_condition,
            "passes": g2_passes,
        },
        "interpretation_limits": [
            "Zero-shot ReAct is SkillStack's own implementation; no few-shot trajectories.",
            "Five tasks, one per family: raw counts only, no statistical inference.",
            "Cost figures are estimates from list prices in configs/llm_backends.json.",
            "DeepSeek runs are a portability control, not a model-quality bake-off.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
