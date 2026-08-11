"""Adapt a retriever's native candidates into flat executor context."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from skillstack.contracts import (
    RETRIEVAL_CANDIDATE_FIELDS,
    RETRIEVAL_RESPONSE_FIELDS,
    empty_adapter_event,
    require_fields,
)


def adapt_retrieval_for_execution(
    retrieval_response: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Preserve selected native text while making a flat execution context."""

    require_fields(retrieval_response, RETRIEVAL_RESPONSE_FIELDS, "retrieval response")
    candidates: List[Dict[str, Any]] = retrieval_response["ranked_candidates"]
    for candidate in candidates:
        require_fields(candidate, RETRIEVAL_CANDIDATE_FIELDS, "retrieval candidate")

    event = empty_adapter_event()
    event["read"] = [
        "ranked_candidates[*].skill_id",
        "ranked_candidates[*].score",
        "ranked_candidates[*].native_payload",
    ]

    selected_skill_ids = [candidate["skill_id"] for candidate in candidates]
    selected_scores = [candidate["score"] for candidate in candidates]
    selected_native_skills = [candidate["native_payload"] for candidate in candidates]
    sections = [
        f"### Selected skill {index}: {candidate['skill_id']}\n\n{candidate['native_payload']}"
        for index, candidate in enumerate(candidates, start=1)
    ]
    flat_skill_context = "\n\n---\n\n".join(sections)
    event["generated"] = [
        "selected_skill_ids",
        "selected_scores",
        "selected_native_skills",
        "flat_skill_context",
    ]
    if not candidates:
        event["warnings"].append("No skills selected; executor receives an empty skill context.")

    execution_input = {
        "selected_skill_ids": selected_skill_ids,
        "selected_scores": selected_scores,
        "selected_native_skills": selected_native_skills,
        "flat_skill_context": flat_skill_context,
    }
    return execution_input, event

