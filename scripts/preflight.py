"""Validate the P0.0 experiment skeleton without requiring external packages."""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

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


def main() -> int:
    missing = [
        path
        for path in (*REQUIRED_DIRECTORIES, *REQUIRED_FILES)
        if not (ROOT / path).exists()
    ]
    config_text = (ROOT / "configs/p0_smoke.yaml").read_text(encoding="utf-8")
    required_markers = (
        "id: p0_0_vertical_slice",
        "provider: alfworld_text",
        "split: valid_unseen",
        "control: no_skill",
        "pilot: debug_lexical_top_k",
    )
    missing_markers = [marker for marker in required_markers if marker not in config_text]

    result = {
        "experiment_id": "p0_0_vertical_slice",
        "phase": "0",
        "workspace": str(ROOT),
        "python": sys.version.split()[0],
        "platform": f"{platform.system()} {platform.machine()}",
        "required_directories_present": len(missing) == 0,
        "configuration_valid": len(missing_markers) == 0,
        "missing": missing,
        "missing_configuration_markers": missing_markers,
        "next_gate": "Select and commit five loadable valid_unseen task IDs.",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not missing and not missing_markers else 1


if __name__ == "__main__":
    raise SystemExit(main())
