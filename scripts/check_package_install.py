#!/usr/bin/env python3
"""Build and smoke-test SkillStack artifacts outside the source checkout.

This is intentionally a user-run gate: creating virtual environments and
installing a source archive can take several minutes and may need a package
index. The command never contacts a model or benchmark service; the installed
CLI only runs the deterministic packaged demo.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence


def _run(command: Sequence[str], cwd: Path) -> None:
    print("$ " + " ".join(command), flush=True)
    subprocess.run(list(command), cwd=str(cwd), check=True)


def _assert_import_removed(python: Path, cwd: Path) -> None:
    result = subprocess.run(
        [str(python), "-c", "import skillstack"],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        raise RuntimeError("skillstack remained importable after uninstall")


def _venv_python(venv: Path) -> Path:
    candidate = venv / "Scripts" / "python.exe"
    if candidate.exists():
        return candidate
    return venv / "bin" / "python"


def _venv_executable(venv: Path, name: str) -> Path:
    candidate = venv / "Scripts" / f"{name}.exe"
    if candidate.exists():
        return candidate
    return venv / "bin" / name


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_paths(dist: Path, selection: str) -> Iterable[Path]:
    paths = sorted(dist.glob("*.whl")) + sorted(dist.glob("*.tar.gz"))
    if selection == "wheel":
        paths = [path for path in paths if path.suffix == ".whl"]
    elif selection == "sdist":
        paths = [path for path in paths if path.name.endswith(".tar.gz")]
    if not paths:
        raise FileNotFoundError(f"No {selection} artifacts found in {dist}")
    return paths


def _write_summary(path: Optional[Path], summary: Dict[str, object]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True)
    path.write_text(encoded + "\n", encoding="utf-8")


def _parse_args(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--python",
        default="3.12",
        help="Python selector passed to uv venv (default: 3.12)",
    )
    parser.add_argument(
        "--artifact",
        choices=("all", "wheel", "sdist"),
        default="all",
        help="artifact types to install (default: all)",
    )
    parser.add_argument(
        "--no-deps",
        action="store_true",
        help="skip dependency installation when checking a local/cached package",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="preserve the temporary build and virtual environments for inspection",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        help="optional JSON path for the acceptance summary",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    root = args.root.expanduser().resolve()
    summary_path = args.summary.expanduser().resolve() if args.summary else None
    uv = shutil.which("uv")
    if uv is None:
        raise SystemExit("uv is required; install it before running this gate")

    temp_dir: Optional[Path] = None
    if args.keep_temp:
        temp_dir = Path(tempfile.mkdtemp(prefix="skillstack-package-"))
        context = None
    else:
        context = tempfile.TemporaryDirectory(prefix="skillstack-package-")
        temp_dir = Path(context.name)

    summary: Dict[str, object] = {
        "status": "not_run",
        "source_checkout": root.name,
        "workspace_isolation": "temporary_directory",
        "python_selector": args.python,
        "artifacts": [],
        "network_calls": 0,
        "model_calls": 0,
    }
    try:
        dist = temp_dir / "dist"
        clean_config_home = temp_dir / "empty-config"
        clean_config_home.mkdir(parents=True, exist_ok=True)
        os.environ.pop("SKILLSTACK_LLM_CONFIG", None)
        os.environ["XDG_CONFIG_HOME"] = str(clean_config_home)
        _run([uv, "build", "--out-dir", str(dist)], root)
        artifacts = list(_artifact_paths(dist, args.artifact))
        summary["status"] = "running"

        for artifact in artifacts:
            label = "wheel" if artifact.suffix == ".whl" else "sdist"
            cast_artifacts = summary["artifacts"]
            assert isinstance(cast_artifacts, list)
            artifact_record: Dict[str, object] = {
                "type": label,
                "path": artifact.name,
                "bytes": artifact.stat().st_size,
                "sha256": _sha256(artifact),
            }
            cast_artifacts.append(artifact_record)
            venv = temp_dir / f"venv-{label}"
            outside = temp_dir / f"outside-{label}"
            output_root = temp_dir / f"outputs-{label}"
            outside.mkdir(parents=True, exist_ok=True)
            _run([uv, "venv", "--python", args.python, str(venv)], root)
            python = _venv_python(venv)
            install = [uv, "pip", "install", "--python", str(python)]
            if args.no_deps:
                install.append("--no-deps")
            install.append(str(artifact))
            _run(install, outside)
            cli = _venv_executable(venv, "skillstack")
            _run([str(cli), "--version"], outside)
            _run([str(cli), "demo", "--help"], outside)
            _run(
                [
                    str(python),
                    "-c",
                    "from skillstack.llm import load_backends; assert load_backends()",
                ],
                outside,
            )
            _run(
                [
                    str(cli),
                    "demo",
                    "--output-root",
                    str(output_root),
                    "--run-id-prefix",
                    f"package_{label}",
                ],
                outside,
            )
            _run(
                [
                    str(python),
                    "-c",
                    (
                        "from importlib import metadata; "
                        "m=metadata.metadata('skillstack'); "
                        "assert m['Name']=='skillstack'; "
                        "assert any(str(p).endswith('/LICENSE') or str(p)=='LICENSE' "
                        "for p in (metadata.files('skillstack') or ())); "
                        "assert any(str(p).endswith('/THIRD_PARTY_NOTICES.md') "
                        "or str(p)=='THIRD_PARTY_NOTICES.md' "
                        "for p in (metadata.files('skillstack') or ())); "
                        "assert any(ep.name=='skillstack' and ep.value=='skillstack.cli:main' "
                        "for ep in metadata.entry_points(group='console_scripts'))"
                    ),
                ],
                outside,
            )
            run_dirs = sorted((output_root / "demo").glob("package_*"))
            if len(run_dirs) != 2:
                raise RuntimeError(
                    f"Installed {label} demo produced {len(run_dirs)} runs; expected 2"
                )
            artifact_record.update(
                {
                    "run_directories": [
                        path.relative_to(temp_dir).as_posix() for path in run_dirs
                    ],
                    "metadata_license_entrypoint": "pass",
                }
            )
            _run([uv, "pip", "uninstall", "--python", str(python), "-y", "skillstack"], outside)
            _assert_import_removed(python, outside)
            artifact_record["uninstall"] = "pass"

        summary["status"] = "pass"
        encoded = json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True)
        print(encoded)
        _write_summary(summary_path, summary)
        if args.keep_temp:
            print(f"Preserved temporary gate directory: {temp_dir}")
        return 0
    except Exception as error:
        summary["status"] = "fail"
        summary["error"] = {
            "type": type(error).__name__,
            "message": str(error)[:1000],
        }
        if isinstance(error, subprocess.CalledProcessError):
            summary["failed_command"] = list(error.cmd)
            summary["returncode"] = error.returncode
        _write_summary(summary_path, summary)
        raise
    finally:
        if context is not None:
            context.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
