"""Create a reproducible P0.0 pilot summary from immutable C0/C1 raw traces."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skillstack.tasks import load_p0_tasks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--c0-run", type=Path, required=True, help="C0 run directory")
    parser.add_argument("--c1-run", type=Path, required=True, help="C1 run directory")
    parser.add_argument(
        "--output", type=Path, default=ROOT / "reports" / "week1" / "phase5_pilot_summary.json"
    )
    return parser.parse_args()


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def run_metrics(traces: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    trace_list = list(traces)
    episode_count = len(trace_list)
    return {
        "episode_count": episode_count,
        "task_success_count": sum(trace["success"] for trace in trace_list),
        "runner_exception_count": sum(
            trace.get("stop_reason") == "runner_exception" for trace in trace_list
        ),
        "pipeline_complete_count": sum(
            trace.get("stop_reason") != "runner_exception" for trace in trace_list
        ),
        "total_environment_actions": sum(len(trace.get("actions", [])) for trace in trace_list),
        "mean_environment_actions": (
            sum(len(trace.get("actions", [])) for trace in trace_list) / episode_count
            if episode_count
            else 0.0
        ),
    }


def relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def main() -> int:
    args = parse_args()
    c0_run = args.c0_run.resolve()
    c1_run = args.c1_run.resolve()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing pilot summary: {output}")

    c0_manifest = read_json(c0_run / "run_manifest.json")
    c1_manifest = read_json(c1_run / "run_manifest.json")
    c0_traces = read_jsonl(c0_run / "episodes.jsonl")
    c1_traces = read_jsonl(c1_run / "episodes.jsonl")
    if c0_manifest["configuration_name"] != "c0_no_skill":
        raise ValueError("--c0-run does not identify a c0_no_skill run")
    if c1_manifest["configuration_name"] != "c1_debug_lexical":
        raise ValueError("--c1-run does not identify a c1_debug_lexical run")

    task_records = {task["task_id"]: task for task in load_p0_tasks()}
    expected_task_ids = set(task_records)
    if {trace["task_id"] for trace in c0_traces} != expected_task_ids:
        raise ValueError("C0 task IDs do not match the frozen P0.0 manifest")
    if {trace["task_id"] for trace in c1_traces} != expected_task_ids:
        raise ValueError("C1 task IDs do not match the frozen P0.0 manifest")

    c0_by_task_id = {trace["task_id"]: trace for trace in c0_traces}
    c1_by_task_id = {trace["task_id"]: trace for trace in c1_traces}
    retrieval_cases = []
    for task_id, task in task_records.items():
        c0_trace = c0_by_task_id[task_id]
        c1_trace = c1_by_task_id[task_id]
        selected = c1_trace.get("selected_skill_ids", [])
        expected = task["expected_skill_id"]
        retrieval_cases.append(
            {
                "task_id": task_id,
                "task_family": task["task_family"],
                "expected_skill_id": expected,
                "c0_selected_skill_ids": c0_trace.get("selected_skill_ids", []),
                "c1_selected_skill_ids": selected,
                "top_1_matches_expected": bool(selected) and selected[0] == expected,
                "top_k_contains_expected": expected in selected,
            }
        )

    summary = {
        "experiment_id": "p0_0_vertical_slice",
        "phase": "5_pilot",
        "pilot_type": "interface-validation pilot",
        "raw_runs": {
            "c0_no_skill": {
                "run_id": c0_manifest["run_id"],
                "run_directory": relative_path(c0_run),
                "episodes": relative_path(c0_run / "episodes.jsonl"),
            },
            "c1_debug_lexical": {
                "run_id": c1_manifest["run_id"],
                "run_directory": relative_path(c1_run),
                "episodes": relative_path(c1_run / "episodes.jsonl"),
            },
        },
        "design": {
            "task_split": "valid_unseen",
            "fixed_task_count": len(task_records),
            "c0": "No-skill control; empty native-skill selection.",
            "c1": "Task-instruction-only IDF-weighted lexical Top-2 retrieval.",
            "shared_executor": "RecordedActionExecutor",
            "shared_action_fixture": "One admissible `look` action per task.",
        },
        "pipeline_metrics": {
            "c0_no_skill": run_metrics(c0_traces),
            "c1_debug_lexical": run_metrics(c1_traces),
        },
        "retrieval_metrics_c1": {
            "correctness_reference": "Frozen task-family to static-skill mapping in configs/p0_tasks.json.",
            "top_1_match_count": sum(case["top_1_matches_expected"] for case in retrieval_cases),
            "top_k_contains_expected_count": sum(
                case["top_k_contains_expected"] for case in retrieval_cases
            ),
            "task_count": len(retrieval_cases),
            "cases": retrieval_cases,
        },
        "interpretation_limits": [
            "Task success is not evaluated: both configurations replay only one `look` action.",
            "The lexical retriever is a transparent debug baseline, not embedding Top-k or SkillReranker.",
            "The task-family mapping measures selection agreement only; it does not establish downstream utility.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

