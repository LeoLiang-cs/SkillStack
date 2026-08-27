"""Isolated, deterministic fixture for exercising GRASP-style ADD admission."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any, Callable, Dict, Mapping, MutableMapping, Optional


ProbeRunner = Callable[[Mapping[str, str]], Mapping[str, Any]]


def evaluate_add_candidate(
    starting_library: Mapping[str, str],
    proposal: Mapping[str, Any],
    *,
    capacity: int,
    probe_runner: ProbeRunner,
) -> Dict[str, Any]:
    """Evaluate one ADD on a fork; the caller's starting library is immutable."""

    baseline_library = deepcopy(dict(starting_library))
    candidate_library = deepcopy(dict(starting_library))
    before_hash = _library_hash(baseline_library)

    rejection_reason = _preflight_reason(baseline_library, proposal, capacity)
    if rejection_reason is not None:
        return _decision(
            proposal, "rejected", rejection_reason, before_hash, before_hash,
            {}, {}, {}, 0, 0, 0,
        )

    baseline_results = _normalize_probe_results(probe_runner(deepcopy(baseline_library)))
    candidate_library[str(proposal["normalized_name"])] = str(proposal["normalized_content"])
    candidate_results = _normalize_probe_results(probe_runner(deepcopy(candidate_library)))
    if set(baseline_results) != set(candidate_results):
        raise ValueError("Baseline and candidate probe task IDs differ")

    transitions: MutableMapping[str, Dict[str, bool]] = {}
    fixes = 0
    regressions = 0
    for task_id in sorted(baseline_results):
        before = baseline_results[task_id]
        after = candidate_results[task_id]
        transitions[task_id] = {"baseline_success": before, "candidate_success": after}
        fixes += int(not before and after)
        regressions += int(before and not after)
    adjusted_score = fixes - regressions
    accepted = adjusted_score > 0 and regressions == 0
    status = "accepted" if accepted else "rejected"
    reason = "L.ADMITTED_POSITIVE_NO_REGRESSION" if accepted else "L.REJECTED_NO_POSITIVE_SAFE_GAIN"
    after_library = candidate_library if accepted else baseline_library
    return _decision(
        proposal, status, reason, before_hash, _library_hash(after_library),
        baseline_results, candidate_results, transitions, fixes, regressions, adjusted_score,
    )


def _preflight_reason(
    library: Mapping[str, str], proposal: Mapping[str, Any], capacity: int
) -> Optional[str]:
    if proposal.get("parse_status") != "valid":
        return proposal.get("rejection_reason", "L.INVALID_PROPOSAL")
    if proposal.get("normalized_action") != "ADD":
        return "L.UNSUPPORTED_ACTION"
    name = proposal.get("normalized_name")
    content = proposal.get("normalized_content")
    if not isinstance(name, str) or not name or not isinstance(content, str) or not content:
        return "L.INVALID_ADD_SCHEMA"
    if name in library:
        return "L.DUPLICATE_NAME"
    if len(library) >= capacity:
        return "L.ADD_BLOCKED_CAPACITY"
    return None


def _normalize_probe_results(results: Mapping[str, Any]) -> Dict[str, bool]:
    if not isinstance(results, Mapping):
        raise ValueError("Probe runner must return a task-ID mapping")
    normalized: Dict[str, bool] = {}
    for task_id, outcome in results.items():
        if not isinstance(task_id, str) or not task_id:
            raise ValueError("Probe task IDs must be non-empty strings")
        if isinstance(outcome, bool):
            normalized[task_id] = outcome
        elif isinstance(outcome, Mapping) and isinstance(outcome.get("success"), bool):
            normalized[task_id] = outcome["success"]
        else:
            raise ValueError(f"Probe result for {task_id} lacks a boolean success")
    return normalized


def _library_hash(library: Mapping[str, str]) -> str:
    payload = json.dumps(dict(library), sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _decision(
    proposal: Mapping[str, Any],
    status: str,
    reason: str,
    before_hash: str,
    after_hash: str,
    baseline_results: Mapping[str, bool],
    candidate_results: Mapping[str, bool],
    transitions: Mapping[str, Mapping[str, bool]],
    fixes: int,
    regressions: int,
    adjusted_score: int,
) -> Dict[str, Any]:
    return {
        "proposal_id": proposal.get("proposal_id"),
        "decision": status,
        "reason": reason,
        "starting_library_hash": before_hash,
        "result_library_hash": after_hash,
        "baseline_probe_results": deepcopy(dict(baseline_results)),
        "candidate_probe_results": deepcopy(dict(candidate_results)),
        "probe_transitions": deepcopy(dict(transitions)),
        "fixes": fixes,
        "regressions": regressions,
        "invalid_action_regressions": 0,
        "adjusted_score": adjusted_score,
    }
