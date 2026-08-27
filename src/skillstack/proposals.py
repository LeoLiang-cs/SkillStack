"""Experiment-boundary proposal envelopes that preserve native candidates."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, Mapping, Optional

from skillstack.contracts import PROPOSAL_ENVELOPE_FIELDS, require_fields


def make_proposal_envelope(
    *,
    proposal_id: str,
    producer_method: str,
    source_commit: str,
    native_action: Optional[str],
    native_payload: Any,
    normalized_action: Optional[str],
    normalized_name: Optional[str],
    normalized_description: Optional[str],
    normalized_content: Optional[str],
    normalized_tags: Iterable[str],
    triggering_evidence_ids: Iterable[str],
    adapter_events: Iterable[Mapping[str, Any]],
    unsupported_semantics: Iterable[str],
    writer_model: Optional[str],
    decoding: Optional[Mapping[str, Any]],
    call_usage: Optional[Mapping[str, Any]],
    parse_status: str,
) -> Dict[str, Any]:
    """Wrap one candidate without replacing or mutating its native payload."""

    envelope: Dict[str, Any] = {
        "proposal_id": proposal_id,
        "producer_method": producer_method,
        "source_commit": source_commit,
        "native_action": native_action,
        "native_payload": deepcopy(native_payload),
        "normalized_action": normalized_action,
        "normalized_name": normalized_name,
        "normalized_description": normalized_description,
        "normalized_content": normalized_content,
        "normalized_tags": list(normalized_tags),
        "triggering_evidence_ids": list(triggering_evidence_ids),
        "adapter_events": [dict(event) for event in adapter_events],
        "unsupported_semantics": list(unsupported_semantics),
        "writer_model": writer_model,
        "decoding": deepcopy(decoding),
        "call_usage": deepcopy(call_usage),
        "parse_status": parse_status,
    }
    require_fields(envelope, PROPOSAL_ENVELOPE_FIELDS, "proposal envelope")
    return envelope
