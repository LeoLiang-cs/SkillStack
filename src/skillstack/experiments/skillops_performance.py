"""M4 AgentBench evaluation for raw versus SkillOps-maintained libraries."""

from __future__ import annotations

import hashlib
import importlib
import json
import logging
import os
import random
import shutil
import socket
import subprocess
import sys
import time
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from skillstack.experiments.agentbench_performance import (
    atomic_write_json,
    checkpoint_name,
    json_safe,
    read_json,
    sanitize_tool_history,
)
from skillstack.experiments.grasp_source import EXPECTED_GRASP_COMMIT
from skillstack.llm import LlmClient, load_backends


BACKEND_NAME = "deepseek_v4_flash"
CELLS = ("raw_stress", "maintained_stress")
ALLOWED_VAL_SEEDS = (42, 7, 123)


class RecordingAgent:
    """AgentBench-compatible model client retaining every raw call and cost."""

    def __init__(self, client: LlmClient, *, max_tokens: int = 512, temperature: float = 0.0):
        self.client = client
        self.model_name = client.backend.model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._calls: List[Dict[str, Any]] = []
        self._lock = Lock()

    def inference(self, history, tools=None):
        raw_messages = [_message_dict(message) for message in history]
        messages, sanitization_events = sanitize_tool_history(raw_messages)
        response = self.client.chat(
            messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            tools=json_safe(tools) if tools else None,
        )
        record = {
            "request": {
                "messages": deepcopy(messages),
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "tools": json_safe(tools) if tools else None,
                "history_sanitization": sanitization_events,
            },
            "raw_content": response["content"],
            "raw_message": deepcopy(response["message"]),
            "usage": deepcopy(response["usage"]),
            "latency_seconds": response["latency_seconds"],
            "estimated_cost_usd": self.client.estimate_cost_usd(response["usage"]),
        }
        with self._lock:
            self._calls.append(record)
        if response["message"].get("tool_calls"):
            return response["message"]
        return response["content"]

    def drain_calls(self) -> List[Dict[str, Any]]:
        with self._lock:
            calls = self._calls
            self._calls = []
        return calls


class SelectionLogHandler(logging.Handler):
    """Observe native GRASP selector logs without changing selection logic."""

    def __init__(self) -> None:
        super().__init__()
        self.events: List[Dict[str, Any]] = []

    def emit(self, record: logging.LogRecord) -> None:
        if record.msg == "skill_selection selected=%s scores=%s" and isinstance(record.args, tuple):
            self.events.append(
                {"selected": list(record.args[0]), "scores": dict(record.args[1])}
            )


def parse_csv(value: str) -> List[str]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items or len(items) != len(set(items)):
        raise ValueError(f"Expected non-empty unique comma-separated values: {value!r}")
    return items


def parse_seeds(value: str) -> List[int]:
    try:
        seeds = [int(item) for item in parse_csv(value)]
    except ValueError as error:
        raise ValueError(f"Invalid replicate seeds: {value!r}") from error
    return seeds


