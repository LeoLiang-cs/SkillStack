"""Run the five fixed P0.0 tasks for C0/C1 and persist raw JSONL traces."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skillstack.execution import RecordedActionExecutor
from skillstack.library import load_static_library
from skillstack.retrieval import DebugLexicalRetriever, NoSkillRetriever
from skillstack.runner import EpisodeRunner
from skillstack.tasks import DEFAULT_RECORDED_ACTIONS, DEFAULT_TASK_MANIFEST, load_p0_tasks, load_recorded_actions
from skillstack.tracing import JsonlTraceWriter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--configuration",
        choices=("all", "c0_no_skill", "c1_debug_lexical"),
        default="all",
    )
    parser.add_argument("--top-k", type=int, default=2)
    parser.add_argument("--output-root", type=Path, default=ROOT / "runs")
    return parser.parse_args()


def planned_configurations(selection: str) -> Iterable[Tuple[str, Any]]:
    configurations = (
        ("c0_no_skill", NoSkillRetriever),
        ("c1_debug_lexical", DebugLexicalRetriever),
    )
    if selection == "all":
        return configurations
    return tuple(item for item in configurations if item[0] == selection)


def main() -> int:
    args = parse_args()
    if args.top_k < 1:
        raise ValueError("top-k must be at least 1")
    tasks = load_p0_tasks()
    native_skills = load_static_library()
    all_run_summaries: List[Dict[str, Any]] = []

    for configuration_name, retriever_type in planned_configurations(args.configuration):
        retriever = retriever_type()
        executor = RecordedActionExecutor()
        writer = JsonlTraceWriter(args.output_root, configuration_name)
        manifest = {
            "experiment_id": "p0_0_vertical_slice",
            "run_id": writer.run_id,
            "configuration_name": configuration_name,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "task_manifest": str(DEFAULT_TASK_MANIFEST.relative_to(ROOT)),
            "recorded_action_fixture": str(DEFAULT_RECORDED_ACTIONS.relative_to(ROOT)),
            "task_count": len(tasks),
            "retriever": retriever.name,
            "executor": executor.name,
            "top_k": args.top_k,
            "seed": 42,
            "skill_library": "alfworld_static_v0",
            "native_skill_count": len(native_skills),
            "environment": "alfworld_text_0.4.2",
            "host": {"platform": platform.system(), "architecture": platform.machine()},
            "interpretation": "Interface and trace validation only; recorded actions are not an agent policy.",
        }
        writer.write_manifest(manifest)
        runner = EpisodeRunner(
            data_root=ROOT / "data" / "alfworld",
            native_skills=native_skills,
            retriever=retriever,
            executor=executor,
        )

        episode_summaries = []
        for index, task in enumerate(tasks):
            trace = runner.run(
                task,
                load_recorded_actions(task["task_id"]),
                top_k=args.top_k,
            )
            trace.update(
                {
                    "run_id": writer.run_id,
                    "episode_id": f"{writer.run_id}_episode_{index:02d}",
                    "episode_index": index,
                    "seed": 42,
                    "skill_library_version": "alfworld_static_v0",
                    "environment_version": "alfworld_text_0.4.2",
                }
            )
            writer.append_episode(trace)
            episode_summaries.append(
                {
                    "task_id": trace["task_id"],
                    "task_family": trace["task_family"],
                    "selected_skill_ids": trace.get("selected_skill_ids", []),
                    "action_count": len(trace.get("actions", [])),
                    "success": trace["success"],
                    "stop_reason": trace.get("stop_reason"),
                    "warning_count": len(trace["warnings"]),
                }
            )

        summary = {
            "experiment_id": "p0_0_vertical_slice",
            "run_id": writer.run_id,
            "configuration_name": configuration_name,
            "episode_count": len(episode_summaries),
            "success_count": sum(episode["success"] for episode in episode_summaries),
            "runner_exception_count": sum(
                episode["stop_reason"] == "runner_exception" for episode in episode_summaries
            ),
            "episodes": episode_summaries,
            "interpretation": "Recorded one-step actions validate component interchangeability and trace shape only.",
        }
        writer.write_summary(summary)
        all_run_summaries.append(
            {
                "configuration_name": configuration_name,
                "run_id": writer.run_id,
                "run_directory": str(writer.run_dir.relative_to(ROOT)),
                "episode_count": len(episode_summaries),
                "runner_exception_count": summary["runner_exception_count"],
            }
        )

    print(json.dumps({"runs": all_run_summaries}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

