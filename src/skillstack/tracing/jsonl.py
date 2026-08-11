"""Append-only JSONL storage for reproducible P0.0 raw episode traces."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


RUN_ID_PATTERN = re.compile(r"[^a-zA-Z0-9_.-]+")


class JsonlTraceWriter:
    """Create one immutable run directory and append structured episode traces."""

    def __init__(self, output_root: Path, label: str, run_id: Optional[str] = None) -> None:
        self.output_root = output_root.resolve()
        self.output_root.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id or _make_run_id(label)
        self.run_dir = self.output_root / self.run_id
        self.run_dir.mkdir(exist_ok=False)
        self.episodes_path = self.run_dir / "episodes.jsonl"

    def write_manifest(self, manifest: Dict[str, Any]) -> Path:
        """Write the effective configuration once; never overwrite it."""

        path = self.run_dir / "run_manifest.json"
        if path.exists():
            raise FileExistsError(f"Run manifest already exists: {path}")
        self._write_json(path, manifest)
        return path

    def append_episode(self, trace: Dict[str, Any]) -> Path:
        """Append a complete episode trace as exactly one JSONL line."""

        required = ("run_id", "episode_id", "task_id", "retriever_name", "executor_name")
        missing = [field for field in required if field not in trace]
        if missing:
            raise ValueError(f"Episode trace is missing fields: {', '.join(missing)}")
        if trace["run_id"] != self.run_id:
            raise ValueError("Episode trace run_id does not match this writer")
        with self.episodes_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(trace, ensure_ascii=False, sort_keys=True) + "\n")
        return self.episodes_path

    def write_summary(self, summary: Dict[str, Any]) -> Path:
        """Write a one-time run summary after all episodes have completed."""

        path = self.run_dir / "summary.json"
        if path.exists():
            raise FileExistsError(f"Run summary already exists: {path}")
        self._write_json(path, summary)
        return path

    @staticmethod
    def _write_json(path: Path, payload: Dict[str, Any]) -> None:
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _make_run_id(label: str) -> str:
    normalized_label = RUN_ID_PATTERN.sub("-", label).strip("-.") or "run"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{timestamp}_{normalized_label}"