def performance_preflight(
    *,
    grasp_root: Path,
    controller_address: str,
    backend_name: str,
    split: str,
    m1_m3_root: Path,
) -> Dict[str, Any]:
    split_path = _agentbench_root(grasp_root) / "data" / "alfworld" / f"split_{split}.json"
    tasks = _load_tasks(split_path)
    backend = load_backends()[backend_name]
    m1_m3_summary_path = Path(m1_m3_root) / "summary.json"
    m1_m3_summary = read_json(m1_m3_summary_path) if m1_m3_summary_path.is_file() else {}
    library_paths = _library_paths(m1_m3_root)
    commits_match = _git_commit(grasp_root) == EXPECTED_GRASP_COMMIT
    api_key_present = bool(os.environ.get(backend.api_key_env))
    docker = _command_status(["docker", "info", "--format", "{{.ServerVersion}}"])
    ports = {str(port): _tcp_open("127.0.0.1", port) for port in (5060, 5061)}
    service: Dict[str, Any] = {"checked": False, "reachable": False}
    if ports["5060"]:
        try:
            native = native_modules(grasp_root)
            task_client = native["TaskClient"](
                name="alfworld-skill", controller_address=controller_address
            )
            available = {int(item) for item in task_client.get_indices()}
            required = {int(task["id"]) for task in tasks}
            missing = sorted(required - available)
            service = {
                "checked": True,
                "reachable": True,
                "index_count": len(available),
                "required_task_count": len(required),
                "missing_required_ids": missing,
                "required_ids_available": not missing,
                "available_concurrency": task_client.get_concurrency(),
            }
        except Exception as error:
            service = {
                "checked": True,
                "reachable": False,
                "error_type": type(error).__name__,
                "error": str(error),
            }
    libraries_ready = all(path.is_dir() and list(path.glob("*.md")) for path in library_paths.values())
    checks = {
        "grasp_commit_matches": commits_match,
        "m1_m3_accepted": m1_m3_summary.get("status") == "m1_m3_accepted",
        "libraries_ready": libraries_ready,
        "api_key_present": api_key_present,
        "docker_ready": docker["ok"],
        "controller_port_ready": ports["5060"],
        "worker_port_ready": ports["5061"],
        "service_reachable": service.get("reachable", False),
        "required_ids_available": service.get("required_ids_available", False),
        "worker_capacity_available": int(service.get("available_concurrency", 0)) > 0,
    }
    return {
        "ready": all(checks.values()),
        "checks": checks,
        "backend": backend_name,
        "model": backend.model,
        "api_key_env": backend.api_key_env,
        "split": split,
        "task_count": len(tasks),
        "task_ids": [task["id"] for task in tasks],
        "grasp_commit": _git_commit(grasp_root),
        "m1_m3_summary": m1_m3_summary,
        "library_paths": {key: str(value) for key, value in library_paths.items()},
        "library_hashes": {key: directory_hash(value) for key, value in library_paths.items()},
        "docker": docker,
        "ports": ports,
        "agentbench_service": service,
        "model_calls_made": False,
        "alfworld_episode_calls": 0,
    }


