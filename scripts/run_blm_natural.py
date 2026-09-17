#!/usr/bin/env python3
"""Screen, dry-run, and (only after explicit approval) run R2 natural cases.

The implementation turn intentionally stops at ``dry-run``.  ``run`` requires
the literal approval token and never records credentials or HTTP headers.
"""

from __future__ import annotations

import argparse
import copy
import json
import platform
import random
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import yaml

from skillstack.blm import BLM_INTERVENTION_SCHEMA_V3, _hash_json
from skillstack.environments.alfworld_text import create_single_game_environment
from skillstack.execution import ReActExecutor
from skillstack.experiments.blm_natural import (
    NATURAL_BOUNDARY_ID,
    build_natural_context,
    build_natural_protocol,
    code_revision,
    dry_run_summary,
    natural_state_sha256,
    screen_natural_candidates,
)
from skillstack.library import load_static_library
from skillstack.llm import LlmClient, load_backend, load_env_file
from skillstack.retrieval import (
    DebugLexicalRetriever,
    NoSkillRetriever,
    RandomSkillRetriever,
    TaskSemanticRetriever,
)
from skillstack.runner import EpisodeRunner
from skillstack.tasks import load_task_manifest
from skillstack.tracing import JsonlTraceWriter


SCREEN_PATH = ROOT / "configs" / "blm" / "r2_candidate_screen.json"
PROTOCOL_PATH = ROOT / "configs" / "blm" / "r2_natural_case_protocol.yaml"
WEEK8 = ROOT / "report" / "week8"
PROMPT_PATH = ROOT / "configs" / "p0_react_prompt.txt"
APPROVAL_TOKEN = "R2-LIVE-APPROVED"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    screen = sub.add_parser("candidate-screen")
    screen.add_argument("--task-manifest", type=Path, default=ROOT / "configs" / "p0_tasks_picktwo.json")
    screen.add_argument("--data-root", type=Path, default=ROOT / "data" / "alfworld")
    screen.add_argument("--output", type=Path, default=SCREEN_PATH)
    dry = sub.add_parser("dry-run")
    dry.add_argument("--protocol", type=Path, default=PROTOCOL_PATH)
    dry.add_argument("--output", type=Path, default=None)
    run = sub.add_parser("run")
    run.add_argument("--protocol", type=Path, default=PROTOCOL_PATH)
    run.add_argument("--output-root", type=Path, default=ROOT / "runs")
    run.add_argument("--approve-live", default=None)
    resume = sub.add_parser("resume")
    resume.add_argument("--run-id", required=True)
    resume.add_argument("--output-root", type=Path, default=ROOT / "runs")
    summary = sub.add_parser("summarize")
    summary.add_argument("--run-id", required=True)
    summary.add_argument("--output-root", type=Path, default=ROOT / "runs")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "candidate-screen":
        screen = screen_natural_candidates(args.task_manifest.resolve(), args.data_root.resolve(), prompt_path=PROMPT_PATH)
        _write_json(args.output, screen)
        _write_json(WEEK8 / "r2_candidate_screen_evidence.json", screen)
        _write_text(ROOT / "docs" / "research" / "blm" / "r2_natural_candidate_register.md", _candidate_markdown(screen))
        print(json.dumps({"eligible_cases": screen["eligible_cases"], "excluded_cases": screen["excluded_cases"]}, indent=2))
        return 0
    if args.command == "dry-run":
        protocol = _load_or_build_protocol(args.protocol.resolve())
        _write_yaml(args.protocol.resolve(), protocol)
        dry = dry_run_summary(protocol)
        output = args.output or WEEK8 / "r2_dry_run_evidence.json"
        _write_json(output, dry)
        print(json.dumps(dry, indent=2, ensure_ascii=False))
        return 0
    if args.command == "run":
        if args.approve_live != APPROVAL_TOKEN:
            raise SystemExit(
                "R2 live provider is gated. Review dry-run evidence, then rerun with "
                f"--approve-live {APPROVAL_TOKEN}."
            )
        protocol = yaml.safe_load(args.protocol.read_text(encoding="utf-8"))
        run_id = _run_live(protocol, args.protocol.resolve(), args.output_root.resolve())
        print(json.dumps({"run_id": run_id}, indent=2))
        return 0
    if args.command == "resume":
        run_id = _resume_live(args.run_id, args.output_root.resolve())
        print(json.dumps({"run_id": run_id}, indent=2))
        return 0
    if args.command == "summarize":
        summary = _summarize_run(args.run_id, args.output_root.resolve())
        _write_json(args.output_root.resolve() / args.run_id / "diagnostics.json", summary)
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0
    raise SystemExit(f"unknown command: {args.command}")


