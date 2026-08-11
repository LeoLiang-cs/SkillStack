"""Load P0.0's native-text static ALFWorld skill artifacts."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from skillstack.contracts import NATIVE_SKILL_FIELDS, require_fields


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LIBRARY_PATH = REPOSITORY_ROOT / "skills" / "alfworld_static"
TASK_FAMILY_PATTERN = re.compile(r"^\*\*Task family:\*\*\s+`([^`]+)`\s*$", re.MULTILINE)


def load_static_library(library_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Return sorted, lossless native artifacts from the P0.0 static library."""

    root = (library_path or DEFAULT_LIBRARY_PATH).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Static skill library does not exist: {root}")

    artifacts: List[Dict[str, Any]] = []
    for path in sorted(root.glob("skill_*.md")):
        native_payload = path.read_text(encoding="utf-8")
        task_family = _extract_task_family(path, native_payload)
        try:
            source_path = str(path.relative_to(REPOSITORY_ROOT))
        except ValueError:
            source_path = str(path)
        artifact: Dict[str, Any] = {
            "skill_id": path.stem,
            "source_path": source_path,
            "native_payload": native_payload,
            "local_metadata": {"task_family": task_family},
        }
        require_fields(artifact, NATIVE_SKILL_FIELDS, f"native skill artifact {path.name}")
        artifacts.append(artifact)

    if not artifacts:
        raise ValueError(f"No skill_*.md artifacts found in {root}")
    _ensure_unique_skill_ids(artifacts)
    return artifacts


def _extract_task_family(path: Path, native_payload: str) -> str:
    match = TASK_FAMILY_PATTERN.search(native_payload)
    if not match:
        raise ValueError(f"{path} does not declare a '**Task family:** `...`' line")
    return match.group(1)


def _ensure_unique_skill_ids(artifacts: List[Dict[str, Any]]) -> None:
    skill_ids = [artifact["skill_id"] for artifact in artifacts]
    duplicates = sorted({skill_id for skill_id in skill_ids if skill_ids.count(skill_id) > 1})
    if duplicates:
        raise ValueError(f"Duplicate skill IDs: {', '.join(duplicates)}")

