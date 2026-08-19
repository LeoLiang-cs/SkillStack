"""Wrong-skill control retriever for the week-2 condition set."""

from __future__ import annotations

import random
from typing import Any, Dict, List

from skillstack.contracts import (
    RETRIEVAL_CANDIDATE_FIELDS,
    RETRIEVAL_RESPONSE_FIELDS,
    require_fields,
)
from skillstack.retrieval.base import validate_retrieval_request


class RandomSkillRetriever:
    """Return a seeded shuffle of the library as a wrong-skill control.

    Scores are rank positions, not calibrated similarities. The retriever is
    deterministic for a fixed seed and library order.
    """

    name = "random_skill"

    def __init__(self, seed: int) -> None:
        self.seed = seed

    def retrieve(
        self,
        task_record: Dict[str, Any],
        observation: str,
        native_skills: List[Dict[str, Any]],
        top_k: int,
    ) -> Dict[str, Any]:
        validate_retrieval_request(task_record, native_skills, top_k)
        # Shuffle deterministically per task so each task receives its own
        # wrong-skill draw instead of one shared shuffle across all tasks.
        rng = random.Random((self.seed, task_record["task_id"]))
        shuffled = list(native_skills)
        rng.shuffle(shuffled)

        ranked_candidates: List[Dict[str, Any]] = []
        for rank, skill in enumerate(shuffled[:top_k], start=1):
            candidate = {
                "skill_id": skill["skill_id"],
                "score": float(len(shuffled) - rank),
                "native_payload": skill["native_payload"],
            }
            require_fields(candidate, RETRIEVAL_CANDIDATE_FIELDS, "random retrieval candidate")
            ranked_candidates.append(candidate)

        response: Dict[str, Any] = {
            "retriever_name": self.name,
            "ranked_candidates": ranked_candidates,
            "raw_output": {
                "selection_policy": "seeded_shuffle_per_task",
                "seed": self.seed,
                "library_size": len(shuffled),
                "observation_characters": len(observation),
                "requested_top_k": top_k,
            },
            "warnings": ["Random-skill control ignores task and observation text by design."],
        }
        require_fields(response, RETRIEVAL_RESPONSE_FIELDS, "random retrieval response")
        return response
