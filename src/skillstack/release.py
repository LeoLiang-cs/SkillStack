"""Build and verify an isolated public-release snapshot."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


RELEASE_ROOTS = (
    ".env.example",
    ".github",
    ".gitignore",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "README.md",
    "THIRD_PARTY_NOTICES.md",
    "configs",
    "docs",
    "examples",
    "fixtures",
    "pyproject.toml",
    "reports",
    "scripts",
    "skills",
    "src",
    "tests",
    "uv.lock",
)

RELEASE_SINGLE_FILES = ("data/.gitkeep", "runs/.gitkeep")

EXCLUDED_PARTS = {
    ".DS_Store",
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "ideaspark_run",
    "papers",
    "tmp",
}

HELD_PREFIXES = ("docs/final_cards/",)

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


def collect_release_files(root: Path) -> List[Path]:
    """Return files intended for the public alpha snapshot.

    Tracked academic skills are included explicitly. Untracked local skills,
    held research cards, generated runs, external data, and scratch material
    are excluded.
    """

    repository = root.expanduser().resolve()
    selected: Set[Path] = set()

    for relative in RELEASE_ROOTS:
        candidate = repository / relative
        if candidate.is_file():
            selected.add(candidate.resolve())
        elif candidate.is_dir():
            selected.update(path.resolve() for path in candidate.rglob("*") if path.is_file())

    for relative in RELEASE_SINGLE_FILES:
        candidate = repository / relative
        if candidate.is_file():
            selected.add(candidate.resolve())

    license_path = repository / "LICENSE"
    if license_path.is_file():
        selected.add(license_path.resolve())

    for relative in _tracked_files(repository, ".agents/skills"):
        path = repository / relative
        if path.is_file():
            selected.add(path.resolve())

    return sorted(
        path
        for path in selected
        if not _is_excluded(path.relative_to(repository))
    )


def release_metadata(root: Path) -> Dict[str, Any]:
    repository = root.expanduser().resolve()
    files = collect_release_files(repository)
    relative_files = [path.relative_to(repository).as_posix() for path in files]
    held_present = [
        path for path in relative_files if any(path.startswith(prefix) for prefix in HELD_PREFIXES)
    ]
    license_present = (repository / "LICENSE").is_file()
    return {
        "check": "skillstack_release_metadata",
        "target_tag": "v0.1.0-alpha",
        "package_version": "0.1.0a0",
        "files_selected": len(relative_files),
        "license_present": license_present,
        "held_files_selected": held_present,
        "status": "pass" if license_present and not held_present else "fail",
    }


def copy_release_snapshot(root: Path, destination: Path) -> int:
    repository = root.expanduser().resolve()
    target = destination.expanduser().resolve()
    count = 0
    for source in collect_release_files(repository):
        relative = source.relative_to(repository)
        output = target / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(source), str(output))
        count += 1
    return count


def verify_fresh_clone(root: Path, allow_license_pending: bool = False) -> Dict[str, Any]:
    """Create a local git source snapshot, clone it, and run the release gate."""

    repository = root.expanduser().resolve()
    metadata = release_metadata(repository)
    command_results: List[Dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="skillstack-release-") as directory:
        temporary_root = Path(directory)
        source = temporary_root / "source"
        clone = temporary_root / "clone"
        source.mkdir()
        copied = copy_release_snapshot(repository, source)

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

    commands_passed = len(command_results) == len(CHECK_COMMANDS) and all(
        item["returncode"] == 0 for item in command_results
    )
    license_gate = bool(metadata["license_present"]) or allow_license_pending
    status = "pass" if commands_passed and license_gate and not metadata["held_files_selected"] else "fail"
    return {
        **metadata,
        "check": "skillstack_fresh_clone",
        "status": status,
        "technical_gate": "pass" if commands_passed else "fail",
        "license_gate": "pass"
        if metadata["license_present"]
        else ("waived_for_check" if allow_license_pending else "fail"),
        "files_copied": copied,
        "commands": command_results,
        "network_calls_by_skillstack": 0,
        "model_calls": 0,
    }


def run_fresh_clone_check(root: Path, allow_license_pending: bool = False) -> int:
    result = verify_fresh_clone(root, allow_license_pending=allow_license_pending)
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


def _tracked_files(root: Path, pathspec: str) -> Iterable[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z", "--", pathspec],
            cwd=str(root),
            check=True,
            capture_output=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ()
    return tuple(Path(entry.decode("utf-8")) for entry in result.stdout.split(b"\0") if entry)


def _is_excluded(relative: Path) -> bool:
    relative_text = relative.as_posix()
    if any(relative_text.startswith(prefix) for prefix in HELD_PREFIXES):
        return True
    return any(part in EXCLUDED_PARTS or part.endswith(".egg-info") for part in relative.parts)


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
