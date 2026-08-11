"""Narrow ALFWorld text-environment adapter for deterministic P0.0 episodes."""

from __future__ import annotations

import os
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any, Dict, Tuple


def create_single_game_environment(
    data_root: Path, relative_game_file: str, quiet: bool = True
) -> Tuple[Any, str, Dict[str, Any]]:
    """Reset one manifest-selected ALFWorld text game and return unbatched state."""

    data_root = data_root.resolve()
    game_file = (data_root / relative_game_file).resolve()
    if not game_file.exists():
        raise FileNotFoundError(f"ALFWorld game file does not exist: {game_file}")
    os.environ["ALFWORLD_DATA"] = str(data_root)
    from alfworld.agents.environment.alfred_tw_env import AlfredTWEnv

    config = {
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
    # ALFWorld reports game collection progress directly to stdout. The runner
    # emits machine-readable JSON, so capture that third-party chatter here;
    # callers can set quiet=False while debugging environment setup.
    output = StringIO()
    stdout_context = redirect_stdout(output) if quiet else _nullcontext()
    with stdout_context:
        wrapper = AlfredTWEnv(config, train_eval="eval_out_of_distribution")
        if str(game_file) not in {str(Path(path).resolve()) for path in wrapper.game_files}:
            raise ValueError(f"Game is not accepted as a loadable ALFWorld text game: {game_file}")
        wrapper.game_files = [str(game_file)]
        wrapper.num_games = 1
        env = wrapper.init_env(batch_size=1)
        observations, infos = env.reset()
    return env, observations[0], _unbatch_info(infos)


def _unbatch_info(infos: Dict[str, Any]) -> Dict[str, Any]:
    return {
        key: value[0] if isinstance(value, list) and len(value) == 1 else value
        for key, value in infos.items()
    }


class _nullcontext:
    """A tiny Python 3.9-compatible no-op context manager."""

    def __enter__(self) -> None:
        return None

    def __exit__(self, *args: Any) -> None:
        return None
