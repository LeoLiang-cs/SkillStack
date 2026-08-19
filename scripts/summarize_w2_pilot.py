"""Bind the four immutable week-2 runs into a reproducible pilot summary.

Refuses to overwrite a prior summary. Computes the H1 gate from raw traces:
C-oracle must strictly outperform C-no-skill and C-random on task success.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skillstack.tasks import load_p0_tasks

EXPECTED_CONDITIONS = ("no_skill", "random_skill", "lexical", "oracle")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-skill-run", type=Path, required=True)
    parser.add_argument("--random-skill-run", type=Path, required=True)
    parser.add_argument("--lexical-run", type=Path, required=True)
    parser.add_argument("--oracle-run", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "reports" / "week2" / "w2_pilot_summary.json"
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
    for trace in trace_list:
        reason = trace.get("stop_reason") or "unknown"
        stop_reasons[reason] = stop_reasons.get(reason, 0) + 1
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
        "stop_reasons": stop_reasons,
    }


def main() -> int:
    args = parse_args()
    output = args.output.resolve()
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
        traces = read_jsonl(run_dir / "episodes.jsonl")
        expected_task_ids = {task["task_id"] for task in load_p0_tasks()}
        if {trace["task_id"] for trace in traces} != expected_task_ids:
            raise ValueError(f"{condition} task IDs do not match the frozen P0.0 manifest")
        runs[condition] = {
            "run_id": manifest["run_id"],
            "run_directory": relative_path(run_dir),
            "episodes": relative_path(run_dir / "episodes.jsonl"),
            "traces_by_task": {trace["task_id"]: trace for trace in traces},
        }

    task_records = load_p0_tasks()
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
                "plan_skill_id": trace.get("executor_report", {}).get("plan_skill_id"),
                "success": trace["success"],
                "stop_reason": trace.get("stop_reason"),
                "action_count": len(trace.get("actions", [])),
            }
        per_task_cases.append(case)

    success_by_condition = {
        condition: sum(
            case[condition]["success"] for case in per_task_cases
        )
        for condition in EXPECTED_CONDITIONS
    }
    h1_passes = (
        success_by_condition["oracle"] > success_by_condition["no_skill"]
        and success_by_condition["oracle"] > success_by_condition["random_skill"]
    )

    summary = {
        "experiment_id": "w2_skill_conditioned_execution",
        "phase": "2a_pilot",
        "pilot_type": "skill-conditioned execution pilot",
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
            "shared_executor": "SkillPlanExecutor (deterministic, hand-coded, no LLM)",
            "conditions": {
                "no_skill": "No-skill control; generic explore-take-place plan, no transformations.",
                "random_skill": "Seeded per-task wrong-skill control.",
                "lexical": "Task-instruction-only IDF-weighted lexical Top-2 retrieval.",
                "oracle": "Frozen task-family to expected-skill mapping.",
            },
            "seed": 42,
            "max_steps": 50,
            "top_k": 2,
        },
        "pipeline_metrics": {
            condition: run_metrics(
                runs[condition]["traces_by_task"][task["task_id"]] for task in task_records
            )
            for condition in EXPECTED_CONDITIONS
        },
        "per_task_cases": per_task_cases,
        "h1_gate": {
            "description": (
                "C-oracle must strictly outperform C-no-skill and C-random on task success."
            ),
            "success_by_condition": success_by_condition,
            "passes": h1_passes,
        },
        "interpretation_limits": [
            "The executor is a hand-coded deterministic policy, not an LLM agent or a paper reproduction.",
            "Five tasks, one per family: report raw counts only, no statistical inference.",
            "Random-condition success is expected to be nonzero when a wrong draw coincides with a task the skill can satisfy.",
            "Task success is the environment goal check; process-level questions (did the agent follow the right procedure for the right reason) need the action_rationales trace.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
