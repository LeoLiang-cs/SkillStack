"""Minimal P0.0 runtime-boundary helpers, not a canonical skill schema."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, MutableMapping


TASK_RECORD_FIELDS = ("task_id", "task_family", "task_instruction", "game_file")
NATIVE_SKILL_FIELDS = ("skill_id", "source_path", "native_payload", "local_metadata")
RETRIEVAL_CANDIDATE_FIELDS = ("skill_id", "score", "native_payload")
RETRIEVAL_RESPONSE_FIELDS = ("retriever_name", "ranked_candidates", "raw_output", "warnings")
ADAPTER_EVENT_FIELDS = (
    "component",
    "read",
    "generated",
    "dropped",
    "approximated",
    "defaulted",
    "warnings",
)
EXECUTOR_REPORT_FIELDS = ("actions", "observations", "rewards", "success", "stop_reason", "warnings")
PROPOSAL_ENVELOPE_FIELDS = (
    "proposal_id",
    "producer_method",
    "source_commit",
    "native_action",
    "native_payload",
    "normalized_action",
    "normalized_name",
    "normalized_description",
    "normalized_content",
    "normalized_tags",
    "triggering_evidence_ids",
    "adapter_events",
    "unsupported_semantics",
    "writer_model",
    "decoding",
    "call_usage",
    "parse_status",
)


def require_fields(
    payload: Mapping[str, Any], required_fields: Iterable[str], context: str
) -> None:
    """Raise a clear error when a P0.0 boundary payload is incomplete."""

    missing = [field for field in required_fields if field not in payload]
    if missing:
        raise ValueError(f"{context} is missing required fields: {', '.join(missing)}")


def empty_adapter_event() -> MutableMapping[str, Any]:
    """Create an explicit record of an adapter that has made no transformations."""

    return {
        "component": "retrieval_to_execution_adapter",
        "read": [],
        "generated": [],
        "dropped": [],
        "approximated": [],
        "defaulted": [],
        "warnings": [],
    }
