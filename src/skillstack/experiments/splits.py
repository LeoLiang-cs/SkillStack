"""Strict-disjoint task splitting for the GRASP/SkillRL component experiment."""

from __future__ import annotations

import random
from copy import deepcopy
from typing import Any, Dict, Iterable, List, Mapping, Sequence


def build_strict_disjoint_split(
    records: Sequence[Mapping[str, Any]],
    *,
    seed: int = 2,
    epoch: int = 0,
    history_size: int = 13,
    proposal_size: int = 13,
) -> Dict[str, Any]:
    """Shuffle deterministically, split once, and fail on ambiguous task IDs."""

    expected = history_size + proposal_size
    if len(records) != expected:
        raise ValueError(f"Expected {expected} dev records, received {len(records)}")
    task_ids = [_task_id(record) for record in records]
    _ensure_unique(task_ids, "dev records")

    order = list(range(len(records)))
    source_shuffle_seed = f"{seed}:shuffle:{epoch}"
    random.Random(source_shuffle_seed).shuffle(order)
    ordered = [deepcopy(dict(records[index])) for index in order]
    history = ordered[:history_size]
    proposal = ordered[history_size:]
    validate_disjoint_task_ids(
        (_task_id(record) for record in history),
        (_task_id(record) for record in proposal),
    )
    return {
        "seed": seed,
        "epoch": epoch,
        "source_shuffle_seed": source_shuffle_seed,
        "ordering_method": "grasp_python_random_shuffle_indices",
        "history_probe_source": history,
        "proposal_source": proposal,
        "history_probe_task_ids": [_task_id(record) for record in history],
        "proposal_task_ids": [_task_id(record) for record in proposal],
    }


def validate_disjoint_task_ids(
    history_probe_task_ids: Iterable[str], proposal_task_ids: Iterable[str]
) -> None:
    """Reject duplicates within or across the two frozen evidence partitions."""

    history = list(history_probe_task_ids)
    proposal = list(proposal_task_ids)
    _ensure_unique(history, "history_probe_source")
    _ensure_unique(proposal, "proposal_source")
    overlap = sorted(set(history).intersection(proposal))
    if overlap:
        raise ValueError(f"Proposal/probe task-ID overlap: {', '.join(overlap)}")


def _task_id(record: Mapping[str, Any]) -> str:
    task_id = record.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        raise ValueError("Every split record requires a non-empty string task_id")
    return task_id


def _ensure_unique(task_ids: List[str], context: str) -> None:
    duplicates = sorted({task_id for task_id in task_ids if task_ids.count(task_id) > 1})
    if duplicates:
        raise ValueError(f"Duplicate task IDs in {context}: {', '.join(duplicates)}")
