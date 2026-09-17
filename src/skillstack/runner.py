"""Run one in-memory P0.0 episode through swappable retrieval and execution."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Tuple

from skillstack.adapters.retrieval_to_execution import adapt_retrieval_for_execution
from skillstack.blm import (
    BLM_BOUNDARY_SCHEMA_V2,
    BLM_INTERVENTION_SCHEMA_V3,
    STATE_SCOPE,
    apply_boundary_intervention,
    finalize_boundary_record,
    instrument_execution_input,
)
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
        environment_factory: Optional[
            Callable[[Path, Dict[str, Any]], Tuple[Any, str, Dict[str, Any]]]
        ] = None,
    ) -> None:
        self.data_root = data_root.resolve()
        self.native_skills = native_skills
        self.retriever = retriever
        self.executor = executor
        self.environment_factory = environment_factory

    def run(
        self,
        task_record: Dict[str, Any],
        recorded_actions: Optional[Iterable[str]] = None,
        top_k: int = 2,
        max_steps: Optional[int] = None,
        *,
        blm_intervention: Optional[Mapping[str, Any]] = None,
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
        read_tracker = None
        consumer_reads = None
        try:
            if self.environment_factory is None:
                env, initial_observation, initial_info = create_single_game_environment(
                    self.data_root, task_record["game_file"]
                )
            else:
                env, initial_observation, initial_info = self.environment_factory(
                    self.data_root, task_record
                )
            retrieval_response = self.retriever.retrieve(
                task_record, initial_observation, self.native_skills, top_k
            )
            execution_input, adapter_event = adapt_retrieval_for_execution(retrieval_response)
            blm_boundary = None
            blm_v3 = (
                isinstance(blm_intervention, Mapping)
                and blm_intervention.get("schema_version") == BLM_INTERVENTION_SCHEMA_V3
            )
            if blm_intervention is not None:
                natural_apply = None
                if blm_v3:
                    from skillstack.experiments.blm_natural import (
                        apply_natural_boundary_intervention,
                    )

                    natural_apply = apply_natural_boundary_intervention
                context = {
                    "task_record": task_record,
                    "initial_observation": initial_observation,
                    "initial_info": initial_info,
                    "environment_class": (
                        f"{type(env).__module__}.{type(env).__qualname__}"
                    ),
                    "consumer_name": getattr(
                        self.executor, "name", type(self.executor).__name__
                    ),
                    "consumer_step_budget": getattr(
                        self.executor, "step_budget_per_plan_step", None
                    ),
                    "native_skills": self.native_skills,
                    "top_k": top_k,
                    "effective_max_steps": max_steps if max_steps is not None else 50,
                    "state_scope": STATE_SCOPE,
                    "retrieval_response": retrieval_response,
                }
                if blm_v3:
                    from skillstack.experiments.blm_natural import build_natural_context

                    prompt_template = getattr(self.executor, "prompt_template", "")
                    backend = getattr(getattr(self.executor, "client", None), "backend", None)
                    natural_context = build_natural_context(
                        env,
                        task_record,
                        initial_observation,
                        initial_info,
                        self.native_skills,
                        top_k=top_k,
                        max_steps=max_steps if max_steps is not None else 50,
                        prompt_template=prompt_template,
                        backend_name=getattr(backend, "name", None) or "unknown",
                        model=getattr(backend, "model", None) or "unknown",
                        max_tokens_per_step=getattr(self.executor, "max_tokens_per_step", None)
                        or 512,
                        consumer_step_budget=getattr(
                            self.executor, "step_budget_per_plan_step", None
                        ),
                    )
                    effective_input, blm_boundary = natural_apply(
                        execution_input, blm_intervention, natural_context
                    )
                else:
                    effective_input, blm_boundary = apply_boundary_intervention(
                        execution_input, blm_intervention, context
                    )
                if effective_input is None:
                    warning = f"BLM intervention rejected: {blm_boundary['validity_reason']}"
                    trace.update(
                        {
                            "raw_observations": [initial_observation],
                            "retrieval_response": retrieval_response,
                            "selected_skill_ids": execution_input["selected_skill_ids"],
                            "selected_native_payloads": execution_input[
                                "selected_native_skills"
                            ],
                            "adapter_events": [adapter_event],
                            "executor_report": {},
                            "actions": [],
                            "action_rationales": [],
                            "rewards": [],
                            "success": False,
                            "stop_reason": "invalid_input",
                            "warnings": retrieval_response["warnings"]
                            + adapter_event["warnings"]
                            + [warning],
                            "blm_boundary": blm_boundary,
                        }
                    )
                    return trace
                execution_input = effective_input
                if blm_boundary.get("schema_version") == BLM_BOUNDARY_SCHEMA_V2:
                    execution_input, read_tracker = instrument_execution_input(execution_input)
                elif blm_v3:
                    execution_input, read_tracker = instrument_execution_input(
                        execution_input, mode="v3"
                    )
            executor_report = self.executor.execute(
                env,
                initial_observation,
                initial_info,
                execution_input,
                recorded_actions=recorded_actions,
                task_record=task_record,
                max_steps=max_steps,
            )
            if read_tracker is not None:
                # Freeze the Consumer-only event stream before Runner serializes
                # selected fields into the top-level trace.
                consumer_reads = list(read_tracker.events)
            trace.update(
                {
                    "raw_observations": executor_report["observations"],
                    "retrieval_response": retrieval_response,
                    "selected_skill_ids": execution_input["selected_skill_ids"],
                    "selected_native_payloads": execution_input["selected_native_skills"],
                    "adapter_events": [adapter_event],
                    "executor_report": executor_report,
                    "actions": executor_report["actions"],
                    "action_rationales": executor_report.get("action_rationales", []),
                    "rewards": executor_report["rewards"],
                    "success": executor_report["success"],
                    "stop_reason": executor_report["stop_reason"],
                    "warnings": retrieval_response["warnings"]
                    + adapter_event["warnings"]
                    + executor_report["warnings"],
                }
            )
            if blm_boundary is not None:
                if blm_v3:
                    from skillstack.experiments.blm_natural import (
                        finalize_natural_boundary_record,
                    )

                    trace["blm_boundary"] = finalize_natural_boundary_record(
                        blm_boundary, executor_report, consumer_reads
                    )
                else:
                    trace["blm_boundary"] = finalize_boundary_record(
                        blm_boundary,
                        executor_report,
                        consumer_reads,
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
