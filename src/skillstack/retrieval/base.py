"""Common boundary validation for swappable P0.0 retrievers."""

from __future__ import annotations

from typing import Any, Dict, List

from skillstack.contracts import NATIVE_SKILL_FIELDS, TASK_RECORD_FIELDS, require_fields


def validate_retrieval_request(
    task_record: Dict[str, Any],
    native_skills: List[Dict[str, Any]],
    top_k: int,
) -> None:
    require_fields(task_record, TASK_RECORD_FIELDS, "retrieval task record")
    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    for skill in native_skills:
        require_fields(skill, NATIVE_SKILL_FIELDS, "native skill supplied to retriever")

