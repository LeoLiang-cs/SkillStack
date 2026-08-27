"""Pinned SkillRL updater instrumentation that preserves raw request/response evidence."""

from __future__ import annotations

import hashlib
import importlib.util
import os
import subprocess
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Mapping


EXPECTED_SKILLRL_COMMIT = "8e66726ed866a4e0a7f053586a41022798192e6c"
UPDATER_RELATIVE = Path("agent_system/memory/skill_updater.py")


def prepare_skillrl_request(
    skillrl_root: Path,
    failed_trajectories: list,
    current_skills: Mapping[str, Any],
) -> Dict[str, Any]:
    """Build the exact released prompt without constructing a network client."""

    root, module = _load_pinned_module(skillrl_root)
    updater = module.SkillUpdater.__new__(module.SkillUpdater)
    updater.max_new_skills_per_update = 3
    updater.max_completion_tokens = 2048
    next_dyn_index = updater._next_dyn_index(current_skills)
    prompt = updater._build_analysis_prompt(
        deepcopy(failed_trajectories), deepcopy(dict(current_skills)), next_dyn_index
    )
    source_path = root / UPDATER_RELATIVE
    return {
        "source_commit": EXPECTED_SKILLRL_COMMIT,
        "source_path": str(source_path),
        "source_sha256": _sha256_bytes(source_path.read_bytes()),
        "model": "o3",
        "max_completion_tokens": 2048,
        "max_new_skills_per_update": 3,
        "next_dyn_index": next_dyn_index,
        "failed_trajectories": deepcopy(failed_trajectories),
        "current_skills": deepcopy(dict(current_skills)),
        "prompt": prompt,
        "prompt_sha256": _sha256_bytes(prompt.encode("utf-8")),
    }


def run_released_skillrl_once(
    skillrl_root: Path,
    failed_trajectories: list,
    current_skills: Mapping[str, Any],
) -> Dict[str, Any]:
    """Attempt one released call, retaining credential blocks and raw API evidence."""

    prepared = prepare_skillrl_request(skillrl_root, failed_trajectories, current_skills)
    _, module = _load_pinned_module(skillrl_root)
    credentials = credential_status()
    if not credentials["ready"]:
        try:
            module.SkillUpdater(max_new_skills_per_update=3, max_completion_tokens=2048)
        except Exception as error:
            constructor_error = {
                "type": type(error).__name__,
                "message": str(error),
            }
        else:
            constructor_error = None
        return {
            "status": "blocked_credentials",
            "call_executed": False,
            "credential_status": credentials,
            "prepared_request": prepared,
            "constructor_error": constructor_error,
            "native_return": None,
            "raw_api_request": None,
            "raw_api_response": None,
            "api_error": None,
        }

    updater = module.SkillUpdater(max_new_skills_per_update=3, max_completion_tokens=2048)
    recorder = _CompletionRecorder(updater.client.chat.completions)
    updater.client = SimpleNamespace(
        chat=SimpleNamespace(completions=recorder)
    )
    native_return = updater.analyze_failures(
        deepcopy(failed_trajectories), deepcopy(dict(current_skills))
    )
    status = "completed" if recorder.error is None else "api_error_returned_empty"
    return {
        "status": status,
        "call_executed": True,
        "credential_status": credentials,
        "prepared_request": prepared,
        "constructor_error": None,
        "native_return": deepcopy(native_return),
        "raw_api_request": deepcopy(recorder.request),
        "raw_api_response": deepcopy(recorder.response),
        "api_error": deepcopy(recorder.error),
        "update_history": deepcopy(updater.update_history),
    }


def parse_substituted_skillrl_response(
    skillrl_root: Path,
    raw_content: str,
    current_skills: Mapping[str, Any],
) -> Dict[str, Any]:
    """Use released SkillRL parsing and ID reassignment on a substituted writer output."""

    _, module = _load_pinned_module(skillrl_root)
    updater = module.SkillUpdater.__new__(module.SkillUpdater)
    updater.max_new_skills_per_update = 3
    next_dyn_index = updater._next_dyn_index(current_skills)
    parsed = updater._parse_skills_response(raw_content)
    reassigned = updater._reassign_dyn_ids(parsed, next_dyn_index)
    return {
        "raw_parsed_candidates": deepcopy(parsed),
        "native_return": deepcopy(reassigned[:3]),
        "next_dyn_index": next_dyn_index,
        "parse_status": "valid" if reassigned else "empty_or_parse_error",
    }


def credential_status() -> Dict[str, Any]:
    """Report presence only; never expose credential values or endpoint text."""

    key_present = bool(os.environ.get("AZURE_OPENAI_API_KEY"))
    endpoint_present = bool(os.environ.get("AZURE_OPENAI_ENDPOINT"))
    version_present = bool(os.environ.get("AZURE_OPENAI_API_VERSION"))
    return {
        "azure_api_key_present": key_present,
        "azure_endpoint_present": endpoint_present,
        "azure_api_version_present": version_present,
        "uses_default_api_version": not version_present,
        "ready": key_present and endpoint_present,
    }


class _CompletionRecorder:
    def __init__(self, completions: Any) -> None:
        self.completions = completions
        self.request = None
        self.response = None
        self.error = None

    def create(self, **kwargs: Any) -> Any:
        self.request = _safe_payload(kwargs)
        try:
            response = self.completions.create(**kwargs)
        except Exception as error:
            self.error = {"type": type(error).__name__, "message": str(error)}
            raise
        self.response = _safe_payload(response)
        return response


def _load_pinned_module(skillrl_root: Path) -> tuple:
    root = skillrl_root.resolve()
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    if commit != EXPECTED_SKILLRL_COMMIT:
        raise ValueError(
            f"SkillRL commit mismatch: expected {EXPECTED_SKILLRL_COMMIT}, received {commit}"
        )
    path = root / UPDATER_RELATIVE
    spec = importlib.util.spec_from_file_location("skillstack_pinned_skillrl_updater", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load SkillRL updater: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return root, module


def _safe_payload(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _safe_payload(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe_payload(item) for item in value]
    if hasattr(value, "model_dump"):
        return _safe_payload(value.model_dump(mode="json"))
    return repr(value)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
