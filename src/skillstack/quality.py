"""Deterministic, zero-network checks for files intended for public release."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Set

import yaml


PUBLIC_ROOTS = (
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

EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "data",
    "dist",
    "ideaspark_run",
    "papers",
    "runs",
    "tmp",
}

HELD_PREFIXES = ("docs/final_cards/",)

TEXT_SUFFIXES = {".csv", ".json", ".md", ".py", ".toml", ".txt", ".yaml", ".yml"}

PRIVATE_PATH_PATTERNS = (
    re.compile(r"/Users/[^/\s]+/"),  # public-repo-check: allow-pattern
    re.compile(r"/home/[^/\s]+/"),  # public-repo-check: allow-pattern
    re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+\\"),  # public-repo-check: allow-pattern
)

SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"authorization\s*:\s*bearer\s+[A-Za-z0-9._-]{12,}", re.IGNORECASE),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)

MARKDOWN_LINK_PATTERN = re.compile(r"\]\(([^)]+)\)")


def collect_public_files(root: Path) -> List[Path]:
    """Collect tracked files plus untracked files under declared public roots."""

    repository = root.expanduser().resolve()
    files: Set[Path] = set(_tracked_files(repository))
    for relative in PUBLIC_ROOTS:
        candidate = repository / relative
        if candidate.is_file():
            files.add(candidate.resolve())
        elif candidate.is_dir():
            files.update(path.resolve() for path in candidate.rglob("*") if path.is_file())
    selected = []
    for path in files:
        relative = path.relative_to(repository)
        relative_text = relative.as_posix()
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in EXCLUDED_PARTS or part.endswith(".egg-info") for part in relative.parts):
            continue
        if any(relative_text.startswith(prefix) for prefix in HELD_PREFIXES):
            continue
        selected.append(path)
    return sorted(selected)


def check_text(path: Path, text: str, root: Path) -> List[Dict[str, str]]:
    findings: List[Dict[str, str]] = []
    relative = str(path.relative_to(root))

    if text and not text.endswith("\n"):
        findings.append(_finding("missing_final_newline", relative, "file must end with a newline"))

    for line_number, line in enumerate(text.splitlines(), start=1):
        if "public-repo-check: allow-pattern" in line:
            continue
        for pattern in PRIVATE_PATH_PATTERNS:
            if pattern.search(line):
                findings.append(
                    _finding("private_absolute_path", relative, f"line {line_number}")
                )
                break
        for pattern in SECRET_PATTERNS:
            if pattern.search(line):
                findings.append(_finding("credential_like_value", relative, f"line {line_number}"))
                break

        if path.name.startswith(".env") and "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            if key.strip() and value.strip():
                findings.append(_finding("credential_like_value", relative, f"line {line_number}"))

    if path.suffix.lower() == ".md":
        findings.extend(_check_markdown_links(path, text, root))
    if path.suffix.lower() == ".json":
        try:
            json.loads(text)
        except json.JSONDecodeError as error:
            findings.append(_finding("invalid_json", relative, f"line {error.lineno}: {error.msg}"))
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            yaml.safe_load(text)
        except yaml.YAMLError as error:
            findings.append(_finding("invalid_yaml", relative, str(error).splitlines()[0]))
    return findings


def inspect_repository(root: Path) -> Dict[str, object]:
    repository = root.expanduser().resolve()
    findings: List[Dict[str, str]] = []
    files = collect_public_files(repository)
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(
                _finding("non_utf8_text_file", str(path.relative_to(repository)), "cannot decode as UTF-8")
            )
            continue
        findings.extend(check_text(path, text, repository))
    return {
        "check": "skillstack_public_repository",
        "status": "pass" if not findings else "fail",
        "files_checked": len(files),
        "findings": findings,
        "network_calls": 0,
        "model_calls": 0,
    }


def run_repository_checks(root: Path) -> int:
    result = inspect_repository(root)
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


def _tracked_files(root: Path) -> Iterable[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=root,
            check=True,
            capture_output=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ()
    return tuple(
        (root / entry.decode("utf-8")).resolve()
        for entry in result.stdout.split(b"\0")
        if entry and (root / entry.decode("utf-8")).is_file()
    )


def _check_markdown_links(path: Path, text: str, root: Path) -> List[Dict[str, str]]:
    findings: List[Dict[str, str]] = []
    relative = str(path.relative_to(root))
    for raw_target in MARKDOWN_LINK_PATTERN.findall(text):
        target = raw_target.strip().strip("<>")
        if target.startswith(("#", "http://", "https://", "mailto:")):
            continue
        target = target.split("#", 1)[0]
        if not target:
            continue
        destination = (path.parent / target).resolve()
        if not destination.exists():
            findings.append(_finding("broken_local_markdown_link", relative, raw_target))
    return findings


def _finding(kind: str, path: str, detail: str) -> Dict[str, str]:
    return {"kind": kind, "path": path, "detail": detail}
