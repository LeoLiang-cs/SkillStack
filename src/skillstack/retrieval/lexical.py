"""Transparent token-overlap retrieval for P0.0 debugging, not embedding retrieval."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, Dict, Iterable, List, Set

from skillstack.contracts import (
    RETRIEVAL_CANDIDATE_FIELDS,
    RETRIEVAL_RESPONSE_FIELDS,
    require_fields,
)
from skillstack.retrieval.base import validate_retrieval_request


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "is", "it", "of", "on", "or", "some", "the", "to", "with", "you", "your",
}


class DebugLexicalRetriever:
    """Rank native skills by IDF-weighted token overlap with task text.

    The implementation deliberately scores task instruction only. Raw state can
    be added later as a controlled intervention rather than quietly changing
    this baseline into a state-aware retriever.
    """

    name = "debug_lexical_top_k"

    def retrieve(
        self,
        task_record: Dict[str, Any],
        observation: str,
        native_skills: List[Dict[str, Any]],
        top_k: int,
    ) -> Dict[str, Any]:
        validate_retrieval_request(task_record, native_skills, top_k)
        query_tokens = _token_set(task_record["task_instruction"])
        document_tokens = {
            skill["skill_id"]: _token_set(skill["native_payload"])
            for skill in native_skills
        }
        inverse_document_frequency = _idf(document_tokens.values())

        all_candidates = []
        for skill in native_skills:
            skill_tokens = document_tokens[skill["skill_id"]]
            overlap = sorted(query_tokens & skill_tokens)
            score = sum(inverse_document_frequency[token] for token in overlap)
            candidate: Dict[str, Any] = {
                "skill_id": skill["skill_id"],
                "score": float(score),
                "native_payload": skill["native_payload"],
            }
            require_fields(candidate, RETRIEVAL_CANDIDATE_FIELDS, "lexical retrieval candidate")
            all_candidates.append((candidate, overlap))

        all_candidates.sort(key=lambda item: (-item[0]["score"], item[0]["skill_id"]))
        ranked_candidates = [candidate for candidate, _ in all_candidates[:top_k]]
        score_by_skill_id = {candidate["skill_id"]: candidate["score"] for candidate, _ in all_candidates}
        overlap_by_skill_id = {candidate["skill_id"]: overlap for candidate, overlap in all_candidates}
        warnings = []
        if not query_tokens:
            warnings.append("Task instruction contains no scorable lexical tokens.")
        elif all(candidate["score"] == 0.0 for candidate, _ in all_candidates):
            warnings.append("No native skill shares a lexical token with the task instruction.")

        response: Dict[str, Any] = {
            "retriever_name": self.name,
            "ranked_candidates": ranked_candidates,
            "raw_output": {
                "query_source": "task_instruction_only",
                "query_tokens": sorted(query_tokens),
                "observation_characters": len(observation),
                "scoring": "idf_weighted_token_overlap",
                "scores_by_skill_id": score_by_skill_id,
                "overlap_tokens_by_skill_id": overlap_by_skill_id,
                "requested_top_k": top_k,
            },
            "warnings": warnings,
        }
        require_fields(response, RETRIEVAL_RESPONSE_FIELDS, "lexical retrieval response")
        return response


def _token_set(text: str) -> Set[str]:
    return {_normalize_token(token) for token in TOKEN_PATTERN.findall(text.lower()) if token not in STOPWORDS}


def _normalize_token(token: str) -> str:
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("ing") and len(token) > 5:
        return token[:-3]
    if token.endswith("ed") and len(token) > 4:
        return token[:-2]
    if token.endswith("s") and len(token) > 3:
        return token[:-1]
    return token


def _idf(documents: Iterable[Set[str]]) -> Dict[str, float]:
    document_list = list(documents)
    document_frequency: Counter[str] = Counter()
    for tokens in document_list:
        document_frequency.update(tokens)
    count = len(document_list)
    return {
        token: math.log((1 + count) / (1 + frequency)) + 1.0
        for token, frequency in document_frequency.items()
    }

