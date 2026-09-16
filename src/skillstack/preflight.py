"""Repository-level, zero-model preflight checks for SkillStack."""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path
from typing import Any, Dict


REQUIRED_DIRECTORIES = (
    "configs",
    "skills/alfworld_static",
    "src/skillstack/environments",
    "src/skillstack/retrieval",
    "src/skillstack/execution",
    "src/skillstack/tracing",
    "runs",
    "reports",
    "tests",
)

REQUIRED_FILES = (
    "README.md",
    "pyproject.toml",
    "configs/p0_smoke.yaml",
    "reports/week1/phase0_manifest.json",
)

REQUIRED_CONFIG_MARKERS = (
    "id: p0_0_vertical_slice",
    "provider: alfworld_text",
    "split: valid_unseen",
    "control: no_skill",
    "pilot: debug_lexical_top_k",
)


def evaluate_preflight(root: Path) -> Dict[str, Any]:
    """Return a machine-readable repository preflight result without network access."""

    workspace = root.expanduser().resolve()
    repository_marker_present = (workspace / "pyproject.toml").is_file() and (workspace / ".git").exists()
    required_paths = (*REQUIRED_DIRECTORIES, *REQUIRED_FILES)
    missing = [path for path in required_paths if not (workspace / path).exists()]

    config_path = workspace / "configs" / "p0_smoke.yaml"
    if config_path.is_file():
        config_text = config_path.read_text(encoding="utf-8")
        missing_markers = [
            marker for marker in REQUIRED_CONFIG_MARKERS if marker not in config_text
        ]
    else:
        missing_markers = list(REQUIRED_CONFIG_MARKERS)

    passed = repository_marker_present and not missing and not missing_markers
    diagnostic = None
    if not repository_marker_present:
        diagnostic = (
            "preflight is repo-only; run it from a SkillStack checkout or pass "
            "--root <checkout>"
        )
    return {
        "check": "skillstack_repository_preflight",
        "experiment_id": "p0_0_vertical_slice",
        "workspace": str(workspace),
        "repository_marker_present": repository_marker_present,
        "python": sys.version.split()[0],
        "platform": f"{platform.system()} {platform.machine()}",
        "required_directories_present": not missing,
        "configuration_valid": not missing_markers,
        "missing": missing,
        "missing_configuration_markers": missing_markers,
        "diagnostic": diagnostic,
        "status": "pass" if passed else "fail",
        "network_calls": 0,
        "model_calls": 0,
    }


def run_preflight(root: Path) -> int:
    """Print the preflight result and return a process exit code."""

    result = evaluate_preflight(root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1
