"""Run one in-memory P0.0 episode; JSONL persistence is intentionally deferred."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skillstack.execution import RecordedActionExecutor
from skillstack.library import load_static_library
from skillstack.retrieval import DebugLexicalRetriever, NoSkillRetriever
from skillstack.runner import EpisodeRunner
from skillstack.tasks import find_task, load_p0_tasks, load_recorded_actions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retriever", choices=("no_skill", "debug_lexical"), default="debug_lexical")
    parser.add_argument("--task-id", default=None, help="A stable task ID from configs/p0_tasks.json")
    parser.add_argument("--task-index", type=int, default=0, help="Manifest index used when --task-id is omitted")
    parser.add_argument("--top-k", type=int, default=2)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tasks = load_p0_tasks()
    if args.task_id:
        task = find_task(args.task_id)
    else:
        task = tasks[args.task_index]
    retriever = NoSkillRetriever() if args.retriever == "no_skill" else DebugLexicalRetriever()
    runner = EpisodeRunner(
        data_root=ROOT / "data" / "alfworld",
        native_skills=load_static_library(),
        retriever=retriever,
        executor=RecordedActionExecutor(),
    )
    trace = runner.run(task, load_recorded_actions(task["task_id"]), top_k=args.top_k)
    print(json.dumps(trace, indent=2, ensure_ascii=False))
    return 0 if trace["stop_reason"] != "runner_exception" else 1


if __name__ == "__main__":
    raise SystemExit(main())

