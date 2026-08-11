"""Run one deterministic ALFWorld text-environment reset and action."""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = ROOT / "data" / "alfworld"
DEFAULT_OUTPUT = ROOT / "reports" / "phase1_alfworld_smoke.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--game-index", type=int, default=0)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def build_config(data_root: Path) -> Dict[str, Any]:
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
    data_root = args.data_root.resolve()
    games_root = data_root / "json_2.1.1" / "valid_unseen"
    if not games_root.exists():
        raise FileNotFoundError(
            f"ALFWorld text data not found at {games_root}. "
            "Download the P0.0 text assets before running this script."
        )

    # ALFWorld reads this variable at import time; set it before loading the
    # environment modules so all benchmark assets remain project-local.
    os.environ["ALFWORLD_DATA"] = str(data_root)
    from alfworld.agents.environment.alfred_tw_env import AlfredTWEnv

    wrapper = AlfredTWEnv(build_config(data_root), train_eval="eval_out_of_distribution")
    game_files = sorted(wrapper.game_files)
    if not game_files:
        raise RuntimeError(f"No loadable valid_unseen games found under {games_root}.")
    if not 0 <= args.game_index < len(game_files):
        raise IndexError(f"game-index must be in [0, {len(game_files) - 1}].")

    wrapper.game_files = [game_files[args.game_index]]
    wrapper.num_games = 1
    env = wrapper.init_env(batch_size=1)
    try:
        observations, infos = env.reset()
        commands = list(infos["admissible_commands"][0])
        action = "look" if "look" in commands else commands[0]
        next_observations, scores, dones, _ = env.step([action])
    finally:
        env.close()

    result = {
        "experiment_id": "p0_0_vertical_slice",
        "phase": "1",
        "status": "passed",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "platform": f"{platform.system()} {platform.machine()}",
        "python": sys.version.split()[0],
        "data_root": str(data_root),
        "split": "valid_unseen",
        "available_games": len(game_files),
        "game_index": args.game_index,
        "game_file": infos["extra.gamefile"][0],
        "initial_observation": observations[0],
        "admissible_command_count": len(commands),
        "action": action,
        "next_observation": next_observations[0],
        "reward": scores[0],
        "done": dones[0],
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

