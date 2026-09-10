"""Small deterministic environment used by the public zero-model demo."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


class DeterministicFixtureEnv:
    """A one-step, batch-compatible environment with no external dependency.

    The fixture validates the runtime shape expected by ``RecordedActionExecutor``.
    Its positive transition demonstrates pipeline completion only; it is not a
    benchmark task and must not be interpreted as an agent success result.
    """

    name = "deterministic_fixture_v1"

    def __init__(self, task_id: str, seed: int = 42) -> None:
        if not task_id:
            raise ValueError("task_id must be a non-empty string")
        self.task_id = task_id
        self.seed = seed
        self._step_index = 0
        self._done = False
        self._closed = False
        self.invalid_actions: List[str] = []

    def reset(self) -> Tuple[List[str], Dict[str, Any]]:
        """Reset the fixture and return the same batched shape as ALFWorld."""

        if self._closed:
            raise RuntimeError("Cannot reset a closed fixture environment")
        self._step_index = 0
        self._done = False
        self.invalid_actions = []
        return [self._observation("ready")], self._batched_info(["look"])

    def step(self, actions: List[str]) -> Tuple[List[str], List[float], List[bool], Dict[str, Any]]:
        """Apply exactly one action and return batched observations and metadata."""

        if self._closed:
            raise RuntimeError("Cannot step a closed fixture environment")
        if len(actions) != 1:
            raise ValueError("DeterministicFixtureEnv accepts exactly one action")

        action = actions[0]
        self._step_index += 1
        if self._done:
            return (
                [self._observation("already_done")],
                [0.0],
                [True],
                self._batched_info([]),
            )

        if action == "look":
            self._done = True
            return (
                [self._observation("looked")],
                [1.0],
                [True],
                self._batched_info([]),
            )

        self.invalid_actions.append(action)
        return (
            [self._observation("invalid_action")],
            [0.0],
            [False],
            self._batched_info(["look"]),
        )

    def close(self) -> None:
        self._closed = True

    def _observation(self, state: str) -> str:
        return (
            f"Fixture room for {self.task_id}: state={state}; "
            f"step={self._step_index}; seed={self.seed}."
        )

    def _batched_info(self, admissible_commands: List[str]) -> Dict[str, Any]:
        return {
            "admissible_commands": [list(admissible_commands)],
            "fixture_state": ["done" if self._done else "ready"],
            "fixture_seed": [self.seed],
            "invalid_actions": [list(self.invalid_actions)],
        }


def create_fixture_environment(
    _data_root: Any, task_record: Dict[str, Any], seed: int = 42
) -> Tuple[DeterministicFixtureEnv, str, Dict[str, Any]]:
    """Create and reset a fixture environment using the runner factory shape."""

    env = DeterministicFixtureEnv(task_record["task_id"], seed=seed)
    observations, infos = env.reset()
    return env, observations[0], _unbatch_info(infos)


def _unbatch_info(infos: Dict[str, Any]) -> Dict[str, Any]:
    return {
        key: value[0] if isinstance(value, list) and len(value) == 1 else value
        for key, value in infos.items()
    }
