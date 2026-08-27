"""Loss-visible adapter from released SkillRL ADD outputs to GRASP candidates."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set

from skillstack.proposals import make_proposal_envelope


SKILLRL_SOURCE_COMMIT = "8e66726ed866a4e0a7f053586a41022798192e6c"
SKILLRL_UNSUPPORTED_SEMANTICS = (
    "MODIFY",
    "REMOVE",
    "verification_examples",
    "probe_scores",
    "refinement",
    "rollback",
)


def adapt_skillrl_output(
    native_output: Any,
    *,
    task_type: str,
    triggering_evidence_ids: Iterable[str],
    existing_names: Iterable[str] = (),
    source_commit: str = SKILLRL_SOURCE_COMMIT,
    writer_model: Optional[str] = "o3",
    decoding: Optional[Mapping[str, Any]] = None,
    call_usage: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Adapt a parsed SkillRL output batch while retaining invalid/no-op states."""

    raw_copy = deepcopy(native_output)
    if not isinstance(native_output, list):
        return _batch_result(raw_copy, [], "parse_error", "A.SKILLRL_OUTPUT_NOT_LIST")
    if not native_output:
        return _batch_result(raw_copy, [], "empty", "A.SKILLRL_EMPTY_OUTPUT")

    evidence_ids = tuple(triggering_evidence_ids)
    occupied_names = set(existing_names)
    seen_names: Set[str] = set()
    proposals = []
    for index, candidate in enumerate(native_output, start=1):
        proposal = _adapt_candidate(
            candidate,
            index=index,
            task_type=task_type,
            triggering_evidence_ids=evidence_ids,
            occupied_names=occupied_names,
            seen_names=seen_names,
            source_commit=source_commit,
            writer_model=writer_model,
            decoding=decoding,
            call_usage=call_usage,
        )
        if index > 3:
            proposal["parse_status"] = "rejected"
            proposal["rejection_reason"] = "A.MATCHED_ADD_CAP_EXCEEDED"
            proposal["adapter_events"].append(
                _event(
                    "batch_index",
                    "matched_candidate_cap",
                    "copy",
                    "fatal",
                    "Candidate retained but excluded because the matched ADD cap is three.",
                )
            )
        proposals.append(proposal)

    valid_count = sum(proposal["parse_status"] == "valid" for proposal in proposals)
    batch_status = "valid" if valid_count == len(proposals) else "partial_or_rejected"
    return _batch_result(raw_copy, proposals, batch_status, None)


