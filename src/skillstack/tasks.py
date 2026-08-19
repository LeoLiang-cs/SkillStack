"""Read the fixed P0.0 task and recorded-action manifests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from skillstack.contracts import TASK_RECORD_FIELDS, require_fields


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TASK_MANIFEST = REPOSITORY_ROOT / "configs" / "p0_tasks.json"
DEFAULT_RECORDED_ACTIONS = REPOSITORY_ROOT / "configs" / "p0_recorded_actions.json"


def load_task_manifest(
    manifest_path: Optional[Path] = None, exact_count: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Load and validate a frozen task manifest.

    ``exact_count`` enforces a fixed task count when the manifest's contract
    requires it (the P0.0 manifest requires five).
    """

    path = (manifest_path or DEFAULT_TASK_MANIFEST).resolve()
    manifest = json.loads(path.read_text(encoding="utf-8"))
    tasks = manifest["tasks"]
    if exact_count is not None and len(tasks) != exact_count:
        raise ValueError(f"Expected {exact_count} tasks, found {len(tasks)}")
    for task in tasks:
        require_fields(task, TASK_RECORD_FIELDS, "task record")
    task_ids = [task["task_id"] for task in tasks]
    if len(task_ids) != len(set(task_ids)):
        raise ValueError("Task manifest contains duplicate task IDs")
    return tasks


def load_p0_tasks(manifest_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load and validate the five immutable P0.0 task records."""

    return load_task_manifest(manifest_path, exact_count=5)


def find_task(task_id: str, manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """Return one fixed task by its stable task identifier."""

    for task in load_p0_tasks(manifest_path):
        if task["task_id"] == task_id:
            return task
    raise KeyError(f"Unknown P0.0 task ID: {task_id}")


def load_recorded_actions(
    task_id: str, fixture_path: Optional[Path] = None
) -> List[str]:
    """Load an explicitly labelled deterministic action fixture for one task."""

    path = (fixture_path or DEFAULT_RECORDED_ACTIONS).resolve()
    fixture = json.loads(path.read_text(encoding="utf-8"))
    actions = fixture["actions_by_task_id"].get(task_id)
    if actions is None:
        raise KeyError(f"No recorded action fixture for task ID: {task_id}")
    if not all(isinstance(action, str) for action in actions):
        raise ValueError(f"Recorded action fixture for {task_id} must be strings")
    return actions

