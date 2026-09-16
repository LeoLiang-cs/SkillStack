"""Append-only JSONL storage for reproducible P0.0 raw episode traces."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


RUN_ID_PATTERN = re.compile(r"[^a-zA-Z0-9_.-]+")
RUN_MANIFEST_SCHEMA = "skillstack-run-manifest-v1"
EPISODE_TRACE_SCHEMA = "skillstack-episode-trace-v1"
STATUS_KEYS = (
    "planned",
    "started",
    "completed",
    "valid",
    "success",
    "task_failure",
    "error",
    "timeout",
    "cancelled",
    "invalid",
    "abstained",
    "skipped",
)


class JsonlTraceWriter:
    """Create one immutable run directory and append structured episode traces."""

    def __init__(
        self, output_root: Path, label: str, run_id: Optional[str] = None
    ) -> None:
        self.output_root = output_root.resolve()
        self.output_root.mkdir(parents=True, exist_ok=True)
        self.run_id = _normalize_run_id(run_id or _make_run_id(label))
        self.run_dir = self.output_root / self.run_id
        _ensure_contained(self.output_root, self.run_dir)
        self.run_dir.mkdir(exist_ok=False)
        self.episodes_path = self.run_dir / "episodes.jsonl"
        self.manifest: Optional[Dict[str, Any]] = None

    @classmethod
    def resume(
        cls,
        output_root: Path,
        run_id: str,
        expected_manifest: Optional[Dict[str, Any]] = None,
    ) -> "JsonlTraceWriter":
        """Re-open one existing run after checking its immutable identity."""

        writer = cls.__new__(cls)
        writer.output_root = output_root.expanduser().resolve()
        writer.run_id = _normalize_run_id(run_id)
        writer.run_dir = writer.output_root / writer.run_id
        _ensure_contained(writer.output_root, writer.run_dir)
        if not writer.run_dir.is_dir():
            raise FileNotFoundError(f"Run directory does not exist: {writer.run_dir}")
        writer.episodes_path = writer.run_dir / "episodes.jsonl"
        manifest_path = writer.run_dir / "run_manifest.json"
        if not manifest_path.is_file():
            raise FileNotFoundError(f"Run manifest does not exist: {manifest_path}")
        writer.manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        stored_identity = writer.manifest.get("run_identity_sha256")
        if not stored_identity:
            raise ValueError("Run manifest has no run_identity_sha256")
        if expected_manifest is not None:
            candidate = _normalize_manifest(expected_manifest, writer.run_id)
            if candidate["run_identity_sha256"] != stored_identity:
                raise ValueError(
                    "Run identity drift detected; create a new run instead of resuming"
                )
        return writer

    def write_manifest(self, manifest: Dict[str, Any]) -> Path:
        """Write the effective configuration once; never overwrite it."""

        path = self.run_dir / "run_manifest.json"
        if path.exists():
            raise FileExistsError(f"Run manifest already exists: {path}")
        normalized = _normalize_manifest(manifest, self.run_id)
        self._write_json(path, normalized)
        self.manifest = normalized
        return path

    def append_episode(self, trace: Dict[str, Any]) -> Path:
        """Append a complete episode trace as exactly one JSONL line."""

        required = ("run_id", "episode_id", "task_id", "retriever_name", "executor_name")
        missing = [field for field in required if field not in trace]
        if missing:
            raise ValueError(f"Episode trace is missing fields: {', '.join(missing)}")
        if trace["run_id"] != self.run_id:
            raise ValueError("Episode trace run_id does not match this writer")
        if (self.run_dir / "summary.json").exists():
            raise ValueError("Run is already summarized; create a new run to append episodes")
        normalized = dict(trace)
        normalized.update(_status_fields(normalized))
        schema_version = normalized.setdefault("schema_version", EPISODE_TRACE_SCHEMA)
        if schema_version != EPISODE_TRACE_SCHEMA:
            raise ValueError(
                f"Episode trace schema_version must be {EPISODE_TRACE_SCHEMA!r}"
            )
        episode_id = normalized["episode_id"]
        for line in self.episodes_path.read_text(encoding="utf-8").splitlines() if self.episodes_path.exists() else ():
            try:
                existing = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Cannot resume past malformed episode trace: {error}") from error
            if existing.get("episode_id") == episode_id:
                raise ValueError(f"Episode ID already exists: {episode_id}")
        with self.episodes_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(normalized, ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        trace.update(normalized)
        return self.episodes_path

    def write_summary(self, summary: Dict[str, Any]) -> Path:
        """Write a one-time run summary after all episodes have completed."""

        path = self.run_dir / "summary.json"
        if path.exists():
            raise FileExistsError(f"Run summary already exists: {path}")
        normalized = dict(summary)
        schema_version = normalized.setdefault("schema_version", "skillstack-run-summary-v1")
        if schema_version != "skillstack-run-summary-v1":
            raise ValueError("Summary schema_version must be 'skillstack-run-summary-v1'")
        normalized.setdefault("run_id", self.run_id)
        if normalized["run_id"] != self.run_id:
            raise ValueError("Summary run_id does not match this writer")
        if self.manifest is not None:
            manifest_identity = self.manifest["run_identity_sha256"]
            supplied_identity = normalized.setdefault(
                "run_identity_sha256", manifest_identity
            )
            if supplied_identity != manifest_identity:
                raise ValueError("Summary run_identity_sha256 does not match manifest")
            normalized.setdefault("code_commit", self.manifest.get("code_commit", "unavailable"))
        normalized.setdefault("generated_at_utc", datetime.now(timezone.utc).isoformat())
        self._write_json(path, normalized)
        return path

    def recompute_status_counts(self) -> Dict[str, int]:
        """Recompute counters from raw JSONL evidence, never from summary.json."""

        totals = {key: 0 for key in STATUS_KEYS}
        if not self.episodes_path.exists():
            return totals
        for line in self.episodes_path.read_text(encoding="utf-8").splitlines():
            try:
                trace = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Cannot recompute past malformed episode trace: {error}") from error
            for key, value in status_counts(trace).items():
                totals[key] += value
        return totals

    @staticmethod
    def _write_json(path: Path, payload: Dict[str, Any]) -> None:
        encoded = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
        temporary_path: Optional[Path] = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=str(path.parent),
                prefix=f".{path.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temporary_path = Path(handle.name)
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(str(temporary_path), str(path))
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()


def _make_run_id(label: str) -> str:
    normalized_label = RUN_ID_PATTERN.sub("-", label).strip("-.") or "run"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{timestamp}_{normalized_label}"


def _normalize_run_id(value: str) -> str:
    raw_path = Path(value)
    if raw_path.is_absolute() or len(raw_path.parts) > 1 or ".." in raw_path.parts:
        raise ValueError("run_id must be a single relative path component")
    normalized = RUN_ID_PATTERN.sub("-", value).strip("-.")
    if not normalized:
        raise ValueError("run_id must contain at least one safe character")
    return normalized


def _ensure_contained(root: Path, candidate: Path) -> None:
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError as error:
        raise ValueError(f"Run path escapes output root: {candidate}") from error


def _normalize_manifest(manifest: Dict[str, Any], run_id: str) -> Dict[str, Any]:
    normalized = dict(manifest)
    if normalized.get("run_id", run_id) != run_id:
        raise ValueError("Manifest run_id does not match this writer")
    normalized["run_id"] = run_id
    schema_version = normalized.setdefault("schema_version", RUN_MANIFEST_SCHEMA)
    if schema_version != RUN_MANIFEST_SCHEMA:
        raise ValueError(f"Manifest schema_version must be {RUN_MANIFEST_SCHEMA!r}")
    normalized.setdefault("code_commit", "unavailable")
    normalized.setdefault("package_version", "unavailable")
    normalized.setdefault("repo_dirty", "unavailable")
    normalized.setdefault("external_checkout_commit", "unavailable")
    normalized.setdefault("created_at_utc", datetime.now(timezone.utc).isoformat())
    normalized.pop("run_identity_sha256", None)
    normalized["run_identity_sha256"] = _identity_hash(normalized)
    return normalized


def _identity_hash(manifest: Dict[str, Any]) -> str:
    stable_manifest = {
        key: value
        for key, value in manifest.items()
        if key not in {"created_at_utc", "run_identity_sha256"}
    }
    canonical = json.dumps(
        stable_manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _status_fields(trace: Dict[str, Any]) -> Dict[str, Any]:
    stop_reason = trace.get("stop_reason")
    if stop_reason is None:
        run_status = "running"
    elif stop_reason == "runner_exception" or stop_reason == "llm_error":
        run_status = "error"
    elif "timeout" in str(stop_reason).lower():
        run_status = "timeout"
    elif "cancel" in str(stop_reason).lower():
        run_status = "cancelled"
    else:
        run_status = "completed"
    benchmark_claim = bool(trace.get("benchmark_success_claim", False))
    reason = str(stop_reason or "").lower()
    if reason in {"abstained", "agent_abstention"}:
        measurement_status = "abstained"
    elif reason in {"invalid_input", "invalid_task"}:
        measurement_status = "invalid"
    elif not benchmark_claim:
        measurement_status = "not_applicable"
    elif run_status == "completed":
        measurement_status = "valid"
    else:
        measurement_status = "invalid"
    task_success = (
        bool(trace["success"])
        if run_status == "completed"
        and measurement_status not in {"invalid", "abstained"}
        and "success" in trace
        else None
    )
    return {
        "run_status": run_status,
        "measurement_status": measurement_status,
        "task_success": task_success,
    }


def status_counts(trace: Dict[str, Any]) -> Dict[str, int]:
    """Return stable, recomputable status counters for one episode."""

    status = _status_fields(trace)
    counts = {key: 0 for key in STATUS_KEYS}
    counts["planned"] = 1
    counts["started"] = 1
    run_status = status["run_status"]
    if run_status == "completed":
        counts["completed"] = 1
        if status["measurement_status"] not in {"invalid", "abstained"}:
            if status["task_success"] is True:
                counts["success"] = 1
            elif status["task_success"] is False:
                counts["task_failure"] = 1
    elif run_status in counts:
        counts[run_status] = 1
    measurement_status = status["measurement_status"]
    if measurement_status == "valid":
        counts["valid"] = 1
    elif measurement_status == "invalid":
        counts["invalid"] = 1
    elif measurement_status == "abstained":
        counts["abstained"] = 1
    return counts
