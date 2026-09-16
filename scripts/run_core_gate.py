#!/usr/bin/env python3
"""Run the core offline suite and fail on an unexpected optional skip."""

from __future__ import annotations

import argparse
import json
import platform
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, Optional, Sequence


ALLOWED_SKIP_REASONS = (
    "pinned SkillOps checkout unavailable",
    "no pick_two tasks in default manifest",
)


def _parse_args(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-dir", type=Path, default=Path("tests"))
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--artifact-hash", default=None)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    suite = unittest.defaultTestLoader.discover(str(args.start_dir))
    runner = unittest.TextTestRunner(
        stream=sys.stdout, verbosity=1, resultclass=unittest.TextTestResult
    )
    result = runner.run(suite)
    unexpected_skips = [
        reason
        for _test, reason in result.skipped
        if not any(allowed in reason for allowed in ALLOWED_SKIP_REASONS)
    ]
    summary: Dict[str, Any] = {
        "status": "pass"
        if result.wasSuccessful() and not unexpected_skips
        else "fail",
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skips": len(result.skipped),
        "skip_reasons": [reason for _test, reason in result.skipped],
        "unexpected_skip_reasons": unexpected_skips,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "artifact_hash": args.artifact_hash,
        "network_calls": 0,
        "model_calls": 0,
    }
    encoded = json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True)
    print(encoded)
    if args.summary:
        summary_path = args.summary.expanduser().resolve()
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(encoded + "\n", encoding="utf-8")
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
