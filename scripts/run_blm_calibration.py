#!/usr/bin/env python3
"""Run the bounded, deterministic R1 BLM calibration stages.

This is intentionally a narrow research script.  It is not part of the
public ``skillstack`` CLI and never contacts a provider or downloads data.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import platform
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

from skillstack.experiments.blm_calibration import (
    CALIBRATION_ARMS,
    FIXTURE_SCOPE,
    MAX_STEPS,
    STEP_BUDGET_PER_PLAN_STEP,
    TASK,
    build_atom_census,
    evaluate_calibration_case,
    materialize_first_handoff_envelope,
    run_v2_calibration_arm,
    stable_projection,
)
from skillstack.tracing import JsonlTraceWriter


RUN_ID = "r1_05_calibration_run"
RUN_SCHEMA = "skillstack-r1-05-calibration-run-v1"
_UNREAD_ARMS = (
    "irrelevant_unread_information:selected_scores[0]",
    "irrelevant_unread_information:selected_native_skills[0]",
    "irrelevant_unread_information:flat_skill_context",
)
_EXECUTION_ARMS = (
    "reference",
    "crossed",
    "crossed_noop",
    "crossed_single_atom",
    "matched_carrier_control",
    "crossed_full_reference_restoration",
    *_UNREAD_ARMS,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    materialize = subparsers.add_parser("materialize-replay")
    materialize.add_argument("--output", type=Path, required=True)

    run = subparsers.add_parser("run")
    run.add_argument("--stage", choices=("r1-05",), required=True)
    run.add_argument("--output-root", type=Path, required=True)

    resume = subparsers.add_parser("resume")
    resume.add_argument("--run-id", default=RUN_ID)
    resume.add_argument("--output-root", type=Path, required=True)

    summarize = subparsers.add_parser("summarize")
    summarize.add_argument("--run-id", default=RUN_ID)
    summarize.add_argument("--output-root", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "materialize-replay":
        return _materialize_replay(args.output)
    if args.command == "run":
        return _run(args.output_root)
    if args.command == "resume":
        return _run(args.output_root, run_id=args.run_id, resume=True)
    return _summarize(args.output_root, args.run_id)


def _materialize_replay(output: Path) -> int:
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "skillstack-r1-02-envelope-set-v1",
        "state_scope": FIXTURE_SCOPE,
        "envelopes": [materialize_first_handoff_envelope(arm) for arm in ("reference", "crossed", "crossed_noop")],
    }
    _write_json(output, payload)
    return 0


def _run(output_root: Path, *, run_id: str = RUN_ID, resume: bool = False) -> int:
    output_root = output_root.expanduser().resolve()
    manifest = _manifest()
    if resume:
        _assert_stored_manifest_integrity(output_root, run_id)
        writer = JsonlTraceWriter.resume(output_root, run_id, expected_manifest=manifest)
    else:
        # The caller may pass either a parent directory or the requested run
        # directory; normalize to the writer's safe parent/run-id pair.
        if output_root.name == run_id:
            writer_parent = output_root.parent
        else:
            writer_parent = output_root
        writer = JsonlTraceWriter(writer_parent, "blm-calibration", run_id=run_id)
        writer.write_manifest(manifest)
    existing = _existing_episode_ids(writer.episodes_path)
    for repetition in range(3):
        for arm_id in _EXECUTION_ARMS:
            episode_id = f"r1-05:{arm_id}:{repetition}"
            if episode_id in existing:
                continue
            trace = run_v2_calibration_arm(arm_id)
            trace.update(
                {
                    "run_id": writer.run_id,
                    "episode_id": episode_id,
                    "calibration_stage": "r1-05",
                    "calibration_arm_id": arm_id,
                    "calibration_repetition": repetition,
                    "calibration_measurement_status": trace.get("blm_boundary", {}).get(
                        "validity", "invalid"
                    ),
                    "evidence_class": "verified_this_run",
                }
            )
            writer.append_episode(trace)
            existing.add(episode_id)
    _write_calibration_outputs(writer)
    return 0


def _summarize(output_root: Path, run_id: str) -> int:
    output_root = output_root.expanduser().resolve()
    writer = JsonlTraceWriter.resume(output_root, run_id)
    summary_path = writer.run_dir / "summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    else:
        _write_calibration_outputs(writer)
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _write_calibration_outputs(writer: JsonlTraceWriter) -> None:
    traces = _read_episodes(writer.episodes_path)
    expected_ids = [f"r1-05:{arm}:{rep}" for rep in range(3) for arm in _EXECUTION_ARMS]
    present_ids = {trace.get("episode_id") for trace in traces}
    complete = all(episode_id in present_ids for episode_id in expected_ids)
    reference = _first_trace(traces, "reference")
    census = build_atom_census(reference) if reference else None
    verdicts = _build_verdicts(traces, complete)
    counts = writer.recompute_status_counts()
    summary = {
        "schema_version": "skillstack-run-summary-v1",
        "run_id": writer.run_id,
        "stage": "r1-05",
        "run_identity_sha256": writer.manifest["run_identity_sha256"] if writer.manifest else None,
        "raw_episode_count": len(traces),
        "expected_episode_count": len(expected_ids),
        "all_expected_episodes_present": complete,
        "status_counts": counts,
        "calibration_valid_count": sum(
            1 for trace in traces
            if trace.get("calibration_measurement_status") == "valid"
        ),
        "calibration_invalid_count": sum(
            1 for trace in traces
            if trace.get("calibration_measurement_status") == "invalid"
        ),
        "verdict_count": len(verdicts),
        "verdicts_recomputed_from_raw": True,
        "state_scope": FIXTURE_SCOPE,
        "mid_episode_snapshot": "not_supported",
        "generated_at_utc_excluded_from_identity": True,
    }
    if not (writer.run_dir / "summary.json").exists():
        writer.write_summary(summary)
    _write_json(writer.run_dir / "verdicts.json", {"schema_version": "skillstack-blm-verdict-set-v1", "verdicts": verdicts})
    if census is not None:
        _write_json(writer.run_dir / "atom_census.json", census)


def _build_verdicts(traces: List[Dict[str, Any]], complete: bool) -> List[Dict[str, Any]]:
    reference = _first_trace(traces, "reference")
    crossed = _first_trace(traces, "crossed")
    single = _first_trace(traces, "crossed_single_atom")
    unread = {
        arm: _first_trace(traces, arm)
        for arm in _UNREAD_ARMS
    }
    identity_exact = bool(reference and single and _behavior_projection(reference) == _behavior_projection(single))
    cases: List[Dict[str, Any]] = [
        {
            "case_id": "known_identity_dependency",
            "measurement_status": "valid" if identity_exact else "abstained",
            "claim_id": "local-c1-identity-dependency",
            "claim": {"claim_id": "local-c1-identity-dependency", "type": "conformance", "explicit": True, "scope": "frozen heat fixture / SkillPlanExecutor identity atom"},
            "verdict_scope": "frozen heat fixture / SkillPlanExecutor identity atom",
            "gates_complete": complete,
            "observed_relation": "single_atom_exact" if identity_exact else "unknown",
            "reason_code": "local_identity_dependency_calibration",
            "evidence_refs": ["episodes.jsonl:r1-05:crossed_single_atom:0", "episodes.jsonl:r1-05:reference:0"],
        },
    ]
    for arm, trace in unread.items():
        no_change = bool(crossed and trace and _behavior_projection(crossed) == _behavior_projection(trace))
        atom = arm.split(":", 1)[1]
        cases.append(
            {
                "case_id": f"unread_probe:{atom}",
                "measurement_status": "valid" if no_change else "abstained",
                "claim_id": "local-c1-unread-domain",
                "claim": {"claim_id": "local-c1-unread-domain", "type": "conformance", "explicit": True, "scope": "current SkillPlanExecutor read domain"},
                "verdict_scope": "current SkillPlanExecutor read domain",
                "gates_complete": complete,
                "observed_relation": "no_change" if no_change else "unknown",
                "reason_code": "unread_negative_control",
                "evidence_refs": [f"episodes.jsonl:r1-05:{arm}:0"],
            }
        )
    cases.extend(
        [
            _diagnostic_case("declared_field_deleted", "invalid", "adapter_transport_nonconformance"),
            _diagnostic_case("opaque_native_or_flat", "valid", "consumer_semantic_read_unverified"),
            {
                "case_id": "synthetic_joint_only",
                "measurement_status": "valid",
                "claim_id": "synthetic-independent-sufficiency",
                "claim": {"claim_id": "synthetic-independent-sufficiency", "type": "synthetic_independent_sufficiency", "explicit": True, "scope": "test-only synthetic classifier record"},
                "verdict_scope": "test-only synthetic classifier record",
                "gates_complete": True,
                "synthetic_test_only": True,
                "observed_relation": "joint_only",
                "evidence_refs": ["synthetic:test-only"],
            },
            _diagnostic_case("invalid_donor_type_group", "invalid", "measurement_not_valid"),
            _diagnostic_case("replay_state_drift", "abstained", "replay_state_incomplete"),
            _diagnostic_case("no_op_drift", "invalid", "no_op_changed_result"),
            _diagnostic_case("interrupted_arm", "abstained", "incomplete_arm"),
            _diagnostic_case("budget_exhausted", "abstained", "budget_exhausted"),
        ]
    )
    return [evaluate_calibration_case(case) for case in cases]


def _diagnostic_case(case_id: str, status: str, diagnostic: str) -> Dict[str, Any]:
    return {
        "case_id": case_id,
        "measurement_status": status,
        "claim_id": "diagnostic-only",
        "claim": {"claim_id": "diagnostic-only", "type": "conformance", "explicit": True, "scope": "R1 bounded calibration diagnostics"},
        "verdict_scope": "R1 bounded calibration diagnostics",
        "gates_complete": True,
        "diagnostic": diagnostic,
        "reason_code": diagnostic,
        "observed_relation": "unknown",
        "evidence_refs": [f"diagnostic:{case_id}"],
    }


def _projection(trace: Mapping[str, Any]) -> Dict[str, Any]:
    return stable_projection(trace)


def _behavior_projection(trace: Mapping[str, Any]) -> Dict[str, Any]:
    report = trace.get("executor_report", {})
    return {
        "actions": trace.get("actions", []),
        "raw_observations": trace.get("raw_observations", []),
        "rewards": trace.get("rewards", []),
        "success": trace.get("success"),
        "stop_reason": trace.get("stop_reason"),
        "plan_skill_id": report.get("plan_skill_id"),
        "plan_steps": report.get("plan_steps"),
        "action_rationales": trace.get("action_rationales", []),
    }


def _first_trace(
    traces: Iterable[Mapping[str, Any]], arm_id: str
) -> Optional[Mapping[str, Any]]:
    for trace in traces:
        if trace.get("calibration_arm_id") == arm_id:
            return trace
    return None


def _read_episodes(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _existing_episode_ids(path: Path) -> set[str]:
    return {trace.get("episode_id") for trace in _read_episodes(path)}


def _manifest() -> Dict[str, Any]:
    return {
        "run_schema": RUN_SCHEMA,
        "stage": "r1-05",
        "state_scope": FIXTURE_SCOPE,
        "task": TASK,
        "arms": list(_EXECUTION_ARMS),
        "repetitions": 3,
        "top_k": 1,
        "max_steps": MAX_STEPS,
        "step_budget_per_plan_step": STEP_BUDGET_PER_PLAN_STEP,
        "oracle": "heat_environment_oracle_v1",
        "code_commit": _git_commit(),
        "calibration_module_sha256": _file_hash(Path(__file__).resolve().parents[1] / "src/skillstack/experiments/blm_calibration.py"),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "model_calls": 0,
        "network_calls": 0,
        "external_data": False,
    }


def _assert_stored_manifest_integrity(output_root: Path, run_id: str) -> None:
    manifest_path = output_root / run_id / "run_manifest.json"
    stored = json.loads(manifest_path.read_text(encoding="utf-8"))
    stored_identity = stored.get("run_identity_sha256")
    stable = {
        key: value
        for key, value in stored.items()
        if key not in {"created_at_utc", "run_identity_sha256"}
    }
    actual_identity = _sha256_json(stable)
    if not isinstance(stored_identity, str) or stored_identity != actual_identity:
        raise ValueError("Run manifest identity drift detected")


def _git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[1],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
