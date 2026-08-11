"""No-skill control retriever for the P0.0 pipeline."""

from __future__ import annotations

from typing import Any, Dict, List

from skillstack.contracts import RETRIEVAL_RESPONSE_FIELDS, require_fields
from skillstack.retrieval.base import validate_retrieval_request


class NoSkillRetriever:
    """Return no skills while preserving the same boundary as real retrievers."""

    name = "no_skill"

    def retrieve(
        self,
        task_record: Dict[str, Any],
        observation: str,
        native_skills: List[Dict[str, Any]],
        top_k: int,
    ) -> Dict[str, Any]:
        validate_retrieval_request(task_record, native_skills, top_k)
        response: Dict[str, Any] = {
            "retriever_name": self.name,
            "ranked_candidates": [],
            "raw_output": {
                "selection_policy": "always_empty",
                "task_id": task_record["task_id"],
                "observation_characters": len(observation),
                "requested_top_k": top_k,
            },
            "warnings": ["No-skill control selected no native skill artifacts."],
        }
        require_fields(response, RETRIEVAL_RESPONSE_FIELDS, "no-skill retrieval response")
        return response

