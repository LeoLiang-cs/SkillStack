"""Build and verify an isolated public-release snapshot from a Git commit."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import stat
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Sequence, Tuple
import zipfile

import yaml


PUBLIC_RELEASE_POLICY = "configs/public_release_scope.yaml"
RELEASE_TAG = "v0.1.0-alpha"
PACKAGE_VERSION = "0.1.0a0"
CATEGORIES = ("public", "held_research", "external_data", "generated")

CHECK_COMMANDS: Tuple[Tuple[str, ...], ...] = (
    ("uv", "sync", "--frozen"),
    ("uv", "run", "skillstack", "preflight"),
    ("uv", "run", "skillstack", "check-repo"),
    (
        "uv",
        "run",
        "skillstack",
        "demo",
        "--output-root",
        "{demo_output}",
        "--run-id-prefix",
        "fresh-clone",
    ),
    ("uv", "run", "python", "-m", "compileall", "-q", "src", "scripts", "tests"),
    ("uv", "run", "python", "-m", "unittest", "discover", "-s", "tests", "-q"),
    ("uv", "build"),
)


class ReleaseError(RuntimeError):
    """Raised when a release input cannot be proven safe."""


@dataclass(frozen=True)
class _Policy:
    patterns: Dict[str, Tuple[str, ...]]
    required: Tuple[str, ...]
    schema_version: int


@dataclass(frozen=True)
class _TreeEntry:
    path: str
    mode: str
    object_id: str


def collect_release_files(root: Path, ref: str = "HEAD") -> List[Path]:
    """Return public paths selected from ``ref``.

    Returned paths are relative to the repository root for compatibility with
    the older API; their bytes are read from Git objects, never the dirty tree.
    """

    repository = root.expanduser().resolve()
    _commit, entries, _ = _release_snapshot(repository, ref)
    return [repository / entry.path for entry in entries]


def release_manifest(root: Path, ref: str = "HEAD") -> Dict[str, Any]:
    """Build a deterministic, hash-addressed manifest for a Git ref."""

    repository = root.expanduser().resolve()
    commit, selected, excluded = _release_snapshot(repository, ref)
    policy_bytes = _git_show(repository, commit, PUBLIC_RELEASE_POLICY)
    policy_hash = _sha256(policy_bytes)

    files: List[Dict[str, Any]] = []
    total_bytes = 0
    for entry in selected:
        content = _git_show(repository, commit, entry.path)
        size = len(content)
        total_bytes += size
        files.append(
            {
                "path": entry.path,
                "mode": entry.mode,
                "object_id": entry.object_id,
                "bytes": size,
                "sha256": _sha256(content),
            }
        )

    categories = {
        category: {
            "count": len(excluded.get(category, ())),
            "paths": list(excluded.get(category, ())),
        }
        for category in (*CATEGORIES, "unknown", "rejected")
    }
    payload: Dict[str, Any] = {
        "schema_version": 1,
        "check": "skillstack_release_manifest",
        "target_tag": RELEASE_TAG,
        "package_version": PACKAGE_VERSION,
        "requested_ref": ref,
        "resolved_commit": commit,
        "policy_path": PUBLIC_RELEASE_POLICY,
        "policy_sha256": policy_hash,
        "files_selected": len(files),
        "total_bytes": total_bytes,
        "categories": categories,
        "required_files": list(_read_policy(policy_bytes).required),
        "files": files,
    }
    payload["content_sha256"] = _content_hash(files)
    payload["manifest_sha256"] = _sha256(_canonical_json(payload))
    return payload


def release_metadata(root: Path, ref: str = "HEAD") -> Dict[str, Any]:
    """Return release metadata, including the complete deterministic manifest."""

    repository = root.expanduser().resolve()
    try:
        manifest = release_manifest(repository, ref)
        rejected = manifest["categories"]["rejected"]["count"]
        required = set(manifest["required_files"])
        selected = {item["path"] for item in manifest["files"]}
        required_missing = sorted(required - selected)
        license_present = "LICENSE" in selected
        status = "pass" if not rejected and not required_missing and license_present else "fail"
        return {
            **manifest,
            "license_present": license_present,
            "held_files_selected": [],
            "required_missing": required_missing,
            "dirty_worktree": _dirty_worktree(repository),
            "status": status,
        }
    except ReleaseError as error:
        return {
            "check": "skillstack_release_metadata",
            "target_tag": RELEASE_TAG,
            "package_version": PACKAGE_VERSION,
            "requested_ref": ref,
            "status": "fail",
            "error": str(error),
            "dirty_worktree": _dirty_worktree(repository),
        }


def copy_release_snapshot(root: Path, destination: Path, ref: str = "HEAD") -> int:
    """Copy selected Git blobs into ``destination`` and return the count."""

    repository = root.expanduser().resolve()
    commit, selected, _ = _release_snapshot(repository, ref)
    target = destination.expanduser().resolve()
    count = 0
    for entry in selected:
        relative = PurePosixPath(entry.path)
        output = target.joinpath(*relative.parts)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(_git_show(repository, commit, entry.path))
        if entry.mode.endswith("755"):
            output.chmod(output.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        count += 1
    return count


def verify_fresh_clone(
    root: Path,
    ref: str = "HEAD",
    allow_license_pending: bool = False,
) -> Dict[str, Any]:
    """Clone a commit-based public snapshot and run the local release gate."""

    repository = root.expanduser().resolve()
    metadata = release_metadata(repository, ref=ref)
    if metadata.get("status") == "fail" and "files" not in metadata:
        return {**metadata, "check": "skillstack_fresh_clone"}

    command_results: List[Dict[str, Any]] = []
    artifact_checks: List[Dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="skillstack-release-") as directory:
        temporary_root = Path(directory)
        source = temporary_root / "source"
        clone = temporary_root / "clone"
        source.mkdir()
        copied = copy_release_snapshot(repository, source, ref=ref)

        setup_commands = (
            ("git", "init", "-q"),
            ("git", "config", "user.name", "SkillStack Release Check"),
            ("git", "config", "user.email", "release-check@example.invalid"),
            ("git", "add", "."),
            ("git", "commit", "-q", "-m", "release snapshot"),
        )
        for command in setup_commands:
            result = _run(command, source)
            if result["returncode"] != 0:
                return {
                    **metadata,
                    "check": "skillstack_fresh_clone",
                    "status": "fail",
                    "files_copied": copied,
                    "failed_stage": "snapshot_git_init",
                    "commands": [result],
                }

        clone_result = _run(("git", "clone", "--no-local", "-q", str(source), str(clone)), temporary_root)
        if clone_result["returncode"] != 0:
            return {
                **metadata,
                "check": "skillstack_fresh_clone",
                "status": "fail",
                "files_copied": copied,
                "failed_stage": "clone",
                "commands": [clone_result],
            }

        demo_output = temporary_root / "demo-output"
        for template in CHECK_COMMANDS:
            command = tuple(part.format(demo_output=str(demo_output)) for part in template)
            result = _run(command, clone)
            command_results.append(result)
            if result["returncode"] != 0:
                break
        artifact_checks = _inspect_artifacts(clone / "dist")

    commands_passed = len(command_results) == len(CHECK_COMMANDS) and all(
        item["returncode"] == 0 for item in command_results
    )
    artifact_gate = bool(artifact_checks) and all(item["status"] == "pass" for item in artifact_checks)
    license_gate = bool(metadata.get("license_present")) or allow_license_pending
    status = (
        "pass"
        if commands_passed and artifact_gate and license_gate and metadata["status"] == "pass"
        else "fail"
    )
    return {
        **metadata,
        "check": "skillstack_fresh_clone",
        "status": status,
        "technical_gate": "pass" if commands_passed else "fail",
        "artifact_gate": "pass" if artifact_gate else "fail",
        "artifacts": artifact_checks,
        "license_gate": "pass"
        if metadata.get("license_present")
        else ("waived_for_check" if allow_license_pending else "fail"),
        "files_copied": copied,
        "commands": command_results,
        "network_calls_by_skillstack": 0,
        "model_calls": 0,
    }


def run_fresh_clone_check(
    root: Path,
    ref: str = "HEAD",
    allow_license_pending: bool = False,
) -> int:
    result = verify_fresh_clone(root, ref=ref, allow_license_pending=allow_license_pending)
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


def _release_snapshot(
    repository: Path, ref: str
) -> Tuple[str, List[_TreeEntry], Dict[str, Tuple[str, ...]]]:
    commit = _resolve_commit(repository, ref)
    policy_bytes = _git_show(repository, commit, PUBLIC_RELEASE_POLICY)
    policy = _read_policy(policy_bytes)
    tree = _tree_entries(repository, commit)
    selected: List[_TreeEntry] = []
    excluded: Dict[str, List[str]] = {category: [] for category in (*CATEGORIES, "unknown", "rejected")}
    selected_paths = set()
    for entry in tree:
        category = _classify(entry.path, policy)
        if category == "public":
            if entry.mode == "120000" or entry.mode not in {"100644", "100755"}:
                excluded["rejected"].append(entry.path)
                continue
            selected.append(entry)
            selected_paths.add(entry.path)
        else:
            excluded[category].append(entry.path)

    missing = [path for path in policy.required if path not in selected_paths]
    if missing:
        raise ReleaseError(f"required public files missing from {commit}: {', '.join(missing)}")
    if excluded["rejected"]:
        raise ReleaseError("unsupported file modes in public scope: " + ", ".join(excluded["rejected"]))
    if not selected:
        raise ReleaseError(f"public policy selected no files from {commit}")
    return commit, selected, {key: tuple(sorted(value)) for key, value in excluded.items()}


def _read_policy(raw: bytes) -> _Policy:
    try:
        data = yaml.safe_load(raw.decode("utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as error:
        raise ReleaseError(f"invalid release policy YAML: {error}") from error
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ReleaseError("release policy must declare schema_version: 1")

    patterns: Dict[str, Tuple[str, ...]] = {}
    seen: Dict[str, str] = {}
    for category in CATEGORIES:
        raw_patterns = data.get(category, [])
        if not isinstance(raw_patterns, list) or not all(isinstance(item, str) for item in raw_patterns):
            raise ReleaseError(f"release policy category {category!r} must be a list of strings")
        normalized: List[str] = []
        for pattern in raw_patterns:
            _validate_pattern(pattern)
            if pattern in seen and seen[pattern] != category:
                raise ReleaseError(f"release policy pattern appears in multiple categories: {pattern}")
            seen[pattern] = category
            normalized.append(pattern)
        patterns[category] = tuple(normalized)

    required = data.get("required", [])
    if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
        raise ReleaseError("release policy required must be a list of strings")
    for path in required:
        _validate_pattern(path)
        if any(char in path for char in "*?["):
            raise ReleaseError(f"required file must be exact, not a glob: {path}")
        if not any(_matches(path, pattern) for pattern in patterns["public"]):
            raise ReleaseError(f"required file is not public: {path}")
    return _Policy(patterns=patterns, required=tuple(required), schema_version=1)


def _validate_pattern(pattern: str) -> None:
    if not pattern or pattern.startswith("/"):
        raise ReleaseError(f"invalid release policy path: {pattern!r}")
    path = PurePosixPath(pattern)
    if ".." in path.parts or "" in path.parts:
        raise ReleaseError(f"release policy path traversal: {pattern!r}")


def _classify(path: str, policy: _Policy) -> str:
    matched = [
        category
        for category in CATEGORIES
        if any(_matches(path, pattern) for pattern in policy.patterns[category])
    ]
    if len(matched) > 1:
        raise ReleaseError(f"release policy categories overlap for {path}: {matched}")
    return matched[0] if matched else "unknown"


def _matches(path: str, pattern: str) -> bool:
    if pattern.endswith("/**"):
        prefix = pattern[:-3].rstrip("/")
        return path == prefix or path.startswith(prefix + "/")
    return fnmatch.fnmatchcase(path, pattern)


def _resolve_commit(root: Path, ref: str) -> str:
    if not ref or ref == "WORKTREE":
        raise ReleaseError("G0 requires a Git ref; WORKTREE is not an accepted release source")
    result = _run_git(root, ("rev-parse", "--verify", f"{ref}^{{commit}}"))
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ReleaseError(f"cannot resolve release ref {ref!r}: {detail or 'unknown Git error'}")
    return result.stdout.decode("ascii").strip()


def _tree_entries(root: Path, commit: str) -> List[_TreeEntry]:
    result = _run_git(root, ("ls-tree", "-r", "-z", "--full-tree", commit))
    if result.returncode != 0:
        raise ReleaseError("cannot enumerate Git tree: " + result.stderr.decode("utf-8", errors="replace"))
    entries: List[_TreeEntry] = []
    for record in result.stdout.split(b"\0"):
        if not record:
            continue
        try:
            metadata, raw_path = record.split(b"\t", 1)
            mode, _kind, object_id = metadata.decode("ascii").split(" ")
            path = raw_path.decode("utf-8")
        except (UnicodeDecodeError, ValueError) as error:
            raise ReleaseError("invalid Git tree entry") from error
        if not path or PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts:
            raise ReleaseError(f"unsafe Git tree path: {path!r}")
        entries.append(_TreeEntry(path=path, mode=mode, object_id=object_id))
    return entries


def _git_show(root: Path, commit: str, path: str) -> bytes:
    result = _run_git(root, ("show", f"{commit}:{path}"))
    if result.returncode != 0:
        raise ReleaseError(f"cannot read Git blob {commit}:{path}")
    return result.stdout


def _run_git(root: Path, args: Sequence[str]) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(["git", *args], cwd=str(root), capture_output=True, check=False)
    except FileNotFoundError as error:
        raise ReleaseError("git executable is required for G0") from error


def _dirty_worktree(root: Path) -> List[str]:
    result = _run_git(root, ("status", "--porcelain=v1", "-z", "--untracked-files=all"))
    if result.returncode != 0:
        return []
    paths: List[str] = []
    for record in result.stdout.split(b"\0"):
        if len(record) < 4:
            continue
        raw_path = record[3:]
        try:
            paths.append(raw_path.decode("utf-8"))
        except UnicodeDecodeError:
            paths.append(raw_path.decode("utf-8", errors="replace"))
    return sorted(set(paths))


def _inspect_artifacts(dist: Path) -> List[Dict[str, Any]]:
    """Inspect wheel/sdist members without extracting untrusted archive paths."""

    artifacts = sorted(
        path for path in dist.glob("*") if path.is_file() and (path.name.endswith(".whl") or ".tar.gz" in path.name)
    ) if dist.is_dir() else []
    checks: List[Dict[str, Any]] = []
    for artifact in artifacts:
        try:
            members = _archive_members(artifact)
            normalized = _strip_archive_root(members)
            unsafe = [name for name in normalized if _unsafe_archive_path(name)]
            forbidden = [name for name in normalized if _forbidden_artifact_path(name)]
            checks.append(
                {
                    "path": artifact.name,
                    "bytes": artifact.stat().st_size,
                    "sha256": _sha256(artifact.read_bytes()),
                    "member_count": len(normalized),
                    "unsafe_members": unsafe,
                    "forbidden_members": forbidden,
                    "status": "pass" if not unsafe and not forbidden else "fail",
                }
            )
        except (OSError, tarfile.TarError, zipfile.BadZipFile) as error:
            checks.append({"path": artifact.name, "status": "fail", "error": str(error)})
    return checks


def _archive_members(path: Path) -> List[str]:
    if path.name.endswith(".whl"):
        with zipfile.ZipFile(path) as archive:
            return [item.filename for item in archive.infolist() if not item.is_dir()]
    with tarfile.open(path, "r:gz") as archive:
        return [item.name for item in archive.getmembers() if item.isfile()]


def _strip_archive_root(names: Sequence[str]) -> List[str]:
    parts = [PurePosixPath(name).parts for name in names]
    roots = {item[0] for item in parts if item}
    if len(roots) == 1 and all(len(item) > 1 for item in parts):
        return [PurePosixPath(*item[1:]).as_posix() for item in parts]
    return [PurePosixPath(*item).as_posix() for item in parts]


def _unsafe_archive_path(name: str) -> bool:
    path = PurePosixPath(name)
    return path.is_absolute() or ".." in path.parts


def _forbidden_artifact_path(name: str) -> bool:
    if name in {"runs/.gitkeep", "data/.gitkeep"}:
        return False
    forbidden_prefixes = (
        "docs/final_cards/",
        "docs/scoop_ check/",
        "reports/week6/",
        "report/week7/",
        ".agents/skills/idea-spark/",
        "papers/",
        "data/alfworld/",
        "ideaspark_run/",
        "tmp/",
        ".venv/",
        "build/",
        "dist/",
        "runs/",
    )
    return any(name.startswith(prefix) for prefix in forbidden_prefixes) or "__pycache__" in PurePosixPath(name).parts


def _content_hash(files: Sequence[Dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for item in files:
        digest.update(item["path"].encode("utf-8"))
        digest.update(b"\0")
        digest.update(item["mode"].encode("ascii"))
        digest.update(b"\0")
        digest.update(str(item["bytes"]).encode("ascii"))
        digest.update(b"\0")
        digest.update(item["sha256"].encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _run(command: Sequence[str], cwd: Path) -> Dict[str, Any]:
    try:
        completed = subprocess.run(
            list(command),
            cwd=str(cwd),
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as error:
        return {
            "command": list(command),
            "returncode": 127,
            "stdout_tail": "",
            "stderr_tail": str(error),
        }
    return {
        "command": list(command),
        "returncode": completed.returncode,
        "stdout_tail": _tail(completed.stdout),
        "stderr_tail": _tail(completed.stderr),
    }


def _tail(text: str, lines: int = 12) -> str:
    return "\n".join(text.splitlines()[-lines:])
