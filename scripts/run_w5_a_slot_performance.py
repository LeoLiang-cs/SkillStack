#!/usr/bin/env python3
"""Run the strict-disjoint A0/A1 AgentBench performance experiment.

The long experiment is deliberately phase-based and checkpointed per task:

1. --preflight-only verifies sources, credentials, Docker and AgentBench.
2. --estimate-only prints task-episode bounds without making model calls.
3. --phase evidence records the immutable 13/13 initial evidence snapshot.
4. --phase cell --cell a0|a1 proposes and gates at most three ADD candidates.
5. --phase compare creates the paired, model-free result summary.

No validation or test split is read by the execution phases.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import socket
import subprocess
import sys
import time
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skillstack.adapters.grasp_to_proposal import adapt_grasp_output
from skillstack.adapters.proposal_to_grasp import envelope_to_grasp_add
from skillstack.adapters.skillrl_to_grasp import adapt_skillrl_output
from skillstack.experiments.agentbench_performance import (
    atomic_write_json,
    checkpoint_name,
    execution_budget,
    json_safe,
    read_json,
    sanitize_tool_history,
    with_effectiveness_sensitivity,
)
from skillstack.experiments.grasp_gate_contract import run_grasp_gate_contract
from skillstack.experiments.grasp_source import (
    AGENTBENCH_RELATIVE,
    EXPECTED_GRASP_COMMIT,
    load_grasp_alfworld_manifest,
)
from skillstack.experiments.skillrl_source import (
    EXPECTED_SKILLRL_COMMIT,
    parse_substituted_skillrl_response,
    prepare_skillrl_request,
)
from skillstack.llm import LlmClient, load_backends, load_env_file


BACKEND_NAME = "deepseek_v4_flash"
DEFAULT_GRASP_ROOT = Path("/Users/leo/Project/Research/USC/FORTIS/_external/week5/GRASP")
DEFAULT_SKILLRL_ROOT = Path("/Users/leo/Project/Research/USC/FORTIS/_external/week5/SkillRL")
DEFAULT_OUTPUT_ROOT = ROOT / "runs" / "week5"
DEFAULT_RUN_NAME = "w5_a_slot_seed2_deepseek_flash"


class RecordingAgent:
    """AgentBench-compatible DeepSeek agent with raw per-call accounting."""

    def __init__(self, client: LlmClient, *, max_tokens: int = 512, temperature: float = 0.0):
        self.client = client
        self.model_name = client.backend.model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._calls: List[Dict[str, Any]] = []
        self._lock = Lock()

    def inference(self, history, tools=None):
        raw_messages = [_message_dict(message) for message in history]
        messages, sanitization_events = sanitize_tool_history(raw_messages)
        response = self.client.chat(
            messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            tools=json_safe(tools) if tools else None,
        )
        record = {
            "request": {
                "messages": deepcopy(messages),
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "tools": json_safe(tools) if tools else None,
                "history_sanitization": sanitization_events,
            },
            "raw_content": response["content"],
            "raw_message": deepcopy(response["message"]),
            "usage": deepcopy(response["usage"]),
            "latency_seconds": response["latency_seconds"],
            "estimated_cost_usd": self.client.estimate_cost_usd(response["usage"]),
        }
        with self._lock:
            self._calls.append(record)
        if response["message"].get("tool_calls"):
            return response["message"]
        return response["content"]

    def drain_calls(self) -> List[Dict[str, Any]]:
        with self._lock:
            calls = self._calls
            self._calls = []
        return calls


def main() -> int:
    args = _parse_args()
    if args.backend != BACKEND_NAME:
        raise SystemExit(
            f"Week5 is frozen to --backend {BACKEND_NAME}; received {args.backend!r}."
        )
    load_env_file()

    if args.estimate_only:
        print(json.dumps(execution_budget(args.candidate_cap, 2), indent=2))
        return 0

    manifest = load_grasp_alfworld_manifest(args.grasp_root)
    run_dir = args.output_root.resolve() / args.run_name
    if args.phase == "compare" and not args.preflight_only:
        return _write_paired_summary(args, manifest, run_dir)
    preflight = _preflight(args, manifest, check_service=True)
    if args.preflight_only:
        print(json.dumps(preflight, indent=2))
        return 0 if preflight["ready"] else 2
    if not preflight["ready"]:
        print(json.dumps(preflight, indent=2), file=sys.stderr)
        raise SystemExit("Preflight failed; no model calls were made.")

    if args.phase == "evidence":
        _prepare_run_dir(run_dir, resume=args.resume)
        return _collect_evidence(args, manifest, preflight, run_dir)
    if args.phase == "cell":
        if not args.cell:
            raise SystemExit("--phase cell requires --cell a0 or --cell a1")
        if not run_dir.exists():
            raise SystemExit(f"Evidence run does not exist: {run_dir}")
        return _run_cell(args, manifest, run_dir)
    raise AssertionError(args.phase)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grasp-root", type=Path, default=DEFAULT_GRASP_ROOT)
    parser.add_argument("--skillrl-root", type=Path, default=DEFAULT_SKILLRL_ROOT)
    parser.add_argument("--controller-address", default="http://127.0.0.1:5060/api")
    parser.add_argument("--backend", default=BACKEND_NAME)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--run-name", default=DEFAULT_RUN_NAME)
    parser.add_argument("--candidate-cap", type=int, default=3, choices=(1, 2, 3))
    parser.add_argument("--phase", choices=("evidence", "cell", "compare"), default="evidence")
    parser.add_argument("--cell", choices=("a0", "a1"))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--estimate-only", action="store_true")
    return parser.parse_args()


def _prepare_run_dir(run_dir: Path, *, resume: bool) -> None:
    if run_dir.exists() and not resume:
        raise SystemExit(f"Run directory exists; use --resume: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=True)


def _preflight(args, manifest: Mapping[str, Any], *, check_service: bool) -> Dict[str, Any]:
    backend = load_backends()[args.backend]
    skillrl_commit = _git_commit(args.skillrl_root)
    docker = _command_status(["docker", "info", "--format", "{{.ServerVersion}}"])
    ports = {str(port): _tcp_open("127.0.0.1", port) for port in (5060, 5061)}
    service: Dict[str, Any] = {"checked": False}
    if check_service and ports["5060"]:
        try:
            native = _native_modules(args.grasp_root)
            task_client = native["TaskClient"](
                name="alfworld-skill", controller_address=args.controller_address
            )
            indices = task_client.get_indices()
            available_ids = {str(index) for index in indices}
            required_ids = set(manifest["strict_dev_split"]["history_probe_task_ids"])
            required_ids.update(manifest["strict_dev_split"]["proposal_task_ids"])
            missing_required_ids = sorted(required_ids - available_ids)
            service = {
                "checked": True,
                "reachable": True,
                "index_count": len(indices),
                "required_dev_index_count": len(required_ids),
                "missing_required_dev_ids": missing_required_ids,
                "required_dev_ids_available": not missing_required_ids,
            }
        except Exception as error:
            service = {
                "checked": True,
                "reachable": False,
                "error_type": type(error).__name__,
                "error": str(error),
            }
    key_present = bool(os.environ.get(backend.api_key_env))
    ready = all(
        (
            manifest["grasp_commit"] == EXPECTED_GRASP_COMMIT,
            skillrl_commit == EXPECTED_SKILLRL_COMMIT,
            key_present,
            docker["ok"],
            ports["5060"],
            ports["5061"],
            service.get("reachable", False),
            service.get("required_dev_ids_available", False),
        )
    )
    return {
        "ready": ready,
        "model_calls_made": False,
        "backend": args.backend,
        "model": backend.model,
        "api_key_env": backend.api_key_env,
        "api_key_present": key_present,
        "grasp_commit": manifest["grasp_commit"],
        "skillrl_commit": skillrl_commit,
        "docker": docker,
        "ports": ports,
        "agentbench_service": service,
    }


def _collect_evidence(args, manifest, preflight, run_dir: Path) -> int:
    manifest_path = run_dir / "run_manifest.json"
    if not manifest_path.exists():
        atomic_write_json(
            manifest_path,
            {
                "experiment_id": "w5_strict_disjoint_a_slot_performance",
                "created_at_utc": _now(),
                "backend": args.backend,
                "provider_fidelity": "provider_substituted_deepseek_flash",
                "grasp_manifest": manifest,
                "skillrl_commit": EXPECTED_SKILLRL_COMMIT,
                "controller_address": args.controller_address,
                "candidate_cap": args.candidate_cap,
                "contrastive_revision": False,
                "matched_action": "ADD_only",
                "budget": execution_budget(args.candidate_cap, 2),
                "preflight": preflight,
            },
        )
    else:
        _verify_resume_manifest(read_json(manifest_path), args, manifest)

    native = _native_modules(args.grasp_root)
    backend = load_backends()[args.backend]
    agent = RecordingAgent(LlmClient(backend), max_tokens=512, temperature=0.0)
    repository = native["SkillRepository"](
        base_dir=_agentbench_root(args.grasp_root) / "skills/alfworld/base",
        learned_dir=run_dir / "starting_library" / "learned",
    )
    task_client = native["TaskClient"](
        name="alfworld-skill", controller_address=args.controller_address
    )
    strict = manifest["strict_dev_split"]
    groups = (
        ("history_probe_source", strict["history_probe_source"]),
        ("proposal_source", strict["proposal_source"]),
    )
    all_entries: Dict[str, List[Dict[str, Any]]] = {}
    for group_name, records in groups:
        sample_entries = []
        for position, record in enumerate(records, start=1):
            checkpoint = run_dir / "evidence" / group_name / (
                f"{position:02d}_" + checkpoint_name(record["task_id"]) + ".json"
            )
            payload = _run_task_checkpoint(
                checkpoint=checkpoint,
                record=record,
                repository=repository,
                agent=agent,
                task_client=task_client,
                native=native,
                resume=args.resume,
                label=group_name,
            )
            sample_entries.append(payload)
            print(
                f"[{group_name} {position}/{len(records)}] "
                f"task={record['task_id']} correct={payload['entry']['is_correct']}"
            )
        all_entries[group_name] = sample_entries

    summary = {
        "status": "complete",
        "completed_at_utc": _now(),
        "same_snapshot_for_a0_a1": True,
        "history_probe_source": _group_summary(all_entries["history_probe_source"]),
        "proposal_source": _group_summary(all_entries["proposal_source"]),
        "starting_library": repository.snapshot(),
        "starting_library_sha256": _directory_hash(repository.base_dir),
    }
    atomic_write_json(run_dir / "evidence_summary.json", summary)
    print(json.dumps({"run_directory": str(run_dir), **summary}, indent=2))
    return 0


def _run_cell(args, manifest, run_dir: Path) -> int:
    evidence_summary_path = run_dir / "evidence_summary.json"
    if not evidence_summary_path.exists():
        raise SystemExit("Evidence is incomplete; run --phase evidence first.")
    _verify_resume_manifest(read_json(run_dir / "run_manifest.json"), args, manifest)
    native = _native_modules(args.grasp_root)
    backend = load_backends()[args.backend]
    cell_dir = run_dir / "cells" / args.cell
    cell_dir.mkdir(parents=True, exist_ok=True)

    proposal_path = cell_dir / "proposal_output.json"
    if proposal_path.exists():
        proposal_output = read_json(proposal_path)
        print(f"[resume] loaded {args.cell} proposal output")
    else:
        proposal_entries = _load_group_entries(run_dir / "evidence" / "proposal_source")
        if args.cell == "a0":
            proposal_output = _propose_a0(args, backend, native, cell_dir, proposal_entries)
        else:
            proposal_output = _propose_a1(args, backend, proposal_entries)
        atomic_write_json(proposal_path, proposal_output)

    envelopes = [
        proposal for proposal in proposal_output["adapter_batch"]["proposals"]
        if proposal.get("parse_status") == "valid"
        and proposal.get("normalized_action") == "ADD"
    ][: args.candidate_cap]
    candidate_results = []
    for index, envelope in enumerate(envelopes, start=1):
        print(f"[{args.cell}] candidate {index}/{len(envelopes)}: {envelope['proposal_id']}")
        candidate_results.append(
            _evaluate_candidate(args, native, backend, run_dir, cell_dir, envelope)
        )

    compact_results = [_compact_candidate_result(result) for result in candidate_results]
    summary = {
        "status": "complete",
        "completed_at_utc": _now(),
        "cell": args.cell,
        "provider_fidelity": "provider_substituted_deepseek_flash",
        "proposal_candidate_count_raw": len(proposal_output["adapter_batch"]["proposals"]),
        "candidate_count_evaluated": len(candidate_results),
        "native_admitted_count": sum(
            bool(result.get("gate", {}).get("native_admitted")) for result in candidate_results
        ),
        "effectiveness_admitted_count": sum(
            bool(result.get("gate", {}).get("effectiveness_admitted"))
            for result in candidate_results
        ),
        "candidate_results": compact_results,
        "proposal_accounting": _accounting(proposal_output.get("model_calls", [])),
        "probe_accounting": _merge_accountings(
            result.get("accounting", {}) for result in candidate_results
        ),
    }
    atomic_write_json(cell_dir / "summary.json", summary)
    print(json.dumps({"run_directory": str(run_dir), **summary}, indent=2))
    return 0


def _write_paired_summary(args, manifest, run_dir: Path) -> int:
    if not run_dir.exists():
        raise SystemExit(f"Run directory does not exist: {run_dir}")
    _verify_resume_manifest(read_json(run_dir / "run_manifest.json"), args, manifest)
    evidence = read_json(run_dir / "evidence_summary.json")
    cells = {}
    for cell in ("a0", "a1"):
        path = run_dir / "cells" / cell / "summary.json"
        if not path.exists():
            raise SystemExit(f"Cell is incomplete: {path}")
        cells[cell] = read_json(path)
    paired = {
        "status": "complete",
        "completed_at_utc": _now(),
        "experiment_id": "w5_strict_disjoint_a_slot_performance",
        "evidence_is_shared": bool(evidence.get("same_snapshot_for_a0_a1")),
        "history_probe_task_ids": evidence["history_probe_source"]["task_ids"],
        "proposal_task_ids": evidence["proposal_source"]["task_ids"],
        "provider_fidelity": "provider_substituted_deepseek_flash",
        "candidate_cap": args.candidate_cap,
        "contrastive_revision": False,
        "a0": _cell_comparison_fields(cells["a0"]),
        "a1": _cell_comparison_fields(cells["a1"]),
        "interpretation_boundary": (
            "One strict-disjoint seed measures paired component behavior under a "
            "substituted DeepSeek writer; it does not establish general superiority."
        ),
    }
    atomic_write_json(run_dir / "paired_summary.json", paired)
    print(json.dumps({"run_directory": str(run_dir), **paired}, indent=2))
    return 0


def _cell_comparison_fields(summary: Mapping[str, Any]) -> Dict[str, Any]:
    gates = [item.get("gate") or {} for item in summary.get("candidate_results", [])]
    return {
        "candidate_count_evaluated": summary.get("candidate_count_evaluated", 0),
        "native_admitted_count": summary.get("native_admitted_count", 0),
        "effectiveness_admitted_count": summary.get("effectiveness_admitted_count", 0),
        "total_fixes": sum(int(gate.get("fixes", 0)) for gate in gates),
        "total_regressions": sum(int(gate.get("regressions", 0)) for gate in gates),
        "proposal_accounting": summary.get("proposal_accounting", {}),
        "probe_accounting": summary.get("probe_accounting", {}),
    }


def _propose_a0(args, backend, native, cell_dir: Path, evidence_entries):
    client = LlmClient(backend)
    agent = RecordingAgent(client, max_tokens=2048, temperature=0.8)
    repository = native["SkillRepository"](
        base_dir=_agentbench_root(args.grasp_root) / "skills/alfworld/base",
        learned_dir=cell_dir / "proposal_library" / "learned",
    )
    updater = native["SkillUpdater"](
        agent=agent, max_proposals=args.candidate_cap, max_learned_skills=10
    )
    entries = [deepcopy(item["entry"]) for item in evidence_entries]
    labels, new_labels = updater.classify_failures(entries, prev_taxonomy={})
    diagnoses = updater.diagnose(entries, repository, failure_labels=labels)
    groups = native["SkillCycleRunner"]._group_entries_by_failure_mode(entries, labels)
    raw_proposals: List[Dict[str, Any]] = []
    selected_group = None
    if groups:
        failure_mode, group = groups[0]
        selected_group = {
            "failure_mode": failure_mode,
            "sample_ids": [str(entry["sample_id"]) for entry in group],
        }
        group_ids = set(selected_group["sample_ids"])
        group_diagnosis = {key: value for key, value in diagnoses.items() if key in group_ids}
        other_failing = [
            dict(entry, _failure_label=labels.get(str(entry["sample_id"]), "unknown"))
            for entry in entries
            if not entry.get("is_correct") and str(entry["sample_id"]) not in group_ids
        ]
        raw_proposals = updater.propose(
            group,
            repository,
            prev_results=None,
            skill_effectiveness={},
            failure_mode=failure_mode if failure_mode != "unknown" else None,
            diagnosis=group_diagnosis or None,
            other_failing=other_failing or None,
        )
    validated = updater.validate(raw_proposals, repository)
    calls = agent.drain_calls()
    usage = _sum_usage(calls)
    adapter_batch = adapt_grasp_output(
        validated[: args.candidate_cap],
        triggering_evidence_ids=[
            str(item["entry"]["sample_id"])
            for item in evidence_entries if not item["entry"]["is_correct"]
        ],
        writer_model=backend.model,
        decoding={"temperature": 0.8, "provider_substituted": True},
        call_usage=usage,
    )
    return {
        "cell": "a0",
        "producer": "GRASP classify_diagnose_group_propose",
        "failure_labels": labels,
        "new_failure_labels": new_labels,
        "diagnoses": diagnoses,
        "all_groups": [
            {"failure_mode": label, "sample_ids": [str(e["sample_id"]) for e in group]}
            for label, group in groups
        ],
        "selected_group": selected_group,
        "raw_proposals": raw_proposals,
        "native_validated_proposals": validated,
        "model_calls": calls,
        "adapter_batch": adapter_batch,
    }


def _propose_a1(args, backend, evidence_entries):
    failed = [_to_skillrl_failure(item["entry"]) for item in evidence_entries if not item["entry"]["is_correct"]]
    current_skills = {"general_skills": [], "task_specific_skills": {}}
    if not failed:
        return {
            "cell": "a1",
            "producer": "SkillRL analyze_failures prompt_parser",
            "failed_trajectories": [],
            "model_calls": [],
            "adapter_batch": adapt_skillrl_output(
                [], task_type="alfworld", triggering_evidence_ids=[], writer_model=backend.model
            ),
        }
    prepared = prepare_skillrl_request(args.skillrl_root, failed, current_skills)
    client = LlmClient(backend)
    response = client.chat(
        [{"role": "user", "content": prepared["prompt"]}],
        max_tokens=prepared["max_completion_tokens"],
        temperature=0.0,
    )
    parsed = parse_substituted_skillrl_response(
        args.skillrl_root, response["content"], current_skills
    )
    usage = response["usage"]
    calls = [{
        "request": {
            "messages": [{"role": "user", "content": prepared["prompt"]}],
            "max_tokens": prepared["max_completion_tokens"],
            "temperature": 0.0,
        },
        "raw_content": response["content"],
        "usage": usage,
        "latency_seconds": response["latency_seconds"],
        "estimated_cost_usd": client.estimate_cost_usd(usage),
    }]
    adapter_batch = adapt_skillrl_output(
        parsed["native_return"],
        task_type="alfworld",
        triggering_evidence_ids=[str(item["entry"]["sample_id"]) for item in evidence_entries if not item["entry"]["is_correct"]],
        writer_model=backend.model,
        decoding={"temperature": 0.0, "provider_substituted": True},
        call_usage=usage,
    )
    return {
        "cell": "a1",
        "producer": "SkillRL analyze_failures prompt_parser",
        "failed_trajectories": failed,
        "prepared_request": prepared,
        "raw_model_content": response["content"],
        "released_parser_result": parsed,
        "model_calls": calls,
        "adapter_batch": adapter_batch,
    }


def _evaluate_candidate(args, native, backend, run_dir: Path, cell_dir: Path, envelope):
    candidate_id = checkpoint_name(envelope["proposal_id"])
    result_path = cell_dir / "candidates" / candidate_id / "result.json"
    if result_path.exists():
        print(f"[resume] loaded completed candidate {envelope['proposal_id']}")
        return read_json(result_path)

    base_repo = native["SkillRepository"](
        base_dir=_agentbench_root(args.grasp_root) / "skills/alfworld/base",
        learned_dir=cell_dir / "candidates" / candidate_id / "starting_learned",
    )
    updater = native["SkillUpdater"](
        agent=None, max_proposals=args.candidate_cap, max_learned_skills=10
    )
    native_proposal = envelope_to_grasp_add(envelope)
    provenance = native_proposal.pop("_skillstack_provenance", {})
    validated = updater.validate([native_proposal], base_repo)
    if len(validated) != 1:
        result = {
            "proposal_id": envelope["proposal_id"],
            "status": "native_validation_rejected",
            "envelope": envelope,
            "native_proposal": native_proposal,
            "provenance": provenance,
            "model_calls": [],
        }
        atomic_write_json(result_path, result)
        return result

    history_entries = _load_group_entries(run_dir / "evidence" / "history_probe_source")
    records = [item["record"] for item in history_entries]
    reference = {
        str(item["entry"]["sample_id"]): not bool(item["entry"]["is_correct"])
        for item in history_entries
    }
    baseline_dir = cell_dir / "candidates" / candidate_id / "baseline"
    candidate_dir = cell_dir / "candidates" / candidate_id / "candidate"
    baseline = _run_probe(args, native, backend, base_repo, records, baseline_dir)

    forked = base_repo.fork()
    try:
        winner = dict(validated[0])
        winner["_provenance"] = {
            "skillstack": provenance,
            "strict_disjoint_candidate": True,
        }
        applied = updater.apply([winner], forked)
        candidate = _run_probe(args, native, backend, forked, records, candidate_dir)
        fork_snapshot = forked.snapshot()
    finally:
        forked.cleanup()

    baseline_gate = _probe_gate_inputs(baseline)
    candidate_gate = _probe_gate_inputs(candidate)
    gate = run_grasp_gate_contract(
        reference,
        baseline_runner=lambda: baseline_gate,
        candidate_runner=lambda: candidate_gate,
    )
    gate = with_effectiveness_sensitivity(gate)
    all_calls = [
        call for payload in (baseline + candidate) for call in payload.get("model_calls", [])
    ]
    result = {
        "proposal_id": envelope["proposal_id"],
        "status": "gate_complete",
        "envelope": envelope,
        "native_proposal": native_proposal,
        "provenance": provenance,
        "native_validated": validated,
        "native_applied_to_isolated_fork": applied,
        "starting_repository_snapshot": base_repo.snapshot(),
        "candidate_fork_snapshot": fork_snapshot,
        "reference_failure_map": reference,
        "baseline_probe": _probe_summary(baseline),
        "candidate_probe": _probe_summary(candidate),
        "baseline_checkpoint_directory": str(baseline_dir),
        "candidate_checkpoint_directory": str(candidate_dir),
        "gate": gate,
        "accounting": _accounting(all_calls),
    }
    atomic_write_json(result_path, result)
    return result


def _run_probe(args, native, backend, repository, records, checkpoint_dir: Path):
    agent = RecordingAgent(LlmClient(backend), max_tokens=512, temperature=0.0)
    task_client = native["TaskClient"](
        name="alfworld-skill", controller_address=args.controller_address
    )
    payloads = []
    for position, record in enumerate(records, start=1):
        checkpoint = checkpoint_dir / (checkpoint_name(record["task_id"]) + ".json")
        payload = _run_task_checkpoint(
            checkpoint=checkpoint,
            record=record,
            repository=repository,
            agent=agent,
            task_client=task_client,
            native=native,
            resume=True,
            label=checkpoint_dir.name,
        )
        payloads.append(payload)
        print(
            f"[{checkpoint_dir.parent.name}/{checkpoint_dir.name} {position}/{len(records)}] "
            f"task={record['task_id']} correct={payload['entry']['is_correct']}"
        )
    return payloads


def _run_task_checkpoint(*, checkpoint, record, repository, agent, task_client, native, resume, label):
    if checkpoint.exists():
        if not resume:
            raise SystemExit(f"Checkpoint exists; use --resume: {checkpoint}")
        return read_json(checkpoint)
    sample = deepcopy(record["native_record"])
    attempt = 0
    while True:
        result = task_client.run_sample(sample["id"], native["SkillAwareAgent"](agent, repository))
        if result.error != native["TaskError"].NOT_AVAILABLE.value:
            break
        wait_seconds = min(5 * (attempt + 1), 30)
        print(f"[{label}] task {record['task_id']} unavailable; retry in {wait_seconds}s")
        time.sleep(wait_seconds)
        attempt += 1
    is_correct = native["score_result"](sample, result, native["eval_fn"])
    entry = native["make_log_entry"](
        sample, result, is_correct, update_cycle=0, skill_snapshot=repository.snapshot()
    )
    calls = agent.drain_calls()
    payload = {
        "record": record,
        "entry": entry,
        "model_calls": calls,
        "accounting": _accounting(calls),
        "completed_at_utc": _now(),
    }
    if result.error:
        failed_path = checkpoint.parent / ".failed" / (
            checkpoint.stem + "_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json"
        )
        atomic_write_json(failed_path, payload)
        raise RuntimeError(
            f"Task {record['task_id']} ended with {result.error}; diagnostic saved to {failed_path}. "
            "The formal checkpoint was not written."
        )
    atomic_write_json(checkpoint, payload)
    return read_json(checkpoint)


def _native_modules(grasp_root: Path) -> Dict[str, Any]:
    agentbench = _agentbench_root(grasp_root)
    if str(agentbench) not in sys.path:
        sys.path.insert(0, str(agentbench))
    cycle = importlib.import_module("src.skills.cycle")
    task = importlib.import_module("src.client.task")
    config = {
        "eval": {"module": "src.server.tasks.alfworld.eval"},
    }
    return {
        "SkillRepository": importlib.import_module("src.skills.repository").SkillRepository,
        "SkillUpdater": importlib.import_module("src.skills.updater").SkillUpdater,
        "SkillCycleRunner": cycle.SkillCycleRunner,
        "SkillAwareAgent": importlib.import_module("src.client.agents.skill_aware_agent").SkillAwareAgent,
        "TaskClient": task.TaskClient,
        "TaskError": task.TaskError,
        "score_result": cycle._score_result,
        "make_log_entry": cycle._make_log_entry,
        "eval_fn": cycle._load_eval_fn(config),
    }


def _load_group_entries(directory: Path) -> List[Dict[str, Any]]:
    paths = sorted(directory.glob("*.json"))
    if len(paths) != 13:
        raise SystemExit(f"Expected 13 complete checkpoints in {directory}, found {len(paths)}")
    return [read_json(path) for path in paths]


def _probe_gate_inputs(payloads: Sequence[Mapping[str, Any]]) -> Dict[str, Dict[str, Any]]:
    output = {}
    for payload in payloads:
        entry = payload["entry"]
        status = str(entry.get("status") or "error")
        if entry.get("error"):
            status = "error"
        output[str(entry["sample_id"])] = {
            "success": bool(entry["is_correct"]),
            "status": status,
        }
    return output


def _to_skillrl_failure(entry: Mapping[str, Any]) -> Dict[str, Any]:
    trajectory = []
    pending_action: Optional[str] = None
    for message in entry.get("history") or []:
        role = message.get("role")
        content = str(message.get("content") or "")
        if role in ("agent", "assistant"):
            if pending_action is not None:
                trajectory.append({"action": pending_action, "observation": ""})
            pending_action = content
        elif role in ("user", "system") and pending_action is not None:
            trajectory.append({"action": pending_action, "observation": content})
            pending_action = None
    if pending_action is not None:
        trajectory.append({"action": pending_action, "observation": ""})
    if not trajectory:
        trajectory = [
            {"action": str(action), "observation": ""}
            for action in entry.get("agent_actions") or []
        ]
    first_user_content = next(
        (
            str(message.get("content") or "")
            for message in entry.get("history") or []
            if message.get("role") in ("user", "system") and message.get("content")
        ),
        "",
    )
    return {
        "task": first_user_content or str(entry.get("instruction") or ""),
        "task_type": str(entry.get("query_type") or "alfworld"),
        "trajectory": trajectory,
    }


def _verify_resume_manifest(saved, args, current_manifest) -> None:
    expected = {
        "backend": args.backend,
        "controller_address": args.controller_address,
        "candidate_cap": args.candidate_cap,
    }
    for key, value in expected.items():
        if saved.get(key) != value:
            raise SystemExit(
                f"Resume mismatch for {key}: saved={saved.get(key)!r}, current={value!r}"
            )
    if saved.get("grasp_manifest", {}).get("grasp_commit") != current_manifest["grasp_commit"]:
        raise SystemExit("Resume mismatch for pinned GRASP commit")


def _group_summary(payloads: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    return {
        "task_ids": [str(item["entry"]["sample_id"]) for item in payloads],
        "correct": sum(bool(item["entry"]["is_correct"]) for item in payloads),
        "total": len(payloads),
        "accounting": _accounting(
            call for item in payloads for call in item.get("model_calls", [])
        ),
    }


def _probe_summary(payloads: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    return {
        "total": len(payloads),
        "correct": sum(bool(item["entry"]["is_correct"]) for item in payloads),
        "errors": sum(bool(item["entry"].get("error")) for item in payloads),
        "task_ids": [str(item["entry"]["sample_id"]) for item in payloads],
    }


def _compact_candidate_result(result: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        key: deepcopy(result.get(key))
        for key in (
            "proposal_id",
            "status",
            "gate",
            "accounting",
            "baseline_probe",
            "candidate_probe",
            "baseline_checkpoint_directory",
            "candidate_checkpoint_directory",
        )
        if key in result
    }


def _merge_accountings(accountings: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    total = {
        "call_count": 0,
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "cached_prompt_tokens": 0},
        "latency_seconds": 0.0,
        "estimated_cost_usd": 0.0,
    }
    for accounting in accountings:
        total["call_count"] += int(accounting.get("call_count", 0))
        for key in total["usage"]:
            total["usage"][key] += int((accounting.get("usage") or {}).get(key, 0))
        total["latency_seconds"] += float(accounting.get("latency_seconds", 0))
        total["estimated_cost_usd"] += float(accounting.get("estimated_cost_usd", 0))
    total["latency_seconds"] = round(total["latency_seconds"], 3)
    total["estimated_cost_usd"] = round(total["estimated_cost_usd"], 8)
    return total


def _accounting(calls: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    materialized = list(calls)
    usage = _sum_usage(materialized)
    return {
        "call_count": len(materialized),
        "usage": usage,
        "latency_seconds": round(sum(float(call.get("latency_seconds", 0)) for call in materialized), 3),
        "estimated_cost_usd": round(sum(float(call.get("estimated_cost_usd", 0)) for call in materialized), 8),
    }


def _sum_usage(calls: Iterable[Mapping[str, Any]]) -> Dict[str, int]:
    totals = {"prompt_tokens": 0, "completion_tokens": 0, "cached_prompt_tokens": 0}
    for call in calls:
        usage = call.get("usage") or {}
        for key in totals:
            totals[key] += int(usage.get(key, 0))
    return totals


def _message_dict(message: Any) -> Dict[str, Any]:
    if isinstance(message, Mapping):
        return json_safe(message)
    if hasattr(message, "model_dump"):
        return json_safe(message.model_dump(mode="json"))
    if hasattr(message, "dict"):
        return json_safe(message.dict())
    return json_safe(vars(message))


def _agentbench_root(grasp_root: Path) -> Path:
    return grasp_root.resolve() / AGENTBENCH_RELATIVE


def _git_commit(root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root.resolve(), check=True,
        capture_output=True, text=True,
    ).stdout.strip()


def _command_status(command: Sequence[str]) -> Dict[str, Any]:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
    except Exception as error:
        return {"ok": False, "error_type": type(error).__name__, "error": str(error)}
    return {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip()[:500],
    }


def _tcp_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


def _directory_hash(directory: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(directory.rglob("*")):
        if path.is_file():
            digest.update(str(path.relative_to(directory)).encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
