#!/usr/bin/env python3
"""Run the isolated public-alpha fresh-clone gate."""

from __future__ import annotations

import argparse
from pathlib import Path

from skillstack.release import run_fresh_clone_check


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--allow-license-pending",
        action="store_true",
        help="run the technical gate while retaining the missing-license warning",
    )
    args = parser.parse_args()
    return run_fresh_clone_check(args.root, allow_license_pending=args.allow_license_pending)


if __name__ == "__main__":
    raise SystemExit(main())
