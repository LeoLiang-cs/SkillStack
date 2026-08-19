"""Transparent heuristic task-semantic retriever (R1, Phase 3).

Mechanism differs from the lexical retriever: it extracts structured task
semantics (goal operation, required transformation, destination, object) and
checks state applicability (required appliance present in the room), then
scores skills by field match + applicability — not by token overlap.
Deterministic, no LLM. All extracted fields and per-skill score breakdowns
are recorded as raw evidence for interface induction.
"""

from __future__ import annotations

from typing import Any, Dict, List

from skillstack.contracts import (
    RETRIEVAL_CANDIDATE_FIELDS,
    RETRIEVAL_RESPONSE_FIELDS,
    require_fields,
)
from skillstack.retrieval.base import validate_retrieval_request
from skillstack.task_semantics import (
    TRANSFORM_VERB_BY_SKILL,
    parse_task_semantics,
    required_appliance_for_family,
)


class TaskSemanticRetriever:
    """Rank skills by structured task semantics + state applicability."""

    name = "task_semantic_top_k"

    def retrieve(
        self,
        task_record: Dict[str, Any],
        observation: str,
        native_skills: List[Dict[str, Any]],
        top_k: int,
    ) -> Dict[str, Any]:
        validate_retrieval_request(task_record, native_skills, top_k)
        semantics = parse_task_semantics(task_record, observation)
        warnings = list(semantics.pop("warnings"))
        task_family = task_record["task_family"]
        required_transformation = semantics["required_transformation"]
        required_appliance = required_appliance_for_family(task_family)
        observation_lower = observation.lower()

        scored: List[Dict[str, Any]] = []
        for skill in native_skills:
            breakdown, score = _score_skill(
                skill,
                semantics=semantics,
                task_family=task_family,
                required_transformation=required_transformation,
                required_appliance=required_appliance,
                observation_lower=observation_lower,
            )
            candidate: Dict[str, Any] = {
                "skill_id": skill["skill_id"],
                "score": float(score),
                "native_payload": skill["native_payload"],
            }
            require_fields(candidate, RETRIEVAL_CANDIDATE_FIELDS, "task-semantic retrieval candidate")
            scored.append({"candidate": candidate, "breakdown": breakdown})

        scored.sort(key=lambda item: (-item["candidate"]["score"], item["candidate"]["skill_id"]))
        ranked_candidates = [item["candidate"] for item in scored[:top_k]]
        score_by_skill_id = {
            item["candidate"]["skill_id"]: item["candidate"]["score"] for item in scored
        }
        breakdown_by_skill_id = {
            item["candidate"]["skill_id"]: item["breakdown"] for item in scored
        }

        if semantics["object"] is None or semantics["destination"] is None:
            warnings.append("Task semantics incomplete; scoring may be degraded.")

        response: Dict[str, Any] = {
            "retriever_name": self.name,
            "ranked_candidates": ranked_candidates,
            "raw_output": {
                "query_source": "task_semantics_heuristic",
                "extracted_semantics": semantics,
                "required_appliance": required_appliance,
                "scoring": "field_match_plus_applicability",
                "scores_by_skill_id": score_by_skill_id,
                "breakdown_by_skill_id": breakdown_by_skill_id,
                "requested_top_k": top_k,
            },
            "warnings": warnings,
        }
        require_fields(response, RETRIEVAL_RESPONSE_FIELDS, "task-semantic retrieval response")
        return response


def _score_skill(
    skill: Dict[str, Any],
    semantics: Dict[str, Any],
    task_family: str,
    required_transformation: Any,
    required_appliance: Any,
    observation_lower: str,
) -> tuple:
    """Return (breakdown, total score) for one native skill."""

    breakdown: Dict[str, float] = {}
    score = 0.0
    skill_id = skill["skill_id"]
    skill_family = skill.get("local_metadata", {}).get("task_family", "")
    payload_lower = skill["native_payload"].lower()

    if skill_family == task_family:
        score += 5.0
        breakdown["family_match"] = 5.0
    else:
        breakdown["family_match"] = 0.0

    skill_transformation = TRANSFORM_VERB_BY_SKILL.get(skill_id)
    if required_transformation and skill_transformation == required_transformation:
        score += 2.0
        breakdown["transformation_match"] = 2.0
    else:
        breakdown["transformation_match"] = 0.0

    if required_appliance:
        if required_appliance in observation_lower:
            score += 1.0
            breakdown["appliance_present"] = 1.0
        else:
            breakdown["appliance_present"] = 0.0
    else:
        breakdown["appliance_present"] = 0.0

    destination = semantics.get("destination")
    if destination and destination in payload_lower:
        score += 1.0
        breakdown["destination_term"] = 1.0
    else:
        breakdown["destination_term"] = 0.0

    object_name = semantics.get("object")
    if object_name and object_name in payload_lower:
        score += 0.5
        breakdown["object_term"] = 0.5
    else:
        breakdown["object_term"] = 0.0

    return breakdown, score
