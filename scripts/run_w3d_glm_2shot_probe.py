"""D3 attribution probe: GLM-4.7-FlashX + 2-shot prompt, oracle, 12-step cap.

Measures action-validity rate (not task success) to attribute the week-3 GLM
failure to prompt coupling vs a model capability floor. Writes a JSON report.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skillstack.execution import ReActExecutor
from skillstack.library import load_static_library
from skillstack.llm import LlmClient, load_backends, load_env_file
from skillstack.retrieval import OracleSkillRetriever
from skillstack.runner import EpisodeRunner
from skillstack.tasks import load_p0_tasks

TWO_SHOT_PROMPT = ROOT / "configs" / "p0_react_prompt_2shot.txt"
VALIDITY_THRESHOLD = 0.9


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-steps", type=int, default=12)
    parser.add_argument("--backend", default="zhipu_glm_flashx")
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "week3" / "w3_glm_2shot_probe.json")
    return parser.parse_args()


def validity_stats(trace: Dict[str, Any]) -> Dict[str, Any]:
    calls = trace.get("executor_report", {}).get("llm_calls", [])
    first_attempts = [call for call in calls if call.get("attempt", 1) == 1]
    retries = [call for call in calls if call.get("attempt", 1) > 1]
    valid_first_try = len(first_attempts) - len(retries)
    rate = (valid_first_try / len(first_attempts)) if first_attempts else 0.0
    return {
        "first_attempt_calls": len(first_attempts),
        "retry_calls": len(retries),
        "valid_first_try": valid_first_try,
        "validity_rate": round(rate, 4),
    }


def main() -> int:
    args = parse_args()
    load_env_file()
    backend = load_backends()[args.backend]
    client = LlmClient(backend)
    executor = ReActExecutor(client, prompt_path=TWO_SHOT_PROMPT)
    tasks = load_p0_tasks()
    skills = load_static_library()
    runner = EpisodeRunner(ROOT / "data" / "alfworld", skills, OracleSkillRetriever(), executor)

    cases = []
    for task in tasks:
        trace = runner.run(task, recorded_actions=None, top_k=2, max_steps=args.max_steps)
        stats = validity_stats(trace)
        cases.append(
            {
                "task_id": task["task_id"],
                "task_family": task["task_family"],
                "success": trace["success"],
                "stop_reason": trace.get("stop_reason"),
                "action_count": len(trace.get("actions", [])),
                **stats,
            }
        )

    total_first = sum(case["first_attempt_calls"] for case in cases)
    total_valid = sum(case["valid_first_try"] for case in cases)
    overall_rate = (total_valid / total_first) if total_first else 0.0
    attribution = "prompt_coupling" if overall_rate >= VALIDITY_THRESHOLD else "capability_floor"

    report = {
        "experiment_id": "w3d_glm_2shot_attribution",
        "phase": "2d_d3",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "backend": backend.name,
        "model": backend.model,
        "prompt": str(TWO_SHOT_PROMPT.relative_to(ROOT)),
        "max_steps": args.max_steps,
        "condition": "oracle",
        "overall_validity_rate": round(overall_rate, 4),
        "validity_threshold": VALIDITY_THRESHOLD,
        "attribution": attribution,
        "cases": cases,
        "interpretation": (
            "Validity rate is the fraction of first-attempt actions that were "
            "admissible. >= threshold attributes the week-3 GLM failure to prompt "
            "coupling; < threshold attributes it to a model capability floor."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
