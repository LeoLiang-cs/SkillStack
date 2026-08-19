"""Run the week-2 skill-conditioned pilot: 5 tasks x 4 skill-input conditions.

Each condition shares the same SkillPlanExecutor, frozen tasks, static
library, adapter, seed, step budget, and trace format. Only the retriever
slot changes. Raw runs are immutable under `runs/`.
"""

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

from skillstack.execution import SkillPlanExecutor
from skillstack.library import load_static_library
from skillstack.retrieval import (
    DebugLexicalRetriever,
    NoSkillRetriever,
    OracleSkillRetriever,
    RandomSkillRetriever,
)
from skillstack.runner import EpisodeRunner
from skillstack.tasks import DEFAULT_TASK_MANIFEST, load_p0_tasks
from skillstack.tracing import JsonlTraceWriter

CONDITION_NAMES = ("no_skill", "random_skill", "lexical", "oracle")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--conditions",
        default="all",
        help="Comma-separated subset of no_skill,random_skill,lexical,oracle, or 'all'.",
    )
    parser.add_argument("--top-k", type=int, default=2)
    parser.add_argument("--max-steps", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-root", type=Path, default=ROOT / "runs")
    return parser.parse_args()


def planned_conditions(selection: str) -> Iterable[Tuple[str, Any]]:
    factory = {
        "no_skill": lambda seed: NoSkillRetriever(),
        "random_skill": lambda seed: RandomSkillRetriever(seed=seed),
        "lexical": lambda seed: DebugLexicalRetriever(),
        "oracle": lambda seed: OracleSkillRetriever(),
    }
    if selection == "all":
        names = CONDITION_NAMES
    else:
        names = tuple(name.strip() for name in selection.split(",") if name.strip())
    unknown = [name for name in names if name not in factory]
    if unknown:
        raise ValueError(f"Unknown condition names: {', '.join(unknown)}")
    return ((name, factory[name]) for name in names)


def main() -> int:
    args = parse_args()
    if args.top_k < 1:
        raise ValueError("top-k must be at least 1")
    tasks = load_p0_tasks()
    native_skills = load_static_library()
    run_summaries: List[Dict[str, Any]] = []

    for condition_name, retriever_factory in planned_conditions(args.conditions):
        retriever = retriever_factory(args.seed)
        executor = SkillPlanExecutor()
        writer = JsonlTraceWriter(args.output_root, f"w2_{condition_name}")
        manifest = {
            "experiment_id": "w2_skill_conditioned_execution",
            "run_id": writer.run_id,
            "configuration_name": condition_name,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "task_manifest": str(DEFAULT_TASK_MANIFEST.relative_to(ROOT)),
            "task_count": len(tasks),
            "retriever": retriever.name,
            "executor": executor.name,
            "top_k": args.top_k,
            "max_steps": args.max_steps,
            "seed": args.seed,
            "skill_library": "alfworld_static_v0",
            "native_skill_count": len(native_skills),
            "environment": "alfworld_text_0.4.2",
            "host": {"platform": platform.system(), "architecture": platform.machine()},
            "interpretation": (
                "Deterministic skill-plan executor; no LLM. Task success is measured "
                "here, but the executor is a hand-coded SkillStack policy, not a "
                "paper reproduction."
            ),
        }
        writer.write_manifest(manifest)
        runner = EpisodeRunner(
            data_root=ROOT / "data" / "alfworld",
            native_skills=native_skills,
            retriever=retriever,
            executor=executor,
        )

        episode_summaries: List[Dict[str, Any]] = []
        for index, task in enumerate(tasks):
            trace = runner.run(
                task,
                recorded_actions=None,
                top_k=args.top_k,
                max_steps=args.max_steps,
            )
            trace.update(
                {
                    "run_id": writer.run_id,
                    "episode_id": f"{writer.run_id}_episode_{index:02d}",
                    "episode_index": index,
                    "seed": args.seed,
                    "max_steps": args.max_steps,
                    "skill_library_version": "alfworld_static_v0",
                    "environment_version": "alfworld_text_0.4.2",
                }
            )
            writer.append_episode(trace)
            report = trace.get("executor_report", {})
            episode_summaries.append(
                {
                    "task_id": trace["task_id"],
                    "task_family": trace["task_family"],
                    "selected_skill_ids": trace.get("selected_skill_ids", []),
                    "plan_skill_id": report.get("plan_skill_id"),
                    "action_count": len(trace.get("actions", [])),
                    "success": trace["success"],
                    "stop_reason": trace.get("stop_reason"),
                    "warning_count": len(trace["warnings"]),
                }
            )

        stop_reasons: Dict[str, int] = {}
        for episode in episode_summaries:
            reason = episode["stop_reason"] or "unknown"
            stop_reasons[reason] = stop_reasons.get(reason, 0) + 1

        summary = {
            "experiment_id": "w2_skill_conditioned_execution",
            "run_id": writer.run_id,
            "configuration_name": condition_name,
            "episode_count": len(episode_summaries),
            "success_count": sum(episode["success"] for episode in episode_summaries),
            "runner_exception_count": sum(
                episode["stop_reason"] == "runner_exception" for episode in episode_summaries
            ),
            "stop_reasons": stop_reasons,
            "episodes": episode_summaries,
            "interpretation": (
                "First week-2 condition run. Success here is task success under a "
                "deterministic executor; compare conditions with raw counts only."
            ),
        }
        writer.write_summary(summary)
        run_summaries.append(
            {
                "configuration_name": condition_name,
                "run_id": writer.run_id,
                "run_directory": str(writer.run_dir.relative_to(ROOT)),
                "success_count": summary["success_count"],
                "episode_count": len(episode_summaries),
                "stop_reasons": stop_reasons,
            }
        )

    print(json.dumps({"runs": run_summaries}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
