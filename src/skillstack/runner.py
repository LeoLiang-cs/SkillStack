"""Run one in-memory P0.0 episode through swappable retrieval and execution."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from skillstack.adapters.retrieval_to_execution import adapt_retrieval_for_execution
from skillstack.contracts import TASK_RECORD_FIELDS, require_fields
from skillstack.environments.alfworld_text import create_single_game_environment


class EpisodeRunner:
    """Connect native skills, a retriever, adapter, executor, and one ALFWorld game."""

    def __init__(
        self,
        data_root: Path,
        native_skills: List[Dict[str, Any]],
        retriever: Any,
        executor: Any,
    ) -> None:
        self.data_root = data_root.resolve()
        self.native_skills = native_skills
        self.retriever = retriever
        self.executor = executor

    def run(
        self,
        task_record: Dict[str, Any],
        recorded_actions: Iterable[str],
        top_k: int = 2,
    ) -> Dict[str, Any]:
        require_fields(task_record, TASK_RECORD_FIELDS, "episode task record")
        trace: Dict[str, Any] = {
            "experiment_id": "p0_0_vertical_slice",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "task_id": task_record["task_id"],
            "task_family": task_record["task_family"],
            "task_instruction": task_record["task_instruction"],
            "retriever_name": getattr(self.retriever, "name", type(self.retriever).__name__),
            "executor_name": getattr(self.executor, "name", type(self.executor).__name__),
            "success": False,
            "warnings": [],
        }
        env = None
        try:
            env, initial_observation, initial_info = create_single_game_environment(
                self.data_root, task_record["game_file"]
            )
            retrieval_response = self.retriever.retrieve(
                task_record, initial_observation, self.native_skills, top_k
            )
            execution_input, adapter_event = adapt_retrieval_for_execution(retrieval_response)
            executor_report = self.executor.execute(
                env,
                initial_observation,
                initial_info,
                execution_input,
                recorded_actions,
            )
            trace.update(
                {
                    "raw_observations": executor_report["observations"],
                    "retrieval_response": retrieval_response,
                    "selected_skill_ids": execution_input["selected_skill_ids"],
                    "selected_native_payloads": execution_input["selected_native_skills"],
                    "adapter_events": [adapter_event],
                    "executor_report": executor_report,
                    "actions": executor_report["actions"],
                    "rewards": executor_report["rewards"],
                    "success": executor_report["success"],
                    "stop_reason": executor_report["stop_reason"],
                    "warnings": retrieval_response["warnings"]
                    + adapter_event["warnings"]
                    + executor_report["warnings"],
                }
            )
        except Exception as error:
            trace.update(
                {
                    "stop_reason": "runner_exception",
                    "warnings": [f"{type(error).__name__}: {error}"],
                }
            )
        finally:
            if env is not None:
                env.close()
        return trace