def _load_or_build_protocol(path: Path) -> Dict[str, Any]:
    if SCREEN_PATH.is_file():
        screen = json.loads(SCREEN_PATH.read_text(encoding="utf-8"))
    else:
        screen = screen_natural_candidates(
            ROOT / "configs" / "p0_tasks_picktwo.json", ROOT / "data" / "alfworld", prompt_path=PROMPT_PATH
        )
        _write_json(SCREEN_PATH, screen)
        _write_json(WEEK8 / "r2_candidate_screen_evidence.json", screen)
        _write_text(ROOT / "docs" / "research" / "blm" / "r2_natural_candidate_register.md", _candidate_markdown(screen))
    return build_natural_protocol(screen)


def _run_live(protocol: Mapping[str, Any], protocol_path: Path, output_root: Path, run_id: Optional[str] = None) -> str:
    if not protocol.get("cases"):
        raise RuntimeError("No eligible natural case; live provider run is not allowed")
    load_env_file()
    backend = load_backend(protocol["backend"]["name"])
    budget = {
        "max_calls_per_run": protocol["live_caps"]["max_provider_calls"],
        "max_prompt_tokens_per_run": protocol["live_caps"]["max_prompt_tokens"],
        "max_completion_tokens_per_run": protocol["live_caps"]["max_completion_tokens"],
        "max_cost_usd_per_run": protocol["live_caps"]["max_cost_usd"],
    }
    client = LlmClient(backend, budget=budget)
    native_skills = load_static_library()
    task_by_case = {case["case_id"]: case["task"] for case in protocol["cases"]}
    label = "r2-natural"
    writer = JsonlTraceWriter(output_root, label, run_id=run_id) if run_id is None else JsonlTraceWriter.resume(output_root, run_id)
    if writer.manifest is None:
        manifest = {
            "experiment_id": "r2_blm_natural_case_increment",
            "run_id": writer.run_id,
            "protocol_path": str(protocol_path.relative_to(ROOT)),
            "protocol_sha256": _hash_json(protocol),
            "boundary_id": NATURAL_BOUNDARY_ID,
            "backend_name": backend.name,
            "model": backend.model,
            "temperature": 0,
            "structured_skills": True,
            "task_count": len(task_by_case),
            "arms": protocol["arms"],
            "repetitions": protocol["repetitions"],
            "code_revision": code_revision(),
            "host": {"platform": platform.system(), "architecture": platform.machine()},
            "credential_policy": "metadata only; no API key, Authorization, or HTTP headers",
            "interpretation": "R2 discovery only; no formal R3 verdict",
        }
        writer.write_manifest(manifest)
    completed = _completed_episode_ids(writer.episodes_path)
    repetition_order = list(range(int(protocol["repetitions"])))
    for repetition in repetition_order:
        arms = list(protocol["arms"])
        random.Random(int(protocol.get("shuffle_seed", 42)) + repetition).shuffle(arms)
        for case_id, task in task_by_case.items():
            for arm in arms:
                episode_id = f"r2:{case_id}:{arm}:{repetition}"
                if episode_id in completed:
                    continue
                retriever, request = _materialize_arm_request(
                    task, arm, native_skills, ROOT / "data" / "alfworld", client, case_id, protocol
                )
                executor = ReActExecutor(
                    client,
                    prompt_path=PROMPT_PATH,
                    max_tokens_per_step=512,
                    structured_skills=True,
                )
                runner = EpisodeRunner(ROOT / "data" / "alfworld", native_skills, retriever, executor)
                trace = runner.run(task, top_k=protocol["top_k"], max_steps=protocol["max_steps"], blm_intervention=request)
                trace.update({"run_id": writer.run_id, "episode_id": episode_id, "repetition": repetition, "case_id": case_id, "arm_id": arm, "seed": protocol.get("shuffle_seed", 42)})
                writer.append_episode(trace)
                completed.add(episode_id)
                if client.budget.calls >= int(protocol["live_caps"]["max_provider_calls"]):
                    return writer.run_id
    summary = _summarize_run(writer.run_id, output_root)
    writer.write_summary(summary)
    return writer.run_id


