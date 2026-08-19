"""Validate a task manifest with a real ALFWorld reset per task."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "configs" / "p0_tasks_hard.json"
DEFAULT_REPORT = ROOT / "reports" / "week3" / "w3_hard_tasks_validation.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--expected-count", type=int, default=None)
    return parser.parse_args()


def build_alfworld_config(data_root: Path) -> Dict[str, Any]:
    return {
        "env": {
            "goal_desc_human_anns_prob": 0.0,
            "task_types": [1, 2, 3, 4, 5, 6],
            "domain_randomization": False,
            "expert_type": "handcoded",
        },
        "dataset": {
            "eval_ood_data_path": str(data_root / "json_2.1.1" / "valid_unseen"),
            "num_eval_games": 0,
        },
        "general": {"training_method": "dagger"},
        "dagger": {"training": {"max_nb_steps_per_episode": 50}},
    }


def main() -> int:
    args = parse_args()
    manifest_path = args.manifest.resolve()
    report_path = args.report.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    data_root = (ROOT / manifest["environment"]["data_root"]).resolve()
    tasks: List[Dict[str, Any]] = manifest["tasks"]
    errors: List[str] = []
    if args.expected_count is not None and len(tasks) != args.expected_count:
        errors.append(f"Expected {args.expected_count} tasks, found {len(tasks)}")
    if len({task["task_id"] for task in tasks}) != len(tasks):
        errors.append("Task IDs are not unique")

    os.environ["ALFWORLD_DATA"] = str(data_root)
    from alfworld.agents.environment.alfred_tw_env import AlfredTWEnv

    wrapper = AlfredTWEnv(build_alfworld_config(data_root), train_eval="eval_out_of_distribution")
    available_game_files = {str(Path(path).resolve()) for path in wrapper.game_files}
    checks = []
    for task in tasks:
        game_file = (data_root / task["game_file"]).resolve()
        trajectory_file = (data_root / task["trajectory_file"]).resolve()
        task_errors: List[str] = []
        if not game_file.exists():
            task_errors.append("missing game file")
        if not trajectory_file.exists():
            task_errors.append("missing trajectory file")

        if trajectory_file.exists():
            trajectory = json.loads(trajectory_file.read_text(encoding="utf-8"))
            if trajectory["task_type"] != task["task_family"]:
                task_errors.append("task-family does not match trajectory")
            annotation = trajectory["turk_annotations"]["anns"][0]["task_desc"]
            if annotation != task["task_instruction"]:
                task_errors.append("task instruction does not match trajectory")
        if game_file.exists():
            game = json.loads(game_file.read_text(encoding="utf-8"))
            if not game.get("solvable"):
                task_errors.append("game is marked unsolvable")
            if str(game_file) not in available_game_files:
                task_errors.append("game is not accepted by AlfredTWEnv")

        observation_preview = None
        if not task_errors:
            wrapper.game_files = [str(game_file)]
            wrapper.num_games = 1
            env = wrapper.init_env(batch_size=1)
            try:
                observations, infos = env.reset()
                observation_preview = observations[0][:160]
                if not infos["admissible_commands"][0]:
                    task_errors.append("reset returned no admissible commands")
            except Exception as error:
                task_errors.append(f"environment reset failed: {error}")
            finally:
                env.close()

        checks.append(
            {
                "task_id": task["task_id"],
                "task_family": task["task_family"],
                "expected_skill_id": task["expected_skill_id"],
                "reset_passed": not task_errors,
                "initial_observation_preview": observation_preview,
                "errors": task_errors,
            }
        )
        errors.extend(f"{task['task_id']}: {error}" for error in task_errors)

    report = {
        "experiment_id": "task_set_validation",
        "phase": "2d_d1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "manifest": str(manifest_path.relative_to(ROOT)),
        "task_count": len(tasks),
        "status": "passed" if not errors else "failed",
        "checks": checks,
        "errors": errors,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
