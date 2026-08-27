"""Run a provider-substituted SkillRL-to-GRASP compatibility flow smoke."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skillrl-root", type=Path, required=True)
    parser.add_argument("--grasp-root", type=Path, required=True)
    parser.add_argument("--backend", default="zhipu_glm_flashx")
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--output-root", type=Path, default=ROOT / "runs")
    args = parser.parse_args()

    load_env_file()
    backend = load_backends()[args.backend]
    client = LlmClient(backend)
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    prepared = prepare_skillrl_request(
        args.skillrl_root,
        fixture["failed_trajectories"],
        fixture["current_skills"],
    )
    request = {
        "model": backend.model,
        "messages": [{"role": "user", "content": prepared["prompt"]}],
        "max_tokens": prepared["max_completion_tokens"],
        "temperature": 0,
        "thinking_disabled": backend.thinking_disabled,
    }
    completion = client.chat(
        request["messages"],
        max_tokens=request["max_tokens"],
        temperature=request["temperature"],
    )
    parsed = parse_substituted_skillrl_response(
        args.skillrl_root, completion["content"], fixture["current_skills"]
    )
    adapter_batch = adapt_skillrl_output(
        parsed["native_return"],
        task_type=fixture["failed_trajectories"][0]["task_type"],
        triggering_evidence_ids=[fixture["source_task_id"]],
        writer_model=backend.model,
        decoding={"temperature": 0, "provider_substituted": True},
        call_usage=completion["usage"],
    )

    candidate_boundaries = []
    for proposal in adapter_batch["proposals"]:
        if proposal["parse_status"] != "valid":
            candidate_boundaries.append({
                "proposal_id": proposal["proposal_id"],
                "status": "adapter_rejected",
                "reason": proposal.get("rejection_reason"),
            })
            continue
        native_proposal = envelope_to_grasp_add(proposal)
        repository_smoke = run_native_repository_smoke(args.grasp_root, native_proposal)
        gate = run_grasp_gate_contract(
            {"fixture_failure": True},
            baseline_runner=lambda: {
                "fixture_failure": {"success": False, "status": "completed"}
            },
            candidate_runner=lambda: {
                "fixture_failure": {"success": False, "status": "completed"}
            },
        )
        candidate_boundaries.append({
            "proposal_id": proposal["proposal_id"],
            "status": "reached_gate",
            "native_proposal": native_proposal,
            "repository_boundary": repository_smoke,
            "deterministic_gate_result": gate,
            "gate_fixture_label": "no_change_runnability_only",
        })

    cost = client.estimate_cost_usd(completion["usage"])
    valid_count = sum(item["status"] == "reached_gate" for item in candidate_boundaries)
    writer = JsonlTraceWriter(args.output_root, f"w4_skillrl_{args.backend}_flow_smoke")
    writer.write_manifest({
        "experiment_id": "w4_skillrl_provider_substituted_flow_smoke",
        "run_id": writer.run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "fidelity_label": "provider_substituted_flow_smoke",
        "source_writer_model": "o3_on_azure",
        "substituted_backend": backend.name,
        "substituted_model": backend.model,
        "fixture": fixture,
        "skillrl_source_commit": prepared["source_commit"],
        "claim_boundary": "Engineering compatibility only; not an I3 source-faithful result.",
    })
    trace = {
        "run_id": writer.run_id,
        "episode_id": f"{writer.run_id}_flow_00",
        "task_id": fixture["source_task_id"],
        "retriever_name": "not_applicable_local",
        "executor_name": "skillrl_provider_substituted_writer_to_grasp",
        "prepared_request": prepared,
        "raw_api_request": request,
        "raw_model_content": completion["content"],
        "usage": completion["usage"],
        "latency_seconds": completion["latency_seconds"],
        "estimated_cost_usd": cost,
        "released_parser_result": parsed,
        "adapter_batch": adapter_batch,
        "candidate_boundaries": candidate_boundaries,
        "success": valid_count > 0,
        "stop_reason": "flow_boundary_complete" if valid_count > 0 else "no_valid_candidate",
        "warnings": ["Writer provider/model differs from released SkillRL o3-on-Azure setup."],
    }
    writer.append_episode(trace)
    writer.write_summary({
        "experiment_id": "w4_skillrl_provider_substituted_flow_smoke",
        "run_id": writer.run_id,
        "backend": backend.name,
        "model": backend.model,
        "native_candidate_count": len(parsed["native_return"]),
        "adapter_valid_candidate_count": valid_count,
        "all_valid_candidates_reached_native_repository": (
            valid_count > 0 and all(
                item.get("repository_boundary", {}).get("boundary_success", False)
                for item in candidate_boundaries if item["status"] == "reached_gate"
            )
        ),
        "usage": completion["usage"],
        "latency_seconds": completion["latency_seconds"],
        "estimated_cost_usd": cost,
        "fidelity_label": "provider_substituted_flow_smoke",
    })
    print(json.dumps({
        "run_id": writer.run_id,
        "run_directory": str(writer.run_dir),
        "backend": backend.name,
        "native_candidate_count": len(parsed["native_return"]),
        "adapter_valid_candidate_count": valid_count,
        "estimated_cost_usd": cost,
    }, indent=2))
    return 0 if valid_count > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
