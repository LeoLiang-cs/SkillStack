"""Zero-model M1-M3 harness for the SkillOps maintenance boundary."""

from __future__ import annotations

import hashlib
import importlib
import json
import logging
import shutil
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from skillstack.adapters.grasp_to_skillops import (
    FIDELITY,
    adapt_directory,
    render_grasp_markdown,
)
from skillstack.adapters.skillops_to_grasp import build_id_mapping, export_payloads


EXPECTED_SKILLOPS_COMMIT = "c80b05246369c0b9d82a293390ca5add675c516a"
EXPECTED_GRASP_COMMIT = "9d7d125a3e9b46ed591692475eb07aff4ae67d34"
SOURCE_CANDIDATES = (
    ("a0", "grasp-001", "infer_goal_from_task_instruction"),
    ("a1", "skillrl-001", "use_valid_actions_only"),
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def directory_manifest(path: Path) -> Dict[str, Any]:
    files = []
    digest = hashlib.sha256()
    for item in sorted(p for p in Path(path).rglob("*") if p.is_file()):
        relative = item.relative_to(path).as_posix()
        raw = item.read_bytes()
        file_hash = hashlib.sha256(raw).hexdigest()
        files.append({"path": relative, "sha256": file_hash, "bytes": len(raw)})
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(raw)
        digest.update(b"\0")
    return {"sha256": digest.hexdigest(), "files": files}


def git_commit(path: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def preflight(skillops_root: Path, grasp_root: Path, source_run: Path) -> Dict[str, Any]:
    agentbench_root = grasp_root / "benchmarks" / "AgentBench"
    required = [
        skillops_root / "skillops" / "maintenance.py",
        agentbench_root / "src" / "client" / "agents" / "skill_aware_agent.py",
        agentbench_root / "src" / "skills" / "repository.py",
        agentbench_root / "data" / "alfworld" / "split_val.json",
    ]
    for cell, candidate_id, _ in SOURCE_CANDIDATES:
        required.append(source_run / "cells" / cell / "candidates" / candidate_id / "result.json")
    missing = [str(path) for path in required if not path.is_file()]
    skillops_commit = git_commit(skillops_root) if (skillops_root / ".git").is_dir() else None
    grasp_commit = git_commit(grasp_root) if (grasp_root / ".git").is_dir() else None
    checks = {
        "required_files_present": not missing,
        "skillops_commit_matches": skillops_commit == EXPECTED_SKILLOPS_COMMIT,
        "grasp_commit_matches": grasp_commit == EXPECTED_GRASP_COMMIT,
    }
    return {
        "ready": all(checks.values()),
        "checks": checks,
        "missing": missing,
        "skillops_commit": skillops_commit,
        "grasp_commit": grasp_commit,
        "model_calls_made": False,
        "alfworld_episode_calls": 0,
        "service_checks_required": False,
    }


def build_clean_fixture(source_run: Path, output_dir: Path) -> Dict[str, Any]:
    _replace_directory(output_dir)
    sources = []
    for cell, candidate_id, expected_name in SOURCE_CANDIDATES:
        result_path = source_run / "cells" / cell / "candidates" / candidate_id / "result.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        snapshot = result.get("candidate_fork_snapshot") or []
        if len(snapshot) != 1:
            raise ValueError(f"Expected one learned skill in {result_path}, got {len(snapshot)}")
        fields = dict(snapshot[0])
        if fields.get("name") != expected_name:
            raise ValueError(f"Unexpected candidate name in {result_path}: {fields.get('name')}")
        (output_dir / f"{candidate_id}.md").write_bytes(render_grasp_markdown(fields))
        sources.append(
            {
                "cell": cell,
                "candidate_id": candidate_id,
                "skill_name": expected_name,
                "result_path": str(result_path),
                "result_sha256": sha256_file(result_path),
            }
        )
    return {"sources": sources, "directory": directory_manifest(output_dir)}


def run_m1(clean_dir: Path, output_dir: Path, skillops_root: Path) -> Dict[str, Any]:
    _replace_directory(output_dir)
    payloads = adapt_directory(clean_dir)
    identity_dir = output_dir / "identity_roundtrip"
    export_payloads(payloads, identity_dir)
    before = [deepcopy(item) for item in payloads]
    maintained, sweep_report = run_official_sweep(payloads, skillops_root)
    sweep_dir = output_dir / "clean_sweep"
    export_payloads(maintained, sweep_dir)
    mapping = build_id_mapping(before, maintained)
    source_manifest = directory_manifest(clean_dir)
    identity_manifest = directory_manifest(identity_dir)
    sweep_manifest = directory_manifest(sweep_dir)
    ledger_summaries = [
        item["metadata"]["skillstack_adapter"]["ledger_summary"] for item in before
    ]
    result = {
        "fidelity": FIDELITY,
        "input_skill_count": len(before),
        "identity_roundtrip_byte_identical": source_manifest == identity_manifest,
        "clean_sweep_byte_identical": source_manifest == sweep_manifest,
        "clean_sweep_noop": sweep_report == {
            "merged": 0,
            "retired": 0,
            "repaired": 0,
            "validators_added": 0,
            "adapters_added": 0,
        },
        "required_field_loss": sum(item["required_field_loss"] for item in ledger_summaries),
        "id_mapping": mapping,
        "sweep_report": sweep_report,
        "source_manifest": source_manifest,
        "identity_manifest": identity_manifest,
        "clean_sweep_manifest": sweep_manifest,
        "model_calls_made": False,
        "alfworld_episode_calls": 0,
    }
    result["accepted"] = all(
        [
            result["identity_roundtrip_byte_identical"],
            result["clean_sweep_byte_identical"],
            result["clean_sweep_noop"],
            result["required_field_loss"] == 0,
            all(item["status"] == "retained" for item in mapping),
        ]
    )
    return result


def build_stress_fixture(clean_dir: Path, output_dir: Path) -> Dict[str, Any]:
    _replace_directory(output_dir)
    shutil.copytree(clean_dir, output_dir, dirs_exist_ok=True)
    debt = []
    for source in sorted(output_dir.glob("*.md")):
        parent_id = source.stem
        payload = adapt_directory(source.parent)
        parent_payload = next(item for item in payload if item["skill_id"] == parent_id)
        fields = deepcopy(parent_payload["metadata"]["skillstack_adapter"]["native_fields"])
        clone_id = f"{parent_id}__controlled_clone_01"
        fields["name"] = f"{fields['name']}__controlled_clone_01"
        provenance = deepcopy(fields.get("provenance") or {})
        provenance["skillstack_controlled_debt"] = {
            "kind": "exact_duplicate",
            "parent_skill_id": parent_id,
            "injection_version": 1,
        }
        fields["provenance"] = provenance
        clone_path = output_dir / f"{clone_id}.md"
        clone_path.write_bytes(render_grasp_markdown(fields))
        debt.append(
            {
                "kind": "exact_duplicate",
                "parent_id": parent_id,
                "clone_id": clone_id,
                "expected_survivor": parent_id,
                "behavior_fingerprint": parent_payload["metadata"]["skillstack_adapter"]["behavior_fingerprint"],
            }
        )
    return {"debt": debt, "directory": directory_manifest(output_dir)}


def run_m2(stress_dir: Path, output_dir: Path, skillops_root: Path, debt: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    _replace_directory(output_dir)
    before = adapt_directory(stress_dir)
    maintained, sweep_report = run_official_sweep(before, skillops_root)
    export_payloads(maintained, output_dir / "maintained")
    mapping = build_id_mapping(before, maintained)
    expected_removed = {str(item["clone_id"]) for item in debt}
    actual_removed = {item["input_id"] for item in mapping if item["status"] == "merged"}
    true_positive = len(expected_removed & actual_removed)
    precision = true_positive / len(actual_removed) if actual_removed else 0.0
    recall = true_positive / len(expected_removed) if expected_removed else 0.0
    survivors_correct = all(
        next(item for item in mapping if item["input_id"] == debt_item["clone_id"])["output_id"]
        == debt_item["expected_survivor"]
        for debt_item in debt
    )
    clean_survivor_hashes_unchanged = all(
        sha256_file(stress_dir / f"{item['parent_id']}.md")
        == sha256_file(output_dir / "maintained" / f"{item['parent_id']}.md")
        for item in debt
    )
    result = {
        "fidelity": FIDELITY,
        "input_skill_count": len(before),
        "output_skill_count": len(maintained),
        "expected_removed_ids": sorted(expected_removed),
        "actual_removed_ids": sorted(actual_removed),
        "unexpected_removed_ids": sorted(actual_removed - expected_removed),
        "missed_removed_ids": sorted(expected_removed - actual_removed),
        "merge_precision": precision,
        "merge_recall": recall,
        "survivors_correct": survivors_correct,
        "survivor_bytes_unchanged": clean_survivor_hashes_unchanged,
        "id_mapping": mapping,
        "sweep_report": sweep_report,
        "model_calls_made": False,
        "alfworld_episode_calls": 0,
    }
    result["accepted"] = all(
        [
            precision == 1.0,
            recall == 1.0,
            survivors_correct,
            clean_survivor_hashes_unchanged,
            sweep_report.get("merged") == len(expected_removed),
            not result["unexpected_removed_ids"],
            not result["missed_removed_ids"],
        ]
    )
    return result


def run_official_sweep(payloads: Sequence[Mapping[str, Any]], skillops_root: Path):
    skillops = _load_skillops(skillops_root)
    library = skillops.SkillLibrary(skillops.Skill.from_dict(deepcopy(dict(item))) for item in payloads)
    report = skillops.MaintenanceEngine(library).sweep().to_dict()
    return [skill.to_dict() for skill in library.all()], report


def run_m3(
    grasp_root: Path,
    raw_dir: Path,
    maintained_dir: Path,
    output_dir: Path,
    provider_config_path: Path = Path("configs/llm_backends.json"),
) -> Dict[str, Any]:
    _replace_directory(output_dir)
    agentbench_root = grasp_root / "benchmarks" / "AgentBench"
    selector_path = agentbench_root / "src" / "client" / "agents" / "skill_aware_agent.py"
    repository_path = agentbench_root / "src" / "skills" / "repository.py"
    evaluator_path = agentbench_root / "src" / "server" / "tasks" / "alfworld" / "task.py"
    environment_path = agentbench_root / "src" / "server" / "tasks" / "alfworld" / "environment.py"
    base_dir = agentbench_root / "skills" / "alfworld" / "base"
    split_path = agentbench_root / "data" / "alfworld" / "split_val.json"
    agent_class, repository_class, logger = _load_grasp_host(agentbench_root)
    tasks = json.loads(split_path.read_text(encoding="utf-8"))
    task_ids = [task["id"] for task in tasks]
    if len(task_ids) != 24 or len(task_ids) != len(set(task_ids)):
        raise ValueError("Expected 24 unique val task IDs")
    provider_config = json.loads(Path(provider_config_path).read_text(encoding="utf-8"))
    frozen_backend = provider_config["backends"]["deepseek_v4_flash"]
    library_results = {}
    parity_ok = True
    for label, library_dir in (("raw_stress", raw_dir), ("maintained_stress", maintained_dir)):
        repository = repository_class(base_dir, library_dir)
        skills = [skill for skill in repository.load_all() if skill["name"] != "skeleton"]
        rows = []
        for task in tasks:
            context = str(task["description"])
            native = agent_class._select_skills(skills, context)
            recorded, log_payload = _record_native_selection(agent_class, logger, skills, context)
            native_names = [item["name"] for item in native]
            recorded_names = [item["name"] for item in recorded]
            row_parity = native_names == recorded_names == log_payload["selected"]
            parity_ok = parity_ok and row_parity
            rendered = agent_class._render_skills(recorded)
            rows.append(
                {
                    "task_id": task["id"],
                    "description": context,
                    "native_selected": native_names,
                    "recorded_selected": recorded_names,
                    "logged_selected": log_payload["selected"],
                    "scores": log_payload["scores"],
                    "injected_characters": len(rendered),
                    "injected_utf8_bytes": len(rendered.encode("utf-8")),
                    "parity": row_parity,
                }
            )
        library_results[label] = {
            "skill_count": len(skills),
            "task_count": len(rows),
            "all_recorder_native_parity": all(row["parity"] for row in rows),
            "rows": rows,
        }
    source_hashes = {
        "selector": sha256_file(selector_path),
        "repository": sha256_file(repository_path),
        "alfworld_evaluator_and_task": sha256_file(evaluator_path),
        "alfworld_environment": sha256_file(environment_path),
        "base_skeleton": directory_manifest(base_dir),
        "val_split": sha256_file(split_path),
        "provider_config": sha256_file(provider_config_path),
    }
    result = {
        "host": "unchanged_grasp_skill_aware_agent",
        "skillops_planner_imported": False,
        "skillops_specific_host_branch": False,
        "source_hashes": source_hashes,
        "source_hashes_shared_across_cells": True,
        "frozen_backend_name": "deepseek_v4_flash",
        "frozen_backend": frozen_backend,
        "frozen_backend_defaults": provider_config["defaults"],
        "task_ids": task_ids,
        "task_ids_sha256": hashlib.sha256(
            json.dumps(task_ids, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "task_ids_shared_across_cells": True,
        "selection_recorder_native_parity": parity_ok,
        "libraries": library_results,
        "model_calls_made": False,
        "alfworld_episode_calls": 0,
    }
    result["accepted"] = all(
        [
            parity_ok,
            result["source_hashes_shared_across_cells"],
            result["task_ids_shared_across_cells"],
            not result["skillops_planner_imported"],
            not result["skillops_specific_host_branch"],
            all(item["task_count"] == 24 for item in library_results.values()),
        ]
    )
    return result


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _load_skillops(root: Path):
    root_text = str(Path(root).resolve())
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    return importlib.import_module("skillops")


def _load_grasp_host(agentbench_root: Path):
    root_text = str(Path(agentbench_root).resolve())
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    module = importlib.import_module("src.client.agents.skill_aware_agent")
    repository_module = importlib.import_module("src.skills.repository")
    return module.SkillAwareAgent, repository_module.SkillRepository, module.logger


class _SelectionLogHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.payload: Dict[str, Any] | None = None

    def emit(self, record: logging.LogRecord) -> None:
        if record.msg == "skill_selection selected=%s scores=%s" and isinstance(record.args, tuple):
            self.payload = {"selected": list(record.args[0]), "scores": dict(record.args[1])}


def _record_native_selection(agent_class, logger, skills, context):
    handler = _SelectionLogHandler()
    old_level = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        selected = agent_class._select_skills(skills, context)
    finally:
        logger.removeHandler(handler)
        logger.setLevel(old_level)
    if handler.payload is None:
        raise RuntimeError("Selection recorder did not observe native GRASP log event")
    return selected, handler.payload


def _replace_directory(path: Path) -> None:
    path = Path(path)
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
