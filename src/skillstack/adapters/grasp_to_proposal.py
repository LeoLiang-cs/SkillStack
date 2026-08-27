"""Wrap released GRASP proposal outputs in the shared experiment envelope."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, Optional, Sequence

from skillstack.proposals import make_proposal_envelope


GRASP_SOURCE_COMMIT = "9d7d125a3e9b46ed591692475eb07aff4ae67d34"


def adapt_grasp_output(
    native_output: Any,
    *,
    triggering_evidence_ids: Iterable[str],
    writer_model: Optional[str],
    decoding: Optional[Mapping[str, Any]],
    call_usage: Optional[Mapping[str, Any]],
) -> Dict[str, Any]:
    """Retain every GRASP output while admitting only valid ADDs to the matched cell."""

    if not isinstance(native_output, list):
        return {
            "producer_method": "GRASP.SkillUpdater.propose",
            "native_output": native_output,
            "proposals": [],
            "parse_status": "parse_error",
            "no_op_reason": "A.GRASP_OUTPUT_NOT_LIST",
        }
    proposals = []
    evidence_ids = list(triggering_evidence_ids)
    for index, candidate in enumerate(native_output, start=1):
        proposals.append(
            _adapt_candidate(
                candidate,
                index=index,
                evidence_ids=evidence_ids,
                writer_model=writer_model,
                decoding=decoding,
                call_usage=call_usage,
            )
        )
    valid = sum(proposal["parse_status"] == "valid" for proposal in proposals)
    if not proposals:
        batch_status = "empty"
    elif valid == len(proposals):
        batch_status = "valid"
    else:
        batch_status = "partial_or_rejected"
    return {
        "producer_method": "GRASP.SkillUpdater.propose",
        "native_output": native_output,
        "proposals": proposals,
        "parse_status": batch_status,
        "no_op_reason": "A.GRASP_EMPTY_OUTPUT" if not proposals else None,
    }


def _adapt_candidate(
    candidate: Any,
    *,
    index: int,
    evidence_ids: Sequence[str],
    writer_model: Optional[str],
    decoding: Optional[Mapping[str, Any]],
    call_usage: Optional[Mapping[str, Any]],
) -> Dict[str, Any]:
    events = []
    action = candidate.get("action") if isinstance(candidate, Mapping) else None
    action = str(action).upper().strip() if action is not None else None
    valid_add = (
        isinstance(candidate, Mapping)
        and action == "ADD"
        and all(isinstance(candidate.get(field), str) and candidate[field].strip()
                for field in ("name", "description", "content"))
        and isinstance(candidate.get("tags", []), list)
    )
    if isinstance(candidate, Mapping):
        for field in ("action", "name", "description", "content", "tags"):
            events.append({
                "source_field": field,
                "target_field": f"normalized_{field}" if field != "action" else "normalized_action",
                "transform_kind": "copy",
                "loss_severity": "none",
                "detail": "Copied from released GRASP proposal.",
            })
    parse_status = "valid" if valid_add else "rejected"
    envelope = make_proposal_envelope(
        proposal_id=f"grasp-{index:03d}",
        producer_method="GRASP.SkillUpdater.propose",
        source_commit=GRASP_SOURCE_COMMIT,
        native_action=action,
        native_payload=candidate,
        normalized_action="ADD" if valid_add else None,
        normalized_name=candidate.get("name") if valid_add else None,
        normalized_description=candidate.get("description") if valid_add else None,
        normalized_content=candidate.get("content") if valid_add else None,
        normalized_tags=candidate.get("tags", []) if valid_add else [],
        triggering_evidence_ids=evidence_ids,
        adapter_events=events,
        unsupported_semantics=[],
        writer_model=writer_model,
        decoding=decoding,
        call_usage=call_usage,
        parse_status=parse_status,
    )
    if not valid_add:
        envelope["rejection_reason"] = (
            "A.GRASP_NON_ADD_EXCLUDED_MATCHED_CELL"
            if action in {"MODIFY", "REMOVE"}
            else "A.GRASP_INVALID_ADD_SCHEMA"
        )
    return envelope
