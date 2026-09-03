#!/usr/bin/env python3
"""Run SkillOps M1-M3 checks and the separately authorized M4 pilot."""

from __future__ import annotations

import argparse
from pathlib import Path

from skillstack.experiments.skillops_maintenance import (
    build_clean_fixture,
    build_stress_fixture,
    preflight,
    run_m1,
    run_m2,
    run_m3,
    write_json,
)
from skillstack.experiments.skillops_performance import (
    BACKEND_NAME,
    compare,
    evaluate,
    parse_csv,
    parse_seeds,
    performance_preflight,
)
from skillstack.llm import load_env_file


DEFAULT_SKILLOPS = Path("/Users/leo/Project/Research/USC/FORTIS/_external/week6/SkillOps")
DEFAULT_GRASP = Path("/Users/leo/Project/Research/USC/FORTIS/_external/week5/GRASP")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase",
        choices=("preflight", "roundtrip", "fixture", "parity", "all", "evaluate", "compare"),
        default="all",
    )
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--skillops-root", type=Path, default=DEFAULT_SKILLOPS)
    parser.add_argument("--grasp-root", type=Path, default=DEFAULT_GRASP)
    parser.add_argument("--source-run", type=Path, default=Path("runs/week5/w5_a_slot_seed2_deepseek_flash"))
    parser.add_argument("--output", type=Path, default=Path("runs/week6/w6_skillops_m1_m3"))
    parser.add_argument("--controller-address", default="http://127.0.0.1:5060/api")
    parser.add_argument("--split", default="val", choices=("val", "test"))
    parser.add_argument("--cells", default="raw_stress,maintained_stress")
    parser.add_argument("--replicate-seeds", default="42")
    parser.add_argument("--backend", default=BACKEND_NAME)
    parser.add_argument("--output-root", type=Path, default=Path("runs/week6"))
    parser.add_argument("--run-name", default="w6_skillops_val_pilot")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--estimate-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.phase in ("evaluate", "compare"):
        load_env_file()
        cells = parse_csv(args.cells)
        seeds = parse_seeds(args.replicate_seeds)
        run_dir = args.output_root.resolve() / args.run_name
        if args.phase == "compare":
            result = compare(run_dir)
            print(f"M4 comparison complete: {run_dir / 'paired_summary.json'}")
            return
        if args.estimate_only:
            episode_count = 24 * len(cells) * len(seeds)
            print(
                f"Declared episodes={episode_count}. M4 seed-42 pilot estimate: 40-90 "
                "minutes, $0.7-$1.1. Each additional two-seed M5 stage is 96 episodes; "
                "use the observed M4 cost for the updated estimate."
            )
            return
        checks = performance_preflight(
            grasp_root=args.grasp_root,
            controller_address=args.controller_address,
            backend_name=args.backend,
            split=args.split,
            m1_m3_root=args.output,
        )
        run_dir.mkdir(parents=True, exist_ok=True)
        write_json(run_dir / "preflight.json", checks)
        if args.preflight_only:
            print(f"M4 preflight ready={checks['ready']}: {run_dir / 'preflight.json'}")
            raise SystemExit(0 if checks["ready"] else 2)
        if not checks["ready"]:
            raise SystemExit(f"M4 preflight failed; no model calls made: {run_dir / 'preflight.json'}")
        result = evaluate(
            grasp_root=args.grasp_root,
            controller_address=args.controller_address,
            backend_name=args.backend,
            split=args.split,
            cells=cells,
            seeds=seeds,
            m1_m3_root=args.output,
            run_dir=run_dir,
            resume=args.resume,
            preflight=checks,
        )
        print(f"M4 evaluation {result['status']}: {run_dir / 'summary.json'}")
        return
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    checks = preflight(args.skillops_root, args.grasp_root, args.source_run)
    write_json(output / "preflight.json", checks)
    if not checks["ready"]:
        raise SystemExit("M1-M3 preflight failed; inspect preflight.json")
    if args.preflight_only or args.phase == "preflight":
        print(f"M1-M3 preflight ready: {output / 'preflight.json'}")
        return

    clean_dir = output / "libraries" / "l_clean"
    clean_manifest = build_clean_fixture(args.source_run, clean_dir)
    write_json(output / "clean_fixture_manifest.json", clean_manifest)
    m1 = run_m1(clean_dir, output / "m1", args.skillops_root)
    write_json(output / "m1_roundtrip_summary.json", m1)
    if not m1["accepted"]:
        raise SystemExit("M1 failed; M2-M3 were not started")
    if args.phase == "roundtrip":
        print(f"M1 accepted: {output / 'm1_roundtrip_summary.json'}")
        return

    stress_dir = output / "libraries" / "l_stress"
    debt_manifest = build_stress_fixture(clean_dir, stress_dir)
    write_json(output / "controlled_debt_manifest.json", debt_manifest)
    m2 = run_m2(stress_dir, output / "m2", args.skillops_root, debt_manifest["debt"])
    write_json(output / "m2_maintenance_summary.json", m2)
    if not m2["accepted"]:
        raise SystemExit("M2 failed; M3 was not started")
    if args.phase == "fixture":
        print(f"M1-M2 accepted: {output / 'm2_maintenance_summary.json'}")
        return

    maintained_dir = output / "m2" / "maintained"
    m3 = run_m3(args.grasp_root, stress_dir, maintained_dir, output / "m3")
    write_json(output / "m3_boundary_parity.json", m3)
    summary = {
        "status": "m1_m3_accepted" if all(item["accepted"] for item in (m1, m2, m3)) else "failed",
        "m1_accepted": m1["accepted"],
        "m2_accepted": m2["accepted"],
        "m3_accepted": m3["accepted"],
        "fidelity": m1["fidelity"],
        "model_calls_made": False,
        "alfworld_episode_calls": 0,
        "long_running_experiment_started": False,
    }
    write_json(output / "summary.json", summary)
    if summary["status"] != "m1_m3_accepted":
        raise SystemExit("M3 failed")
    print(f"M1-M3 accepted: {output / 'summary.json'}")


if __name__ == "__main__":
    main()