def _resume_live(run_id: str, output_root: Path) -> str:
    run_dir = output_root / run_id
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    protocol_path = ROOT / manifest["protocol_path"]
    protocol = yaml.safe_load(protocol_path.read_text(encoding="utf-8"))
    if _hash_json(protocol) != manifest["protocol_sha256"]:
        raise RuntimeError("protocol drift detected; refusing resume")
    return _run_live(protocol, protocol_path, output_root, run_id=run_id)


def _materialize_arm_request(task: Mapping[str, Any], arm: str, native_skills: List[Dict[str, Any]], data_root: Path, client: Any, case_id: str, protocol: Mapping[str, Any]):
    env, observation, info = create_single_game_environment(data_root, task["game_file"])
    try:
        prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
        context = build_natural_context(env, task, observation, info, native_skills, top_k=protocol["top_k"], max_steps=protocol["max_steps"], prompt_template=prompt_template, backend_name=client.backend.name, model=client.backend.model)
        state_sha = natural_state_sha256(context)
        responses = {
            "reference": TaskSemanticRetriever().retrieve(task, observation, native_skills, protocol["top_k"]),
            "crossed": DebugLexicalRetriever().retrieve(task, observation, native_skills, protocol["top_k"]),
            "random3": RandomSkillRetriever(seed=3).retrieve(task, observation, native_skills, protocol["top_k"]),
            "no_skill": NoSkillRetriever().retrieve(task, observation, native_skills, protocol["top_k"]),
        }
    finally:
        env.close()
    base = {"schema_version": BLM_INTERVENTION_SCHEMA_V3, "case_id": case_id, "arm_id": arm, "operation": "capture", "atom_or_group": None, "expected_state_sha256": None, "donor": None}
    if arm == "reference":
        return TaskSemanticRetriever(), base
    if arm == "crossed":
        return DebugLexicalRetriever(), base
    if arm == "no-skill-ablation":
        return NoSkillRetriever(), base
    donor_name, donor_kind, donor_response = "debug_lexical_top_k", "lexical_crossed", responses["crossed"]
    atom = "top_candidate_group"
    if arm == "crossed-noop":
        donor_kind, donor_response = "producer_output", responses["crossed"]
    elif arm == "crossed+top-candidate":
        donor_name, donor_kind, donor_response = "task_semantic_top_k", "task_semantic_reference", responses["reference"]
    elif arm == "matched-carrier":
        donor_name, donor_kind, donor_response = "matched_carrier_static", "matched_nonreference", _matched_carrier_response(
            responses["reference"], responses["crossed"], responses["random3"], native_skills
        )
    elif arm == "crossed+full-reference":
        donor_name, donor_kind, donor_response, atom = "task_semantic_top_k", "task_semantic_reference", responses["reference"], "full_handoff_group"
    elif arm == "score-negative-control":
        donor_name, donor_kind, donor_response, atom = "task_semantic_top_k", "task_semantic_reference", responses["reference"], "selected_scores[0]"
    base.update({"operation": "copy_group_from_donor" if atom in {"top_candidate_group", "full_handoff_group"} else "copy_atom_from_donor", "atom_or_group": atom, "expected_state_sha256": state_sha, "donor": {"kind": donor_kind, "producer_name": donor_name, "task_id": task["task_id"], "task_family": task["task_family"], "state_sha256": state_sha, "retrieval_response": donor_response}})
    return DebugLexicalRetriever(), base