def _adapt_candidate(
    candidate: Any,
    *,
    index: int,
    task_type: str,
    triggering_evidence_ids: Sequence[str],
    occupied_names: Set[str],
    seen_names: Set[str],
    source_commit: str,
    writer_model: Optional[str],
    decoding: Optional[Mapping[str, Any]],
    call_usage: Optional[Mapping[str, Any]],
) -> Dict[str, Any]:
    proposal_id = f"skillrl-{index:03d}"
    events: List[Dict[str, Any]] = []
    if not isinstance(candidate, Mapping):
        events.append(_event("native_payload", None, "copy", "fatal", "Candidate is not an object."))
        return _invalid_envelope(
            proposal_id, candidate, source_commit, triggering_evidence_ids, events,
            writer_model, decoding, call_usage, "A.SKILLRL_CANDIDATE_NOT_OBJECT",
        )

    missing = [
        field for field in ("skill_id", "title", "principle", "when_to_apply")
        if not isinstance(candidate.get(field), str) or not candidate[field].strip()
    ]
    if missing:
        events.append(
            _event(
                ",".join(missing),
                None,
                "copy",
                "fatal",
                "Required SkillRL fields are missing or empty; no value was inferred.",
            )
        )
        return _invalid_envelope(
            proposal_id, candidate, source_commit, triggering_evidence_ids, events,
            writer_model, decoding, call_usage, f"A.SKILLRL_MISSING_{'_'.join(missing).upper()}",
        )

    title = candidate["title"].strip()
    principle = candidate["principle"].strip()
    when_to_apply = candidate["when_to_apply"].strip()
    name = _slugify(title)
    if not name:
        events.append(_event("title", "normalized_name", "rename", "fatal", "Title has no slug characters."))
        return _invalid_envelope(
            proposal_id, candidate, source_commit, triggering_evidence_ids, events,
            writer_model, decoding, call_usage, "A.SKILLRL_EMPTY_SLUG",
        )

    events.extend(
        [
            _event("released_updater_capability", "normalized_action", "synthesize", "none", "ADD only."),
            _event("skill_id", "native_payload.skill_id", "copy", "none", "Native ID retained as provenance."),
            _event("title", "normalized_name", "rename", "low", "GRASP-compatible lowercase underscore slug."),
            _event("when_to_apply", "normalized_description", "copy", "none", "Copied without inference."),
            _event("principle+when_to_apply", "normalized_content", "construct", "low", "Template skillrl-grasp-md-v0."),
            _event("task_type", "normalized_tags", "construct", "low", "One source task-type tag."),
        ]
    )
    parse_status = "valid"
    if name in occupied_names or name in seen_names:
        parse_status = "rejected"
        events.append(_event("normalized_name", "gate.name", "copy", "fatal", "A.DUPLICATE_NAME"))
    seen_names.add(name)

    content = f"# {title}\n\n## Trigger\n\n{when_to_apply}\n\n## Rule\n\n{principle}\n"
    envelope = make_proposal_envelope(
        proposal_id=proposal_id,
        producer_method="SkillRL.SkillUpdater.analyze_failures",
        source_commit=source_commit,
        native_action=None,
        native_payload=candidate,
        normalized_action="ADD",
        normalized_name=name,
        normalized_description=when_to_apply,
        normalized_content=content,
        normalized_tags=[task_type],
        triggering_evidence_ids=triggering_evidence_ids,
        adapter_events=events,
        unsupported_semantics=SKILLRL_UNSUPPORTED_SEMANTICS,
        writer_model=writer_model,
        decoding=decoding,
        call_usage=call_usage,
        parse_status=parse_status,
    )
    if parse_status == "rejected":
        envelope["rejection_reason"] = "A.DUPLICATE_NAME"
    return envelope


def _invalid_envelope(
    proposal_id: str,
    native_payload: Any,
    source_commit: str,
    evidence_ids: Sequence[str],
    events: Sequence[Mapping[str, Any]],
    writer_model: Optional[str],
    decoding: Optional[Mapping[str, Any]],
    call_usage: Optional[Mapping[str, Any]],
    reason: str,
) -> Dict[str, Any]:
    envelope = make_proposal_envelope(
        proposal_id=proposal_id,
        producer_method="SkillRL.SkillUpdater.analyze_failures",
        source_commit=source_commit,
        native_action=None,
        native_payload=native_payload,
        normalized_action=None,
        normalized_name=None,
        normalized_description=None,
        normalized_content=None,
        normalized_tags=[],
        triggering_evidence_ids=evidence_ids,
        adapter_events=events,
        unsupported_semantics=SKILLRL_UNSUPPORTED_SEMANTICS,
        writer_model=writer_model,
        decoding=decoding,
        call_usage=call_usage,
        parse_status="rejected",
    )
    envelope["rejection_reason"] = reason
    return envelope


def _batch_result(
    native_output: Any,
    proposals: Sequence[Mapping[str, Any]],
    parse_status: str,
    no_op_reason: Optional[str],
) -> Dict[str, Any]:
    return {
        "producer_method": "SkillRL.SkillUpdater.analyze_failures",
        "native_output": deepcopy(native_output),
        "proposals": [deepcopy(dict(proposal)) for proposal in proposals],
        "parse_status": parse_status,
        "no_op_reason": no_op_reason,
    }


def _event(
    source_field: str,
    target_field: Optional[str],
    transform_kind: str,
    loss_severity: str,
    detail: str,
) -> Dict[str, Any]:
    return {
        "source_field": source_field,
        "target_field": target_field,
        "transform_kind": transform_kind,
        "loss_severity": loss_severity,
        "detail": detail,
    }


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
