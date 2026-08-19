"""A deterministic executor that validates and replays supplied ALFWorld actions."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional


class RecordedActionExecutor:
    """Execute a fixed action sequence without inferring an action policy.

    This component verifies the retrieval-to-execution boundary and real
    environment trace shape. It is not a ReAct implementation and makes no
    claim that selected skills caused the recorded actions.
    """

    name = "recorded_action_executor"

    def execute(
        self,
        env: Any,
        initial_observation: str,
        initial_info: Dict[str, Any],
        execution_input: Dict[str, Any],
        recorded_actions: Optional[Iterable[str]] = None,
        task_record: Optional[Dict[str, Any]] = None,
        max_steps: Optional[int] = None,
    ) -> Dict[str, Any]:
        _validate_execution_input(execution_input)
        recorded_actions = list(recorded_actions or [])
        current_info = initial_info
        observations = [initial_observation]
        actions: List[str] = []
        rewards: List[float] = []
        warnings: List[str] = []
        success = False
        stop_reason = "recorded_actions_exhausted"

        for step_index, action in enumerate(recorded_actions, start=1):
            admissible_commands = current_info.get("admissible_commands", [])
            if action not in admissible_commands:
                stop_reason = "action_not_admissible"
                warnings.append(
                    f"Recorded action at step {step_index} is not admissible: {action!r}"
                )
                break
            next_observations, scores, dones, next_infos = env.step([action])
            actions.append(action)
            observations.append(next_observations[0])
            rewards.append(float(scores[0]))
            current_info = _unbatch_info(next_infos)
            if dones[0]:
                success = bool(scores[0] > 0)
                stop_reason = "environment_done"
                break

        if not actions and stop_reason == "recorded_actions_exhausted":
            warnings.append("No recorded actions were supplied to the executor.")

        return {
            "executor_name": self.name,
            "action_source": "recorded_action_fixture",
            "actions": actions,
            "observations": observations,
            "rewards": rewards,
            "success": success,
            "stop_reason": stop_reason,
            "warnings": warnings,
        }


def _validate_execution_input(execution_input: Dict[str, Any]) -> None:
    required = (
        "selected_skill_ids",
        "selected_scores",
        "selected_native_skills",
        "flat_skill_context",
    )
    missing = [field for field in required if field not in execution_input]
    if missing:
        raise ValueError(f"Execution input is missing fields: {', '.join(missing)}")


def _unbatch_info(infos: Dict[str, Any]) -> Dict[str, Any]:
    return {
        key: value[0] if isinstance(value, list) and len(value) == 1 else value
        for key, value in infos.items()
    }

