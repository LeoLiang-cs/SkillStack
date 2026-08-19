"""Run the Phase-3 2x2 factorial: R0/R1 retrievers x E0/E1 executors.

Cells (framework B00-B11) plus a no-skill ablation control:

|          | E0 flat ReAct | E1 structured |
|----------|---------------|---------------|
| R0 lexic | B00           | B01           |
| R1 seman | B10           | B11           |

All cells share: pick-two-9 manifest, deepseek backend, 20-step budget,
seed 42, temperature 0, frozen prompt. Each cell gets an immutable run.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skillstack.execution import ReActExecutor
from skillstack.library import load_static_library
from skillstack.llm import LlmClient, load_backends, load_env_file
from skillstack.retrieval import DebugLexicalRetriever, NoSkillRetriever, TaskSemanticRetriever
from skillstack.runner import EpisodeRunner
from skillstack.tasks import load_task_manifest
from skillstack.tracing import JsonlTraceWriter

CELLS = {
    "b00": {"retriever": "lexical", "structured": False},
    "b10": {"retriever": "task_semantic", "structured": False},
    "b01": {"retriever": "lexical", "structured": True},
    "b11": {"retriever": "task_semantic", "structured": True},
    "control": {"retriever": "no_skill", "structured": False},
}
RETRIEVERS = {
    "lexical": DebugLexicalRetriever,
    "task_semantic": TaskSemanticRetriever,
    "no_skill": NoSkillRetriever,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cells",
        default="all",
        help="Comma-separated subset of b00,b10,b01,b11,control, or 'all'.",
    )
    parser.add_argument("--backend", default="deepseek_v4_flash")
    parser.add_argument("--task-manifest", type=Path, default=ROOT / "configs" / "p0_tasks_picktwo9.json")
    parser.add_argument("--max-steps", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-root", type=Path, default=ROOT / "runs")
    return parser.parse_args()


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

    cell_names = (
        list(CELLS)
        if args.cells == "all"
        else tuple(name.strip() for name in args.cells.split(",") if name.strip())
    )
    unknown = [name for name in cell_names if name not in CELLS]
    if unknown:
        raise ValueError(f"Unknown cells: {', '.join(unknown)}")

    for cell_name in cell_names:
        cell = CELLS[cell_name]
        retriever = RETRIEVERS[cell["retriever"]]()
        executor = ReActExecutor(client, structured_skills=cell["structured"])
        writer = JsonlTraceWriter(args.output_root, f"w3_2_{cell_name}")
        manifest = {
            "experiment_id": "w3_2_factorial",
            "run_id": writer.run_id,
            "configuration_name": cell_name,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "task_manifest": str(task_manifest.relative_to(ROOT)),
            "task_count": len(tasks),
            "retriever": retriever.name,
            "executor": executor.name,
            "structured_skills": cell["structured"],
            "backend": backend.name,
            "model": backend.model,
            "max_steps": args.max_steps,
            "seed": args.seed,
            "skill_library": "alfworld_static_v0",
            "environment": "alfworld_text_0.4.2",
            "host": {"platform": platform.system(), "architecture": platform.machine()},
            "interpretation": (
                "Phase-3 2x2 factorial cell. R0=lexical, R1=task-semantic; "
                "E0=flat ReAct, E1=structured ReAct. Control=no-skill ablation."
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
                top_k=2,
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
                    "task_id": task["task_id"],
                    "task_family": task["task_family"],
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
            "experiment_id": "w3_2_factorial",
            "run_id": writer.run_id,
            "configuration_name": cell_name,
            "retriever": retriever.name,
            "executor": executor.name,
            "structured_skills": cell["structured"],
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
            "interpretation": "Phase-3 factorial cell; compare cells with raw counts only.",
        }
        writer.write_summary(summary)
        run_summaries.append(
            {
                "cell": cell_name,
                "retriever": retriever.name,
                "structured_skills": cell["structured"],
                "run_id": writer.run_id,
                "run_directory": str(writer.run_dir.relative_to(ROOT)),
                "success_count": summary["success_count"],
                "episode_count": len(episode_summaries),
                "total_cost_estimate_usd": summary["total_cost_estimate_usd"],
            }
        )

    print(json.dumps({"cells": run_summaries}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