def _matched_carrier_response(reference: Mapping[str, Any], crossed: Mapping[str, Any], random3: Mapping[str, Any], native_skills: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create a fixed, traceable carrier control without reference semantics."""

    reference_top = reference.get("ranked_candidates", [{}])[0].get("skill_id")
    crossed_top = crossed.get("ranked_candidates", [{}])[0].get("skill_id")
    reference_payload = reference.get("ranked_candidates", [{}])[0].get("native_payload", "")
    target_sections = _section_count(reference_payload)
    candidates_by_id = {artifact["skill_id"]: artifact for artifact in native_skills}
    available = [
        artifact
        for artifact in native_skills
        if artifact["skill_id"] not in {reference_top, crossed_top}
    ]
    available.sort(
        key=lambda artifact: (
            abs(_section_count(artifact["native_payload"]) - target_sections),
            abs(len(artifact["native_payload"]) - len(reference_payload)),
            artifact["skill_id"],
        )
    )
    if not available:
        raise RuntimeError("No non-reference/non-crossed matched carrier artifact")
    selected = available[0]
    second = next(
        (artifact for artifact in available[1:] if artifact["skill_id"] != selected["skill_id"]),
        selected,
    )
    return {
        "retriever_name": "matched_carrier_static",
        "ranked_candidates": [
            {"skill_id": selected["skill_id"], "score": 0.0, "native_payload": selected["native_payload"]},
            {"skill_id": second["skill_id"], "score": -1.0, "native_payload": second["native_payload"]},
        ],
        "raw_output": {
            "selection_policy": "fixed_nonreference_noncrossed_native_artifact",
            "source_producer": random3.get("retriever_name"),
            "target_section_count": target_sections,
            "byte_length_distance": abs(len(selected["native_payload"]) - len(reference_payload)),
        },
        "warnings": [],
    }


def _section_count(payload: str) -> int:
    return len(re.findall(r"^##\s+", payload, flags=re.MULTILINE))


def _completed_episode_ids(path: Path) -> set:
    if not path.exists():
        return set()
    return {json.loads(line).get("episode_id") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def _summarize_run(run_id: str, output_root: Path) -> Dict[str, Any]:
    path = output_root / run_id / "episodes.jsonl"
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()] if path.exists() else []
    by_arm: Dict[str, Dict[str, Any]] = {}
    for record in records:
        arm = record.get("arm_id", "unknown")
        bucket = by_arm.setdefault(arm, {"planned": 0, "completed": 0, "valid": 0, "invalid": 0, "abstained": 0, "success_count": 0, "action_count": 0, "provider_calls": 0, "stop_reasons": {}})
        bucket["completed"] += 1
        bucket["valid"] += int(record.get("measurement_status") == "valid")
        bucket["invalid"] += int(record.get("measurement_status") == "invalid")
        bucket["abstained"] += int(record.get("measurement_status") == "abstained")
        bucket["success_count"] += int(bool(record.get("success")))
        bucket["action_count"] += len(record.get("actions", []))
        bucket["provider_calls"] += len(record.get("executor_report", {}).get("llm_calls", []))
        reason = record.get("stop_reason", "unknown")
        bucket["stop_reasons"][reason] = bucket["stop_reasons"].get(reason, 0) + 1
    return {"schema_version": "skillstack-blm-r2-diagnostics-v1", "run_id": run_id, "episode_count": len(records), "arms": by_arm, "claim_boundary": "R2 discovery; no formal falsified/support verdict", "evidence_class": "verified_this_run"}


def _candidate_markdown(screen: Mapping[str, Any]) -> str:
    lines = ["# R2 自然候选登记", "", "本登记只记录零模型 Producer/adapter 预筛选；不把历史 run 当作 R2 live outcome，也不产生 R3 verdict。", "", f"- boundary：`{screen['boundary_id']}`", f"- evidence class：`{screen['evidence_class']}`", f"- eligible cases：`{len(screen['eligible_cases'])}`", ""]
    for record in screen.get("tasks", []):
        lines.extend([f"## {record['case_id']}", "", f"- task：`{record['task']['task_id']}`", f"- instruction：{record['task']['task_instruction']}", f"- environment runtime：`{record['environment_runtime']}`", f"- carrier difference：`{record['carrier_difference']}`", f"- eligible：`{record['eligible']}`", f"- gate reasons：`{record['gate_reasons'] or ['none']}`", f"- TaskSemantic label assistance：`task_family` only; `expected_skill_id` read = `False`; deployment-unassisted = `False`", ""])
        for label in ("lexical", "task_semantic"):
            output = record["producers"][label]
            lines.append(f"- {label}: {[candidate['skill_id'] for candidate in output['retrieval_response']['ranked_candidates']]} / input `{output['hashes']['execution_input_sha256']}`")
        lines.append("")
    lines.extend(["## Claim boundary", "", "`historical_evidence` 仅用于冻结候选集合；若首次 reset 不能重建，候选保持 `not_verified`，不得进入 live arm。自然发现必须交给独立 R3 confirmation。", ""])
    return "\n".join(lines)


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_yaml(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(dict(value), allow_unicode=True, sort_keys=False), encoding="utf-8")


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
