"""Oracle retriever for the week-2 upper-bound condition."""

from __future__ import annotations

from typing import Any, Dict, List

from skillstack.contracts import (
    RETRIEVAL_CANDIDATE_FIELDS,
    RETRIEVAL_RESPONSE_FIELDS,
    require_fields,
)
from skillstack.retrieval.base import validate_retrieval_request


class OracleSkillRetriever:
    """Return the frozen expected skill for a task as the top candidate.

    The source is the project-frozen task-family to static-skill mapping in
    `configs/p0_tasks.json` (`expected_skill_id`). This is an upper-bound
    selection probe, not a learned retriever.
    """

    name = "oracle_skill"

    def retrieve(
        self,
        task_record: Dict[str, Any],
        observation: str,
        native_skills: List[Dict[str, Any]],
        top_k: int,
    ) -> Dict[str, Any]:
        validate_retrieval_request(task_record, native_skills, top_k)
        expected_skill_id = task_record.get("expected_skill_id")
        by_id = {skill["skill_id"]: skill for skill in native_skills}
        warnings: List[str] = []
        ranked_candidates: List[Dict[str, Any]] = []

        if not expected_skill_id:
            warnings.append("Task record has no expected_skill_id; oracle returns no candidates.")
        elif expected_skill_id not in by_id:
            warnings.append(f"Expected skill {expected_skill_id!r} is not in the native library.")
        else:
            skill = by_id[expected_skill_id]
            candidate = {
                "skill_id": skill["skill_id"],
                "score": 1.0,
                "native_payload": skill["native_payload"],
            }
            require_fields(candidate, RETRIEVAL_CANDIDATE_FIELDS, "oracle retrieval candidate")
            ranked_candidates.append(candidate)

        response: Dict[str, Any] = {
            "retriever_name": self.name,
            "ranked_candidates": ranked_candidates,
            "raw_output": {
                "selection_policy": "frozen_task_family_mapping",
                "expected_skill_id": expected_skill_id,
                "observation_characters": len(observation),
                "requested_top_k": top_k,
            },
            "warnings": warnings,
        }
        require_fields(response, RETRIEVAL_RESPONSE_FIELDS, "oracle retrieval response")
        return response
