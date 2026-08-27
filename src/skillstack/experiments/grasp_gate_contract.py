"""Exact, deterministic contract for the released GRASP admission score."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Dict, Mapping, Set


INVALID_ACTION_STATUS = "agent invalid action"
ERROR_STATUS = "error"
INVALID_ACTION_REGRESSION_PENALTY = 2
ProbeRunner = Callable[[], Mapping[str, Mapping[str, Any]]]


def run_grasp_gate_contract(
    probe_reference: Mapping[str, bool],
    *,
    baseline_runner: ProbeRunner,
    candidate_runner: ProbeRunner,
) -> Dict[str, Any]:
    """Run identical task IDs twice and apply GRASP's released admission rule."""

    baseline_results = _normalize_results(baseline_runner(), "baseline")
    candidate_results = _normalize_results(candidate_runner(), "candidate")
    reference = _normalize_reference(probe_reference)
    expected_ids = set(reference)
    if set(baseline_results) != expected_ids or set(candidate_results) != expected_ids:
        raise ValueError("Reference, baseline and candidate probe task IDs must match")

    baseline_fixes = 0
    baseline_regressions = 0
    baseline_error_ids: Set[str] = set()
    for task_id, was_failing in reference.items():
        result = baseline_results[task_id]
        if result["status"] == ERROR_STATUS:
            baseline_error_ids.add(task_id)
            if not was_failing:
                baseline_regressions += 1
            continue
        if was_failing and result["success"]:
            baseline_fixes += 1
        elif not was_failing and not result["success"]:
            baseline_regressions += 1

    fixes = 0
    regressions = 0
    invalid_action_regressions = 0
    transitions: Dict[str, Dict[str, Any]] = {}
    for task_id, was_failing in reference.items():
        baseline = baseline_results[task_id]
        candidate = candidate_results[task_id]
        excluded_preexisting_error = False
        if candidate["status"] == ERROR_STATUS:
            if task_id in baseline_error_ids:
                excluded_preexisting_error = True
            elif not was_failing:
                regressions += 1
        elif was_failing and candidate["success"]:
            fixes += 1
        elif not was_failing and not candidate["success"]:
            regressions += 1
            if candidate["status"] == INVALID_ACTION_STATUS:
                invalid_action_regressions += 1
        transitions[task_id] = {
            "was_failing": was_failing,
            "baseline": deepcopy(baseline),
            "candidate": deepcopy(candidate),
            "candidate_error_excluded_as_preexisting": excluded_preexisting_error,
        }

    raw_score = (
        fixes
        - regressions
        - (INVALID_ACTION_REGRESSION_PENALTY - 1) * invalid_action_regressions
    )
    adjusted_score = (
        (fixes - baseline_fixes)
        - (regressions - baseline_regressions)
        - (INVALID_ACTION_REGRESSION_PENALTY - 1) * invalid_action_regressions
    )
    within_regression_budget = regressions <= baseline_regressions
    admitted = adjusted_score > 0 and within_regression_budget
    if admitted:
        reason = "L.ADMITTED_POSITIVE_WITHIN_REGRESSION_BUDGET"
    elif not within_regression_budget:
        reason = "L.REJECTED_REGRESSION_BUDGET"
    else:
        reason = "L.REJECTED_NON_POSITIVE_ADJUSTED_SCORE"
    return {
        "decision": "accepted" if admitted else "no_op",
        "reason": reason,
        "baseline_fixes": baseline_fixes,
        "baseline_regressions": baseline_regressions,
        "baseline_error_ids": sorted(baseline_error_ids),
        "fixes": fixes,
        "regressions": regressions,
        "invalid_action_regressions": invalid_action_regressions,
        "invalid_action_regression_penalty": INVALID_ACTION_REGRESSION_PENALTY,
        "raw_score": raw_score,
        "adjusted_score": adjusted_score,
        "within_regression_budget": within_regression_budget,
        "probe_transitions": transitions,
    }


def _normalize_reference(reference: Mapping[str, bool]) -> Dict[str, bool]:
    if not isinstance(reference, Mapping):
        raise ValueError("Probe reference must be a task-ID mapping")
    normalized: Dict[str, bool] = {}
    for task_id, was_failing in reference.items():
        if not isinstance(task_id, str) or not task_id:
            raise ValueError("Probe reference task IDs must be non-empty strings")
        if not isinstance(was_failing, bool):
            raise ValueError(f"Probe reference for {task_id} must be boolean")
        normalized[task_id] = was_failing
    return normalized


def _normalize_results(
    results: Mapping[str, Mapping[str, Any]], label: str
) -> Dict[str, Dict[str, Any]]:
    if not isinstance(results, Mapping):
        raise ValueError(f"{label} runner must return a task-ID mapping")
    normalized: Dict[str, Dict[str, Any]] = {}
    for task_id, result in results.items():
        if not isinstance(task_id, str) or not task_id:
            raise ValueError(f"{label} task IDs must be non-empty strings")
        if not isinstance(result, Mapping):
            raise ValueError(f"{label} result for {task_id} must be an object")
        success = result.get("success")
        status = result.get("status")
        if not isinstance(success, bool) or not isinstance(status, str):
            raise ValueError(f"{label} result for {task_id} requires success and status")
        normalized[task_id] = {"success": success, "status": status}
    return normalized