def evaluate(
    *,
    grasp_root: Path,
    controller_address: str,
    backend_name: str,
    split: str,
    cells: Sequence[str],
    seeds: Sequence[int],
    m1_m3_root: Path,
    run_dir: Path,
    resume: bool,
    preflight: Mapping[str, Any],
) -> Dict[str, Any]:
    if backend_name != BACKEND_NAME:
        raise ValueError(f"M4 is frozen to backend {BACKEND_NAME}")
    if split != "val" or set(cells) != set(CELLS):
        raise ValueError("M4-M5 are frozen to val and cells raw_stress+maintained_stress")
    if not seeds or any(seed not in ALLOWED_VAL_SEEDS for seed in seeds):
        raise ValueError(f"Allowed val replicate seeds are {ALLOWED_VAL_SEEDS}")
    run_dir = Path(run_dir)
    manifest_path = run_dir / "run_manifest.json"
    if run_dir.exists() and not resume:
        raise ValueError(f"Run directory exists; use --resume: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=True)
    tasks = _load_tasks(_agentbench_root(grasp_root) / "data" / "alfworld" / "split_val.json")
    source_libraries = _library_paths(m1_m3_root)
    frozen = {
        "experiment_id": "w6_skillops_m4_val_pilot",
        "phase": "M4",
        "split": split,
        "cells": list(cells),
        "replicate_seeds": list(seeds),
        "backend": backend_name,
        "model": load_backends()[backend_name].model,
        "controller_address": controller_address,
        "grasp_commit": _git_commit(grasp_root),
        "task_ids": [task["id"] for task in tasks],
        "source_library_hashes": {
            cell: directory_hash(source_libraries[cell]) for cell in cells
        },
        "m1_m3_summary_sha256": sha256_file(Path(m1_m3_root) / "summary.json"),
        "provider_fidelity": "deepseek_v4_flash_execution_backend",
        "maintenance_fidelity": "source_variant_opaque_contract",
        "preflight": dict(preflight),
    }
    if manifest_path.exists():
        saved = read_json(manifest_path)
        for key in (
            "experiment_id", "split", "cells", "backend",
            "controller_address", "grasp_commit", "task_ids", "source_library_hashes",
        ):
            if saved.get(key) != frozen.get(key):
                raise ValueError(f"Resume manifest mismatch for {key}")
        saved_seeds = [int(seed) for seed in saved.get("replicate_seeds", [])]
        combined_seeds = saved_seeds + [seed for seed in seeds if seed not in saved_seeds]
        if any(seed not in ALLOWED_VAL_SEEDS for seed in combined_seeds):
            raise ValueError("Resume manifest contains an unapproved replicate seed")
        if combined_seeds != saved_seeds:
            saved["replicate_seeds"] = combined_seeds
            saved["seed_scope"] = "task_order_only_provider_seed_not_set"
            saved["updated_at_utc"] = now()
            atomic_write_json(manifest_path, saved)
    else:
        frozen["created_at_utc"] = now()
        frozen["seed_scope"] = "task_order_only_provider_seed_not_set"
        atomic_write_json(manifest_path, frozen)

    native = native_modules(grasp_root)
    backend = load_backends()[backend_name]
    all_cell_summaries = []
    for cell in cells:
        source_library = source_libraries[cell]
        for seed in seeds:
            cell_dir = run_dir / "cells" / cell / f"seed_{seed}"
            learned_dir = cell_dir / "library" / "learned"
            _prepare_library_copy(source_library, learned_dir, resume=resume)
            if directory_hash(learned_dir) != directory_hash(source_library):
                raise RuntimeError(f"Isolated library drift for {cell}/seed_{seed}")
            repository = native["SkillRepository"](
                base_dir=_agentbench_root(grasp_root) / "skills" / "alfworld" / "base",
                learned_dir=learned_dir,
            )
            agent = RecordingAgent(LlmClient(backend), max_tokens=512, temperature=0.0)
            task_client = native["TaskClient"](
                name="alfworld-skill", controller_address=controller_address
            )
            ordered_tasks = _ordered_tasks(tasks, seed)
            payloads = []
            for position, task in enumerate(ordered_tasks, start=1):
                checkpoint = cell_dir / "episodes" / (
                    f"{position:02d}_{checkpoint_name(str(task['id']))}.json"
                )
                payload = _run_checkpoint(
                    checkpoint=checkpoint,
                    task=task,
                    repository=repository,
                    agent=agent,
                    task_client=task_client,
                    native=native,
                    resume=resume,
                    cell=cell,
                    seed=seed,
                )
                payloads.append(payload)
                print(
                    f"[{cell}/seed_{seed} {position}/{len(ordered_tasks)}] "
                    f"task={task['id']} correct={payload['entry']['is_correct']}"
                )
            summary = summarize_cell(cell, seed, payloads, source_library)
            atomic_write_json(cell_dir / "summary.json", summary)
            all_cell_summaries.append(summary)
    complete_summaries = _load_all_cell_summaries(run_dir)
    manifest_seeds = read_json(manifest_path)["replicate_seeds"]
    result = summarize_run(complete_summaries, tasks, cells, manifest_seeds)
    atomic_write_json(run_dir / "summary.json", result)
    return result


def compare(run_dir: Path) -> Dict[str, Any]:
    run_dir = Path(run_dir)
    manifest = read_json(run_dir / "run_manifest.json")
    expected = {str(item) for item in manifest["task_ids"]}
    pairs = []
    per_seed = []
    for seed in manifest["replicate_seeds"]:
        raw_rows = _load_episode_payloads(
            run_dir / "cells" / "raw_stress" / f"seed_{seed}" / "episodes"
        )
        maintained_rows = _load_episode_payloads(
            run_dir / "cells" / "maintained_stress" / f"seed_{seed}" / "episodes"
        )
        raw = {str(item["entry"]["sample_id"]): item for item in raw_rows}
        maintained = {str(item["entry"]["sample_id"]): item for item in maintained_rows}
        if set(raw) != expected or set(maintained) != expected:
            raise ValueError(f"Cannot compare incomplete or mismatched seed {seed} checkpoints")
        seed_pairs = []
        for task_id in sorted(expected, key=int):
            raw_ok = bool(raw[task_id]["entry"]["is_correct"])
            maintained_ok = bool(maintained[task_id]["entry"]["is_correct"])
            seed_pairs.append(
                {
                    "replicate_seed": int(seed),
                    "task_id": int(task_id),
                    "raw_success": raw_ok,
                    "maintained_success": maintained_ok,
                    "difference": int(maintained_ok) - int(raw_ok),
                }
            )
        pairs.extend(seed_pairs)
        per_seed.append(_paired_counts(seed_pairs, int(seed)))
    ci_low, ci_high = bootstrap_mean_ci(
        [int(item["difference"]) for item in pairs], iterations=10000, seed=20260903
    )
    result = {
        "status": "complete",
        "experiment_id": manifest["experiment_id"],
        "split": "val",
        "replicate_seeds": manifest["replicate_seeds"],
        "seed_scope": manifest.get("seed_scope") or "task_order_only_provider_seed_not_set",
        "pair_count": len(pairs),
        "raw_correct": sum(item["raw_success"] for item in pairs),
        "maintained_correct": sum(item["maintained_success"] for item in pairs),
        "maintained_minus_raw": sum(item["difference"] for item in pairs),
        "fixes": sum(item["difference"] == 1 for item in pairs),
        "regressions": sum(item["difference"] == -1 for item in pairs),
        "ties": sum(item["difference"] == 0 for item in pairs),
        "mean_paired_difference": sum(item["difference"] for item in pairs) / len(pairs),
        "bootstrap_95_ci": [ci_low, ci_high],
        "bootstrap_unit": "task_x_replicate_pair",
        "per_seed": per_seed,
        "pairs": pairs,
        "interpretation_boundary": (
            "Val comparison under controlled exact-duplicate debt. Replicate seed controls "
            "task order only; no provider seed is set. This is not general SkillOps superiority."
        ),
        "completed_at_utc": now(),
    }
    atomic_write_json(run_dir / "paired_summary.json", result)
    return result


def bootstrap_mean_ci(
    differences: Sequence[int], *, iterations: int, seed: int
) -> tuple:
    if not differences or iterations < 1:
        raise ValueError("Bootstrap requires differences and positive iterations")
    rng = random.Random(seed)
    count = len(differences)
    estimates = []
    for _ in range(iterations):
        estimates.append(sum(differences[rng.randrange(count)] for _ in range(count)) / count)
    estimates.sort()
    low_index = int(0.025 * (iterations - 1))
    high_index = int(0.975 * (iterations - 1))
    return estimates[low_index], estimates[high_index]


def _paired_counts(pairs: Sequence[Mapping[str, Any]], seed: int) -> Dict[str, Any]:
    return {
        "replicate_seed": seed,
        "pair_count": len(pairs),
        "raw_correct": sum(bool(item["raw_success"]) for item in pairs),
        "maintained_correct": sum(bool(item["maintained_success"]) for item in pairs),
        "maintained_minus_raw": sum(int(item["difference"]) for item in pairs),
        "fixes": sum(int(item["difference"]) == 1 for item in pairs),
        "regressions": sum(int(item["difference"]) == -1 for item in pairs),
    }


def summarize_cell(
    cell: str, seed: int, payloads: Sequence[Mapping[str, Any]], source_library: Path
) -> Dict[str, Any]:
    calls = [call for payload in payloads for call in payload.get("model_calls", [])]
    errors = sum(bool(payload["entry"].get("error")) for payload in payloads)
    return {
        "status": "complete" if len(payloads) == 24 and errors == 0 else "incomplete",
        "cell": cell,
        "replicate_seed": seed,
        "total": len(payloads),
        "correct": sum(bool(payload["entry"]["is_correct"]) for payload in payloads),
        "errors": errors,
        "task_ids": [payload["entry"]["sample_id"] for payload in payloads],
        "selection_event_count": sum(len(payload.get("selection_events", [])) for payload in payloads),
        "orphan_tool_messages_removed": sum(
            len(call.get("request", {}).get("history_sanitization", [])) for call in calls
        ),
        "accounting": accounting(calls),
        "library_sha256": directory_hash(source_library),
        "completed_at_utc": now(),
    }


def summarize_run(
    summaries: Sequence[Mapping[str, Any]],
    tasks: Sequence[Mapping[str, Any]],
    cells: Sequence[str],
    seeds: Sequence[int],
) -> Dict[str, Any]:
    expected = len(tasks) * len(cells) * len(seeds)
    actual = sum(int(item["total"]) for item in summaries)
    errors = sum(int(item["errors"]) for item in summaries)
    return {
        "status": "complete" if actual == expected and errors == 0 else "incomplete",
        "declared_episode_count": expected,
        "completed_episode_count": actual,
        "formal_episode_errors": errors,
        "cells": list(summaries),
        "accounting": merge_accountings(item["accounting"] for item in summaries),
        "completed_at_utc": now(),
    }


def native_modules(grasp_root: Path) -> Dict[str, Any]:
    agentbench = _agentbench_root(grasp_root)
    if str(agentbench) not in sys.path:
        sys.path.insert(0, str(agentbench))
    cycle = importlib.import_module("src.skills.cycle")
    task = importlib.import_module("src.client.task")
    agent_module = importlib.import_module("src.client.agents.skill_aware_agent")
    return {
        "SkillRepository": importlib.import_module("src.skills.repository").SkillRepository,
        "SkillAwareAgent": agent_module.SkillAwareAgent,
        "selection_logger": agent_module.logger,
        "TaskClient": task.TaskClient,
        "TaskError": task.TaskError,
        "score_result": cycle._score_result,
        "make_log_entry": cycle._make_log_entry,
        "eval_fn": cycle._load_eval_fn({"eval": {"module": "src.server.tasks.alfworld.eval"}}),
    }


def accounting(calls: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    materialized = list(calls)
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "cached_prompt_tokens": 0}
    for call in materialized:
        for key in usage:
            usage[key] += int((call.get("usage") or {}).get(key, 0))
    return {
        "call_count": len(materialized),
        "usage": usage,
        "latency_seconds": round(sum(float(call.get("latency_seconds", 0)) for call in materialized), 3),
        "estimated_cost_usd": round(sum(float(call.get("estimated_cost_usd", 0)) for call in materialized), 8),
    }


def merge_accountings(items: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    result = {
        "call_count": 0,
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "cached_prompt_tokens": 0},
        "latency_seconds": 0.0,
        "estimated_cost_usd": 0.0,
    }
    for item in items:
        result["call_count"] += int(item.get("call_count", 0))
        for key in result["usage"]:
            result["usage"][key] += int((item.get("usage") or {}).get(key, 0))
        result["latency_seconds"] += float(item.get("latency_seconds", 0))
        result["estimated_cost_usd"] += float(item.get("estimated_cost_usd", 0))
    result["latency_seconds"] = round(result["latency_seconds"], 3)
    result["estimated_cost_usd"] = round(result["estimated_cost_usd"], 8)
    return result


def directory_hash(directory: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(Path(directory).rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(directory).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_checkpoint(
    *, checkpoint, task, repository, agent, task_client, native, resume, cell, seed
):
    if checkpoint.exists():
        if not resume:
            raise ValueError(f"Checkpoint exists; use --resume: {checkpoint}")
        return read_json(checkpoint)
    handler = SelectionLogHandler()
    logger = native["selection_logger"]
    previous_level = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    attempt = 0
    try:
        while True:
            result = task_client.run_sample(
                task["id"], native["SkillAwareAgent"](agent, repository)
            )
            if result.error != native["TaskError"].NOT_AVAILABLE.value:
                break
            wait_seconds = min(5 * (attempt + 1), 30)
            time.sleep(wait_seconds)
            attempt += 1
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)
    is_correct = native["score_result"](task, result, native["eval_fn"])
    entry = native["make_log_entry"](
        task, result, is_correct, update_cycle=0, skill_snapshot=repository.snapshot()
    )
    calls = agent.drain_calls()
    skill_by_name = {item["name"]: item for item in repository.load_all()}
    for event in handler.events:
        selected = [skill_by_name[name] for name in event["selected"] if name in skill_by_name]
        rendered = native["SkillAwareAgent"]._render_skills(selected)
        event["injected_characters"] = len(rendered)
        event["injected_utf8_bytes"] = len(rendered.encode("utf-8"))
    payload = {
        "cell": cell,
        "replicate_seed": seed,
        "task": task,
        "entry": entry,
        "selection_events": handler.events,
        "model_calls": calls,
        "accounting": accounting(calls),
        "completed_at_utc": now(),
    }
    if result.error:
        failed = checkpoint.parent / ".failed" / (
            checkpoint.stem + "_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json"
        )
        atomic_write_json(failed, payload)
        raise RuntimeError(
            f"Task {task['id']} ended with {result.error}; diagnostic saved to {failed}"
        )
    atomic_write_json(checkpoint, payload)
    return read_json(checkpoint)


def _ordered_tasks(tasks: Sequence[Mapping[str, Any]], seed: int) -> List[Dict[str, Any]]:
    ordered = [deepcopy(dict(item)) for item in tasks]
    random.Random(seed).shuffle(ordered)
    return ordered


def _load_tasks(path: Path) -> List[Dict[str, Any]]:
    tasks = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(tasks, list) or len(tasks) != 24:
        raise ValueError(f"Expected 24 val tasks in {path}")
    ids = [int(item["id"]) for item in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate task IDs in {path}")
    return [dict(item) for item in tasks]


def _library_paths(root: Path) -> Dict[str, Path]:
    root = Path(root)
    return {
        "raw_stress": root / "libraries" / "l_stress",
        "maintained_stress": root / "m2" / "maintained",
    }


def _prepare_library_copy(source: Path, target: Path, *, resume: bool) -> None:
    if target.exists():
        if not resume:
            raise ValueError(f"Library copy exists; use --resume: {target}")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)


def _load_episode_payloads(path: Path) -> List[Dict[str, Any]]:
    files = sorted(Path(path).glob("*.json"))
    return [read_json(item) for item in files]


def _load_all_cell_summaries(run_dir: Path) -> List[Dict[str, Any]]:
    return [
        read_json(path)
        for path in sorted((Path(run_dir) / "cells").glob("*/seed_*/summary.json"))
    ]


def _message_dict(message: Any) -> Dict[str, Any]:
    if isinstance(message, Mapping):
        return json_safe(message)
    if hasattr(message, "model_dump"):
        return json_safe(message.model_dump(mode="json"))
    if hasattr(message, "dict"):
        return json_safe(message.dict())
    return json_safe(vars(message))


def _agentbench_root(grasp_root: Path) -> Path:
    return Path(grasp_root).resolve() / "benchmarks" / "AgentBench"


def _git_commit(root: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(Path(root).resolve()), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _command_status(command: Sequence[str]) -> Dict[str, Any]:
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=10)
    except Exception as error:
        return {"ok": False, "error_type": type(error).__name__, "error": str(error)}
    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip()[:500],
    }


def _tcp_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False
