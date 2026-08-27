"""Map a valid experiment proposal envelope to GRASP's native edit shape."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Mapping

from skillstack.contracts import PROPOSAL_ENVELOPE_FIELDS, require_fields


def envelope_to_grasp_add(proposal: Mapping[str, Any]) -> Dict[str, Any]:
    """Return one native GRASP ADD proposal without inventing missing fields."""

    require_fields(proposal, PROPOSAL_ENVELOPE_FIELDS, "proposal envelope")
    if proposal["parse_status"] != "valid":
        raise ValueError("Only a valid proposal envelope can enter the GRASP adapter")
    if proposal["normalized_action"] != "ADD":
        raise ValueError("The first GRASP source smoke supports ADD only")

    required_strings = (
        "normalized_name",
        "normalized_description",
        "normalized_content",
    )
    missing = [
        field for field in required_strings
        if not isinstance(proposal[field], str) or not proposal[field].strip()
    ]
    if missing:
        raise ValueError(f"GRASP ADD mapping is missing fields: {', '.join(missing)}")
    tags = proposal["normalized_tags"]
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        raise ValueError("GRASP ADD mapping requires normalized_tags as a string list")

    return {
        "action": "ADD",
        "name": proposal["normalized_name"],
        "description": proposal["normalized_description"],
        "content": proposal["normalized_content"],
        "tags": list(tags),
        "_skillstack_provenance": {
            "proposal_id": proposal["proposal_id"],
            "producer_method": proposal["producer_method"],
            "source_commit": proposal["source_commit"],
            "native_payload": deepcopy(proposal["native_payload"]),
            "adapter_events": deepcopy(proposal["adapter_events"]),
            "unsupported_semantics": list(proposal["unsupported_semantics"]),
        },
    }
