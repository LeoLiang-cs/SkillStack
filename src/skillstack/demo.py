"""Run the public, zero-model SkillStack composability demonstration."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Type

from skillstack.adapters.retrieval_to_execution import adapt_retrieval_for_execution
from skillstack.environments.fixture import create_fixture_environment
from skillstack.execution import RecordedActionExecutor
from skillstack.library import load_static_library
from skillstack.retrieval import DebugLexicalRetriever, NoSkillRetriever
from skillstack.runner import EpisodeRunner
from skillstack.tracing import JsonlTraceWriter


DEMO_ID = "skillstack_zero_model_demo_v1"
DEMO_SEED = 42
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIGURATION_TYPES: Tuple[Tuple[str, Type[Any]], ...] = (
    ("c0_no_skill", NoSkillRetriever),
    ("c1_debug_lexical", DebugLexicalRetriever),
)


def load_demo_fixtures(root: Path) -> Tuple[Dict[str, Any], List[str], Path, Path]:
    """Load and validate the committed task and recorded-action fixtures."""

    demo_dir = root.expanduser().resolve() / "examples" / "demo"
    task_path = demo_dir / "task.json"
    actions_path = demo_dir / "recorded_actions.json"
    task = json.loads(task_path.read_text(encoding="utf-8"))
    required = ("task_id", "task_family", "task_instruction", "game_file")
    missing = [field for field in required if field not in task]
    if missing:
        raise ValueError(f"Demo task is missing required fields: {', '.join(missing)}")
    if task.get("benchmark_success_claim") is not False:
        raise ValueError("Demo task must explicitly set benchmark_success_claim to false")
    fixture = json.loads(actions_path.read_text(encoding="utf-8"))
    actions_by_task = fixture.get("actions_by_task_id", {})
    actions = actions_by_task.get(task["task_id"])
    if actions is None:
        raise ValueError(f"Demo action fixture has no actions for {task['task_id']}")
    if not isinstance(actions, list) or not all(isinstance(action, str) for action in actions):
        raise ValueError("Demo recorded actions must be a list of strings")
    return task, list(actions), task_path, actions_path


def run_demo(
    root: Optional[Path] = None,
    output_root: Optional[Path] = None,
    configuration: str = "all",
    top_k: int = 2,
    run_id_prefix: Optional[str] = None,
) -> Dict[str, Any]:
    """Run one or both retriever cells through the shared execution path.

    The returned result is a pipeline demonstration record. ``fixture_success``
    means that the deterministic fixture completed; it is deliberately not a
    benchmark-success or agent-performance claim.
    """

    repository = (root or REPOSITORY_ROOT).expanduser().resolve()
    if configuration not in {"all", "c0_no_skill", "c1_debug_lexical"}:
        raise ValueError(f"Unknown demo configuration: {configuration}")
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    task, recorded_actions, task_path, actions_path = load_demo_fixtures(repository)
    native_skills = load_static_library(repository / "skills" / "alfworld_static")
    selected_configurations = _selected_configurations(configuration)
    demo_output_root = (output_root or repository / "runs").expanduser().resolve() / "demo"
    demo_output_root.mkdir(parents=True, exist_ok=True)

    input_hashes = {
        "task_fixture_sha256": _sha256_file(task_path),
        "recorded_actions_sha256": _sha256_file(actions_path),
        "native_library_sha256": _sha256_library(native_skills),
    }
    writers: List[Tuple[str, JsonlTraceWriter]] = []
    traces_by_configuration: Dict[str, Dict[str, Any]] = {}

    for configuration_name, retriever_type in selected_configurations:
        requested_run_id = None
        if run_id_prefix:
            requested_run_id = f"{_safe_run_id_component(run_id_prefix)}_{configuration_name}"
        writer = JsonlTraceWriter(demo_output_root, f"demo_{configuration_name}", requested_run_id)
        retriever = retriever_type()
        executor = RecordedActionExecutor()
        manifest = _build_manifest(
            writer=writer,
            task=task,
            task_path=task_path,
            actions_path=actions_path,
            repository=repository,
            input_hashes=input_hashes,
            retriever_name=retriever.name,
            executor_name=executor.name,
            top_k=top_k,
        )
        writer.write_manifest(manifest)

        runner = EpisodeRunner(
            data_root=repository / "data" / "alfworld",
            native_skills=native_skills,
            retriever=retriever,
            executor=executor,
            environment_factory=create_fixture_environment,
        )
        trace = runner.run(task, recorded_actions, top_k=top_k)
        trace.update(
            {
                "experiment_id": "zero_model_composability_demo",
                "run_id": writer.run_id,
                "episode_id": f"{writer.run_id}_episode_00",
                "episode_index": 0,
                "demo_id": DEMO_ID,
                "environment_kind": "deterministic_fixture",
                "environment_version": "deterministic_fixture_v1",
                "benchmark_success_claim": False,
                "seed": DEMO_SEED,
                "task_source": _relative(task_path, repository),
                "recorded_action_source": _relative(actions_path, repository),
                "network_calls": 0,
                "model_calls": 0,
            }
        )
        if trace.get("stop_reason") == "runner_exception":
            raise RuntimeError(
                f"Demo runner failed for {configuration_name}: "
                f"{trace.get('warnings', ['unknown error'])[-1]}"
            )
        writer.append_episode(trace)
        traces_by_configuration[configuration_name] = trace
        writers.append((configuration_name, writer))

    comparison = _build_comparison(traces_by_configuration)
    comparison_fingerprint = _comparison_fingerprint(traces_by_configuration, comparison)
    run_records: List[Dict[str, Any]] = []
    for configuration_name, writer in writers:
        trace = traces_by_configuration[configuration_name]
        summary = _build_summary(trace, comparison, comparison_fingerprint, writer)
        writer.write_summary(summary)
        run_records.append(
            {
                "configuration_name": configuration_name,
                "run_id": writer.run_id,
                "run_directory": str(writer.run_dir),
                "summary": summary,
            }
        )

    result = {
        "demo_id": DEMO_ID,
        "configuration": configuration,
        "task_id": task["task_id"],
        "comparison": comparison,
        "comparison_fingerprint": comparison_fingerprint,
        "benchmark_success_claim": False,
        "network_calls": 0,
        "model_calls": 0,
        "runs": run_records,
    }
    if configuration == "all":
        demo_dir = repository / "examples" / "demo"
        _check_expected_fingerprint(demo_dir / "expected_fingerprint.txt", comparison_fingerprint)
        _check_expected_summary(demo_dir / "expected_summary.json", result)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="repository root containing examples/demo and skills (default: current directory)",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path.cwd() / "runs",
        help="directory under which demo/<run-id> directories are created",
    )
    parser.add_argument(
        "--configuration",
        choices=("all", "c0_no_skill", "c1_debug_lexical"),
        default="all",
    )
    parser.add_argument("--top-k", type=int, default=2)
    parser.add_argument(
        "--run-id-prefix",
        default=None,
        help="optional deterministic prefix for tests or resumable local runs",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_demo(
        root=args.root,
        output_root=args.output_root,
        configuration=args.configuration,
        top_k=args.top_k,
        run_id_prefix=args.run_id_prefix,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


def _selected_configurations(selection: str) -> Iterable[Tuple[str, Type[Any]]]:
    if selection == "all":
        return CONFIGURATION_TYPES
    return tuple(item for item in CONFIGURATION_TYPES if item[0] == selection)


def _build_manifest(
    writer: JsonlTraceWriter,
    task: Dict[str, Any],
    task_path: Path,
    actions_path: Path,
    repository: Path,
    input_hashes: Dict[str, str],
    retriever_name: str,
    executor_name: str,
    top_k: int,
) -> Dict[str, Any]:
    return {
        "schema_version": "skillstack-demo-manifest-v1",
        "demo_id": DEMO_ID,
        "experiment_id": "zero_model_composability_demo",
        "run_id": writer.run_id,
        "configuration_name": _configuration_for_retriever(retriever_name),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "seed": DEMO_SEED,
        "task": task,
        "task_source": _relative(task_path, repository),
        "recorded_action_source": _relative(actions_path, repository),
        "retriever": retriever_name,
        "executor": executor_name,
        "adapter": "retrieval_to_execution_adapter",
        "top_k": top_k,
        "environment_kind": "deterministic_fixture",
        "environment_version": "deterministic_fixture_v1",
        "input_hashes": input_hashes,
        "network_calls": 0,
        "model_calls": 0,
        "benchmark_success_claim": False,
        "interpretation": "Pipeline and trace validation only; fixture completion is not benchmark performance.",
    }


def _build_summary(
    trace: Dict[str, Any],
    comparison: Dict[str, Any],
    comparison_fingerprint: str,
    writer: JsonlTraceWriter,
) -> Dict[str, Any]:
    adapter_events = trace.get("adapter_events", [])
    lossless_count = sum(1 for event in adapter_events if _adapter_event_is_lossless(event))
    summary_core = {
        "demo_id": DEMO_ID,
        "configuration_name": trace["retriever_name"],
        "task_id": trace["task_id"],
        "selected_skill_ids": trace.get("selected_skill_ids", []),
        "actions": trace.get("actions", []),
        "rewards": trace.get("rewards", []),
        "success": bool(trace.get("success", False)),
        "stop_reason": trace.get("stop_reason"),
        "adapter_lossless": lossless_count == len(adapter_events),
    }
    return {
        "schema_version": "skillstack-demo-summary-v1",
        "demo_id": DEMO_ID,
        "run_id": writer.run_id,
        "configuration_name": _configuration_for_retriever(trace["retriever_name"]),
        "task_count": 1,
        "episode_count": 1,
        "completed_count": int(trace.get("stop_reason") == "environment_done"),
        "fixture_success_count": int(bool(trace.get("success", False))),
        "selected_skill_ids": trace.get("selected_skill_ids", []),
        "action_count": len(trace.get("actions", [])),
        "adapter_event_count": len(adapter_events),
        "lossless_adapter_event_count": lossless_count,
        "warning_count": len(trace.get("warnings", [])),
        "network_calls": 0,
        "model_calls": 0,
        "benchmark_success_claim": False,
        "run_fingerprint": _sha256_json(summary_core),
        "comparison_fingerprint": comparison_fingerprint,
        "comparison": comparison,
        "interpretation": "Fixture completion validates the shared pipeline, not task-solving performance.",
    }


def _build_comparison(traces: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    c0 = traces.get("c0_no_skill", {})
    c1 = traces.get("c1_debug_lexical", {})
    c0_ids = c0.get("selected_skill_ids", [])
    c1_ids = c1.get("selected_skill_ids", [])
    return {
        "cells": sorted(traces),
        "selection_changed": c0_ids != c1_ids if c0 and c1 else None,
        "c0_selected_skill_ids": c0_ids,
        "c1_selected_skill_ids": c1_ids,
        "action_sequence_equal": c0.get("actions") == c1.get("actions") if c0 and c1 else None,
        "fixture_outcome_equal": (
            (c0.get("success"), c0.get("stop_reason"))
            == (c1.get("success"), c1.get("stop_reason"))
        )
        if c0 and c1
        else None,
        "adapter_lossless_all": all(
            _adapter_event_is_lossless(event)
            for trace in traces.values()
            for event in trace.get("adapter_events", [])
        ),
        "benchmark_success_claim": False,
    }


def _comparison_fingerprint(
    traces: Dict[str, Dict[str, Any]], comparison: Dict[str, Any]
) -> str:
    canonical = {
        "demo_id": DEMO_ID,
        "seed": DEMO_SEED,
        "comparison": comparison,
        "cells": [
            _stable_trace(traces[name])
            for name in sorted(traces)
        ],
    }
    return _sha256_json(canonical)


def _stable_trace(trace: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "configuration_name": _configuration_for_retriever(trace.get("retriever_name", "")),
        "task_id": trace.get("task_id"),
        "selected_skill_ids": trace.get("selected_skill_ids", []),
        "selected_scores": trace.get("retrieval_response", {}).get("ranked_candidates", []),
        "actions": trace.get("actions", []),
        "rewards": trace.get("rewards", []),
        "success": bool(trace.get("success", False)),
        "stop_reason": trace.get("stop_reason"),
        "adapter_lossless": all(
            _adapter_event_is_lossless(event) for event in trace.get("adapter_events", [])
        ),
        "warning_count": len(trace.get("warnings", [])),
    }


def _adapter_event_is_lossless(event: Dict[str, Any]) -> bool:
    return not any(event.get(field) for field in ("dropped", "approximated", "defaulted"))


def _configuration_for_retriever(retriever_name: str) -> str:
    for configuration_name, retriever_type in CONFIGURATION_TYPES:
        if retriever_name == getattr(retriever_type, "name", None):
            return configuration_name
    return retriever_name


def _check_expected_fingerprint(path: Path, actual: str) -> None:
    expected = path.read_text(encoding="utf-8").strip()
    if not expected:
        raise ValueError(f"Expected fingerprint file is empty: {path}")
    if expected != actual:
        raise AssertionError(
            f"Demo fingerprint mismatch: expected {expected}, generated {actual}. "
            "Update the fixture only after reviewing the trace change."
        )


def _check_expected_summary(path: Path, result: Dict[str, Any]) -> None:
    expected = json.loads(path.read_text(encoding="utf-8"))
    actual = {
        "demo_id": result["demo_id"],
        "task_id": result["task_id"],
        "comparison": result["comparison"],
        "comparison_fingerprint": result["comparison_fingerprint"],
        "benchmark_success_claim": result["benchmark_success_claim"],
        "network_calls": result["network_calls"],
        "model_calls": result["model_calls"],
    }
    if expected != actual:
        raise AssertionError(
            f"Demo expected summary mismatch at {path}. "
            "Update the fixture only after reviewing the trace change."
        )


def _safe_run_id_component(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_.-]+", "-", value).strip("-.")
    return normalized or "demo"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_library(native_skills: List[Dict[str, Any]]) -> str:
    payload = [
        {"skill_id": skill["skill_id"], "native_payload": skill["native_payload"]}
        for skill in native_skills
    ]
    return _sha256_json(payload)


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
