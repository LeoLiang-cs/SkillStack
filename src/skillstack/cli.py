"""Command-line entry point for safe, repository-level SkillStack checks."""

from __future__ import annotations

import argparse
from importlib import metadata
from pathlib import Path
from typing import Optional, Sequence

from skillstack.demo import run_demo
from skillstack.preflight import run_preflight
from skillstack.quality import run_repository_checks
from skillstack.release import run_fresh_clone_check


def _version() -> str:
    try:
        return metadata.version("skillstack")
    except metadata.PackageNotFoundError:
        return "0.1.0a0"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skillstack",
        description="SkillStack experimental harness utilities.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {_version()}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    preflight = subparsers.add_parser(
        "preflight",
        help="validate the repository skeleton without data, API keys, or model calls",
    )
    preflight.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="repository root to validate (default: current directory)",
    )

    check_repo = subparsers.add_parser(
        "check-repo",
        help="check public files for broken links, private paths, secrets, and invalid data files",
    )
    check_repo.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="repository root to validate (default: current directory)",
    )

    demo = subparsers.add_parser(
        "demo",
        help="run the deterministic zero-model composability demonstration",
    )
    demo.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="repository root containing examples/demo and skills (default: current directory)",
    )
    demo.add_argument(
        "--output-root",
        type=Path,
        default=Path.cwd() / "runs",
        help="directory under which demo/<run-id> directories are created",
    )
    demo.add_argument(
        "--configuration",
        choices=("all", "c0_no_skill", "c1_debug_lexical"),
        default="all",
    )
    demo.add_argument("--top-k", type=int, default=2)
    demo.add_argument(
        "--run-id-prefix",
        default=None,
        help="optional deterministic prefix for tests or resumable local runs",
    )

    release_check = subparsers.add_parser(
        "release-check",
        help="clone an isolated public snapshot and run the complete local release gate",
    )
    release_check.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="repository root to snapshot (default: current directory)",
    )
    release_check.add_argument(
        "--allow-license-pending",
        action="store_true",
        help="verify technical reproducibility before the owner selects a project license",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "preflight":
        return run_preflight(args.root)
    if args.command == "check-repo":
        return run_repository_checks(args.root)
    if args.command == "demo":
        result = run_demo(
            root=args.root,
            output_root=args.output_root,
            configuration=args.configuration,
            top_k=args.top_k,
            run_id_prefix=args.run_id_prefix,
        )
        import json

        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
        return 0
    if args.command == "release-check":
        return run_fresh_clone_check(
            args.root,
            allow_license_pending=args.allow_license_pending,
        )
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
