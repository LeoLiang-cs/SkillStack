"""Run the week-3 ReAct pilot: 5 tasks x 4 skill-input conditions x 1 backend.

The executor slot is swapped from the deterministic SkillPlanExecutor to the
LLM ReActExecutor; everything else (tasks, library, retrievers, adapter,
runner, trace format, seed, budget) stays fixed. Run again with
--backend deepseek_v4_flash for the portability control.
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

from skillstack.execution import ReActExecutor
from skillstack.library import load_static_library
from skillstack.llm import LlmClient, load_backends, load_env_file
from skillstack.retrieval import (
    DebugLexicalRetriever,
    NoSkillRetriever,
    OracleSkillRetriever,
    RandomSkillRetriever,
)
from skillstack.runner import EpisodeRunner
from skillstack.tasks import load_task_manifest
from skillstack.tracing import JsonlTraceWriter

CONDITION_NAMES = ("no_skill", "random_skill", "lexical", "oracle")
DEFAULT_TASK_MANIFEST = ROOT / "configs" / "p0_tasks.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--conditions",
        default="all",
        help="Comma-separated subset of no_skill,random_skill,lexical,oracle, or 'all'.",
    )
    parser.add_argument(
        "--backend",
        default="zhipu_glm_flashx",
        choices=("zhipu_glm_flashx", "deepseek_v4_flash"),
    )
    parser.add_argument(
        "--task-manifest",
        type=Path,
        default=DEFAULT_TASK_MANIFEST,
        help="Task manifest to run (default: configs/p0_tasks.json).",
    )
    parser.add_argument("--experiment-id", default="w3_react_executor_swap")
    parser.add_argument("--run-prefix", default=None, help="Default: w3_<backend>.")
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
    load_env_file()
    backends = load_backends()
    backend = backends[args.backend]
    client = LlmClient(backend)
    task_manifest = args.task_manifest.resolve()
    tasks = load_task_manifest(task_manifest)
    native_skills = load_static_library()
    run_summaries: List[Dict[str, Any]] = []
    run_prefix = args.run_prefix or f"w3_{args.backend}"

    for condition_name, retriever_factory in planned_conditions(args.conditions):
        retriever = retriever_factory(args.seed)
        executor = ReActExecutor(client)
        writer = JsonlTraceWriter(args.output_root, f"{run_prefix}_{condition_name}")
        manifest = {
            "experiment_id": args.experiment_id,
            "run_id": writer.run_id,
            "configuration_name": condition_name,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "task_manifest": str(task_manifest.relative_to(ROOT)),
            "task_count": len(tasks),
            "retriever": retriever.name,
            "executor": executor.name,
            "backend": backend.name,
            "model": backend.model,
            "thinking_disabled": backend.thinking_disabled,
            "top_k": args.top_k,
            "max_steps": args.max_steps,
            "seed": args.seed,
            "skill_library": "alfworld_static_v0",
            "native_skill_count": len(native_skills),
            "environment": "alfworld_text_0.4.2",
            "host": {"platform": platform.system(), "architecture": platform.machine()},
            "interpretation": (
                "Zero-shot LLM ReAct executor with frozen prompt. Task success is "
                "measured; executor is SkillStack's own implementation, not a paper "
                "reproduction."
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
            llm_calls = report.get("llm_calls", [])
            episode_summaries.append(
                {
                    "task_id": trace["task_id"],
                    "task_family": trace["task_family"],
                    "selected_skill_ids": trace.get("selected_skill_ids", []),
                    "action_count": len(trace.get("actions", [])),
                    "llm_call_count": len(llm_calls),
                    "prompt_tokens": sum(call["usage"]["prompt_tokens"] for call in llm_calls),
                    "completion_tokens": sum(call["usage"]["completion_tokens"] for call in llm_calls),
                    "cost_estimate_usd": round(
                        sum(call["cost_estimate_usd"] for call in llm_calls), 6
                    ),
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
            "experiment_id": args.experiment_id,
            "run_id": writer.run_id,
            "configuration_name": condition_name,
            "backend": backend.name,
            "model": backend.model,
            "episode_count": len(episode_summaries),
            "success_count": sum(episode["success"] for episode in episode_summaries),
            "runner_exception_count": sum(
                episode["stop_reason"] == "runner_exception" for episode in episode_summaries
            ),
            "stop_reasons": stop_reasons,
            "total_cost_estimate_usd": round(
                sum(episode["cost_estimate_usd"] for episode in episode_summaries), 6
            ),
            "episodes": episode_summaries,
            "interpretation": (
                "Week-3 ReAct condition run. Compare conditions with raw counts only; "
                "cost figures are estimates from configs/llm_backends.json list prices."
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
                "total_cost_estimate_usd": summary["total_cost_estimate_usd"],
            }
        )

    print(json.dumps({"runs": run_summaries}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
