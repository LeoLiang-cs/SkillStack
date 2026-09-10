#!/usr/bin/env python3
"""Run the zero-network public-repository quality gate."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skillstack.quality import run_repository_checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    return run_repository_checks(args.root)


if __name__ == "__main__":
    raise SystemExit(main())
