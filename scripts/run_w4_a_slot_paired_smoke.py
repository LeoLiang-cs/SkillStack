"""Run matched DeepSeek A0-GRASP and A1-SkillRL compatibility cells."""

from __future__ import annotations

import argparse
import importlib
import json
import socket
import subprocess
import sys
import tempfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skillstack.adapters.grasp_to_proposal import adapt_grasp_output
from skillstack.adapters.proposal_to_grasp import envelope_to_grasp_add
from skillstack.adapters.skillrl_to_grasp import adapt_skillrl_output
from skillstack.experiments.grasp_gate_contract import run_grasp_gate_contract
from skillstack.experiments.grasp_source import run_native_repository_smoke
from skillstack.experiments.skillrl_source import (
    parse_substituted_skillrl_response,
    prepare_skillrl_request,
)
from skillstack.llm import LlmClient, load_backends, load_env_file
from skillstack.tracing import JsonlTraceWriter


DEFAULT_FIXTURE = ROOT / "fixtures/week4/skillrl_i3_failure_fixture.json"


class RecordingGRASPAgent:
    def __init__(self, client: LlmClient, max_tokens: int = 2048, temperature: float = 0.8):
        self.client = client
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.calls = []

    def inference(self, history):
        response = self.client.chat(
            history, max_tokens=self.max_tokens, temperature=self.temperature
        )
        self.calls.append({
            "request": {"messages": deepcopy(history), "max_tokens": self.max_tokens,
                        "temperature": self.temperature},
            "raw_content": response["content"],
            "usage": response["usage"],
            "latency_seconds": response["latency_seconds"],
            "estimated_cost_usd": self.client.estimate_cost_usd(response["usage"]),
        })
        return response["content"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grasp-root", type=Path, required=True)
    parser.add_argument("--skillrl-root", type=Path, required=True)
    parser.add_argument("--backend", default="deepseek_v4_flash")
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--output-root", type=Path, default=ROOT / "runs")
    args = parser.parse_args()
    load_env_file()
    backend = load_backends()[args.backend]
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    failures = fixture["failed_trajectories"]
    paired_current_skills = {"general_skills": [], "task_specific_skills": {}}
    evidence_id = fixture["source_task_id"]

    a0 = _run_a0(args.grasp_root, backend, failures, evidence_id)
    a1 = _run_a1(
        args.skillrl_root, backend, failures, paired_current_skills, evidence_id
    )
    for cell in (a0, a1):
        cell["candidate_boundaries"] = _run_boundaries(
            args.grasp_root, cell["adapter_batch"]
        )
        cell["valid_candidate_count"] = sum(
            item["status"] == "reached_gate" for item in cell["candidate_boundaries"]
        )

    writer = JsonlTraceWriter(args.output_root, "w4_a_slot_paired_deepseek_smoke")
    manifest = {
        "experiment_id": "w4_a_slot_paired_provider_substituted_smoke",
        "run_id": writer.run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "backend": backend.name,
        "model": backend.model,
        "fixture": fixture,
        "paired_current_skills": paired_current_skills,
        "candidate_cap": 3,
        "contrastive_revision": False,
        "same_evidence": True,
        "same_starting_learned_library": True,
        "same_gate_fixture": True,
        "gate_fixture_label": "no_change_runnability_only",
        "environment_preflight": _environment_preflight(),
        "claim_boundary": (
            "Paired component compatibility and cost only; strict 13/13 task performance blocked."
        ),
    }
    writer.write_manifest(manifest)
    for index, cell in enumerate((a0, a1)):
        writer.append_episode({
            "run_id": writer.run_id,
            "episode_id": f"{writer.run_id}_{cell['cell_id']}_{index}",
            "task_id": evidence_id,
            "retriever_name": "not_applicable_local",
            "executor_name": "a_slot_component_to_grasp_gate",
            **cell,
            "success": cell["valid_candidate_count"] > 0,
            "stop_reason": (
                "compatibility_boundary_complete"
                if cell["valid_candidate_count"] > 0 else "no_valid_candidate"
            ),
            "warnings": ["Provider-substituted DeepSeek writer; no task-performance claim."],
        })
    comparison = _comparison(a0, a1)
    writer.write_summary({
        "experiment_id": "w4_a_slot_paired_provider_substituted_smoke",
        "run_id": writer.run_id,
        "a0_valid_candidate_count": a0["valid_candidate_count"],
        "a1_valid_candidate_count": a1["valid_candidate_count"],
        "paired_comparison": comparison,
        "i4_compatibility_status": "passed" if a0["valid_candidate_count"] else "no_valid_candidate",
        "i5_compatibility_status": "passed" if a1["valid_candidate_count"] else "no_valid_candidate",
        "i6_compatibility_status": "passed" if a0["valid_candidate_count"] and a1["valid_candidate_count"] else "incomplete",
        "i6_task_performance_status": "blocked_environment",
    })
    print(json.dumps({
        "run_id": writer.run_id,
        "run_directory": str(writer.run_dir),
        "a0_valid_candidate_count": a0["valid_candidate_count"],
        "a1_valid_candidate_count": a1["valid_candidate_count"],
        "comparison": comparison,
    }, indent=2))
    return 0 if a0["valid_candidate_count"] and a1["valid_candidate_count"] else 1


def _run_a0(grasp_root: Path, backend, failures, evidence_id: str):
    agentbench = grasp_root.resolve() / "benchmarks/AgentBench"
    sys.path.insert(0, str(agentbench))
    try:
        repository_type = importlib.import_module("src.skills.repository").SkillRepository
        updater_type = importlib.import_module("src.skills.updater").SkillUpdater
        cycle_type = importlib.import_module("src.skills.cycle").SkillCycleRunner
        client = LlmClient(backend)
        agent = RecordingGRASPAgent(client)
        with tempfile.TemporaryDirectory(prefix="skillstack_a0_") as directory:
            repository = repository_type(
                base_dir=agentbench / "skills/alfworld/base",
                learned_dir=Path(directory) / "learned",
            )
            updater = updater_type(agent=agent, max_proposals=3, max_learned_skills=10)
            failure = failures[0]
            entry = {
                "sample_id": evidence_id,
                "instruction": failure["task"],
                "is_correct": False,
                "failure_tags": ["max_steps_exhausted", "wrong_object_pickup"],
                "agent_actions": [step["action"] for step in failure["trajectory"]],
                "history": [],
                "task_result": {},
                "ground_truth": "",
                "skill_snapshot_before": [],
            }
            entries = [entry]
            labels, new_labels = updater.classify_failures(entries, prev_taxonomy={})
            diagnoses = updater.diagnose(entries, repository, failure_labels=labels)
            groups = cycle_type._group_entries_by_failure_mode(entries, labels)
            failure_mode, group = groups[0]
            raw_proposals = updater.propose(
                group, repository, prev_results=None, skill_effectiveness={},
                failure_mode=failure_mode, diagnosis=diagnoses, other_failing=None,
            )
            validated = updater.validate(raw_proposals, repository)
        usage = _sum_usage(agent.calls)
        adapter_batch = adapt_grasp_output(
            validated[:3], triggering_evidence_ids=[evidence_id],
            writer_model=backend.model, decoding={"temperature": 0.8, "provider_substituted": True},
            call_usage=usage,
        )
        return {
            "cell_id": "A0_GRASP_DEEPSEEK",
            "producer": "GRASP classify_diagnose_group_propose",
            "failure_labels": labels,
            "new_failure_labels": new_labels,
            "diagnoses": diagnoses,
            "proposal_groups": [{"label": label, "sample_ids": [e["sample_id"] for e in values]}
                                for label, values in groups],
            "raw_proposals": raw_proposals,
            "native_validated_proposals": validated,
            "model_calls": agent.calls,
            "aggregate_usage": usage,
            "aggregate_latency_seconds": sum(call["latency_seconds"] for call in agent.calls),
            "aggregate_estimated_cost_usd": sum(call["estimated_cost_usd"] for call in agent.calls),
            "adapter_batch": adapter_batch,
        }
    finally:
        if sys.path and sys.path[0] == str(agentbench):
            sys.path.pop(0)


def _run_a1(skillrl_root: Path, backend, failures, current_skills, evidence_id: str):
    client = LlmClient(backend)
    prepared = prepare_skillrl_request(skillrl_root, failures, current_skills)
    completion = client.chat(
        [{"role": "user", "content": prepared["prompt"]}],
        max_tokens=prepared["max_completion_tokens"], temperature=0,
    )
    parsed = parse_substituted_skillrl_response(
        skillrl_root, completion["content"], current_skills
    )
    usage = completion["usage"]
    adapter_batch = adapt_skillrl_output(
        parsed["native_return"], task_type=failures[0]["task_type"],
        triggering_evidence_ids=[evidence_id], writer_model=backend.model,
        decoding={"temperature": 0, "provider_substituted": True}, call_usage=usage,
    )
    return {
        "cell_id": "A1_SKILLRL_DEEPSEEK",
        "producer": "SkillRL analyze_failures prompt_parser",
        "prepared_request": prepared,
        "raw_model_content": completion["content"],
        "released_parser_result": parsed,
        "model_calls": [{
            "request": {"messages": [{"role": "user", "content": prepared["prompt"]}],
                        "max_tokens": prepared["max_completion_tokens"], "temperature": 0},
            "raw_content": completion["content"], "usage": usage,
            "latency_seconds": completion["latency_seconds"],
            "estimated_cost_usd": client.estimate_cost_usd(usage),
        }],
        "aggregate_usage": usage,
        "aggregate_latency_seconds": completion["latency_seconds"],
        "aggregate_estimated_cost_usd": client.estimate_cost_usd(usage),
        "adapter_batch": adapter_batch,
    }


def _run_boundaries(grasp_root: Path, adapter_batch):
    boundaries = []
    for proposal in adapter_batch["proposals"][:3]:
        if proposal["parse_status"] != "valid":
            boundaries.append({"proposal_id": proposal["proposal_id"], "status": "adapter_rejected",
                               "reason": proposal.get("rejection_reason")})
            continue
        native = envelope_to_grasp_add(proposal)
        repository = run_native_repository_smoke(grasp_root, native)
        gate = run_grasp_gate_contract(
            {"fixture_failure": True},
            baseline_runner=lambda: {"fixture_failure": {"success": False, "status": "completed"}},
            candidate_runner=lambda: {"fixture_failure": {"success": False, "status": "completed"}},
        )
        boundaries.append({"proposal_id": proposal["proposal_id"], "status": "reached_gate",
                           "native_proposal": native, "repository_boundary": repository,
                           "gate_result": gate})
    return boundaries


def _sum_usage(calls):
    return {key: sum(int(call["usage"].get(key, 0)) for call in calls)
            for key in ("prompt_tokens", "completion_tokens", "cached_prompt_tokens")}


def _comparison(a0, a1):
    return {
        "same_evidence": True,
        "same_starting_learned_library": True,
        "same_candidate_cap": True,
        "same_gate_fixture": True,
        "a0": {"valid_candidates": a0["valid_candidate_count"],
               "model_call_count": len(a0["model_calls"]), "usage": a0["aggregate_usage"],
               "latency_seconds": a0["aggregate_latency_seconds"],
               "estimated_cost_usd": a0["aggregate_estimated_cost_usd"]},
        "a1": {"valid_candidates": a1["valid_candidate_count"],
               "model_call_count": len(a1["model_calls"]), "usage": a1["aggregate_usage"],
               "latency_seconds": a1["aggregate_latency_seconds"],
               "estimated_cost_usd": a1["aggregate_estimated_cost_usd"]},
        "task_performance": "not_available_environment_blocked",
    }


def _environment_preflight():
    ports = {}
    for port in (5060, 5061):
        connection = socket.socket()
        connection.settimeout(0.2)
        try:
            connection.connect(("127.0.0.1", port))
            ports[port] = True
        except OSError:
            ports[port] = False
        finally:
            connection.close()
    docker = subprocess.run(
        ["docker", "info", "--format", "{{.ServerVersion}}"],
        capture_output=True, text=True,
    )
    available = ports[5060] and ports[5061] and docker.returncode == 0
    return {
        "agentbench_controller_5060": ports[5060],
        "agentbench_worker_5061": ports[5061],
        "docker_daemon": docker.returncode == 0,
        "strict_13_13_task_performance_available": available,
    }


if __name__ == "__main__":
    raise SystemExit(main())
