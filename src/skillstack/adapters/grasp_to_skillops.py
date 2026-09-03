"""Loss-audited GRASP Markdown -> opaque SkillOps contract adapter.

The adapter deliberately does not infer semantic SkillOps P/O/A/V/F fields
from free-form behavioural guidance.  Exact behavioural fingerprints are used
only to exercise released duplicate-maintenance primitives.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

import yaml


CONTRACT_VERSION = "opaque_fingerprint_v0"
FIDELITY = "source_variant_opaque_contract"
DOMAIN_TYPE = "alfworld_behavioral_guidance"
_FRONTMATTER = re.compile(rb"^---\n(.*?)\n---\n(.*)", re.DOTALL)


@dataclass(frozen=True)
class GraspArtifact:
    """A GRASP skill with both parsed fields and its immutable source bytes."""

    native_id: str
    filename: str
    fields: Dict[str, Any]
    raw_bytes: bytes

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.raw_bytes).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def behavior_fingerprint(fields: Mapping[str, Any]) -> str:
    """Fingerprint behavioural payload while excluding identity/provenance."""

    payload = {
        "description": str(fields.get("description", "")),
        "content": str(fields.get("content", "")),
        "tags": sorted(str(tag) for tag in (fields.get("tags") or [])),
    }
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def render_grasp_markdown(fields: Mapping[str, Any]) -> bytes:
    """Render a deterministic GRASP-compatible Markdown skill file."""

    metadata: Dict[str, Any] = {
        "name": str(fields["name"]),
        "description": str(fields.get("description", "")),
        "tags": list(fields.get("tags") or []),
        "version": int(fields.get("version", 1)),
    }
    if fields.get("provenance") is not None:
        metadata["provenance"] = fields["provenance"]
    frontmatter = yaml.dump(
        metadata,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=True,
    ).strip()
    return f"---\n{frontmatter}\n---\n\n{str(fields.get('content', '')).strip()}\n".encode(
        "utf-8"
    )


def parse_grasp_markdown(path: Path, *, native_id: str | None = None) -> GraspArtifact:
    raw = Path(path).read_bytes()
    match = _FRONTMATTER.match(raw)
    if not match:
        metadata: Dict[str, Any] = {}
        content = raw.decode("utf-8").strip()
    else:
        metadata = yaml.safe_load(match.group(1).decode("utf-8")) or {}
        content = match.group(2).decode("utf-8").strip()
    fields = {
        "name": metadata.get("name", Path(path).stem),
        "description": metadata.get("description", ""),
        "tags": metadata.get("tags") or [],
        "version": metadata.get("version", 0),
        "provenance": metadata.get("provenance"),
        "content": content,
    }
    return GraspArtifact(
        native_id=native_id or Path(path).stem,
        filename=Path(path).name,
        fields=fields,
        raw_bytes=raw,
    )


def load_grasp_directory(path: Path) -> List[GraspArtifact]:
    return [parse_grasp_markdown(item) for item in sorted(Path(path).glob("*.md"))]


def adapt_artifact(artifact: GraspArtifact) -> Dict[str, Any]:
    """Create a serializable payload accepted by ``Skill.from_dict``."""

    fingerprint = behavior_fingerprint(artifact.fields)
    controlled_debt = _controlled_debt(artifact.fields.get("provenance"))
    ledger = _field_ledger()
    return {
        "skill_id": artifact.native_id,
        "name": str(artifact.fields["name"]),
        "domain_type": DOMAIN_TYPE,
        "contract": {
            "precondition": {"behavior_fingerprint": fingerprint},
            "operation": [
                {"name": "InjectBehavioralGuidance", "args": [fingerprint]}
            ],
            "artifact": {
                "host_format": "grasp_markdown",
                "behavior_fingerprint": fingerprint,
            },
            "validator": [],
            "failure_modes": [],
        },
        "is_synthetic": bool(controlled_debt),
        "parent_skill_id": controlled_debt.get("parent_skill_id") if controlled_debt else None,
        "degradation_tag": controlled_debt.get("kind") if controlled_debt else None,
        "metadata": {
            "skillstack_adapter": {
                "contract_version": CONTRACT_VERSION,
                "fidelity": FIDELITY,
                "semantic_contract_inferred": False,
                "native_id": artifact.native_id,
                "native_filename": artifact.filename,
                "native_sha256": artifact.sha256,
                "native_bytes_b64": base64.b64encode(artifact.raw_bytes).decode("ascii"),
                "native_fields": artifact.fields,
                "behavior_fingerprint": fingerprint,
                "field_ledger": ledger,
                "ledger_summary": summarize_ledger(ledger),
            }
        },
    }


def adapt_directory(path: Path) -> List[Dict[str, Any]]:
    artifacts = load_grasp_directory(path)
    ids = [artifact.native_id for artifact in artifacts]
    if len(ids) != len(set(ids)):
        raise ValueError("GRASP directory contains duplicate native IDs")
    return [adapt_artifact(artifact) for artifact in artifacts]


def summarize_ledger(entries: Iterable[Mapping[str, Any]]) -> Dict[str, int]:
    summary = {
        "copy": 0,
        "construct": 0,
        "synthesize": 0,
        "drop": 0,
        "approximate": 0,
        "required_field_loss": 0,
    }
    for entry in entries:
        kind = str(entry["transform_kind"])
        if kind in summary:
            summary[kind] += 1
        if entry.get("required") and kind in {"drop", "approximate"}:
            summary["required_field_loss"] += 1
    return summary


def _controlled_debt(provenance: Any) -> Dict[str, Any]:
    if not isinstance(provenance, Mapping):
        return {}
    marker = provenance.get("skillstack_controlled_debt")
    return dict(marker) if isinstance(marker, Mapping) else {}


def _field_ledger() -> List[Dict[str, Any]]:
    entries = []
    for field in ("name", "description", "tags", "version", "provenance", "content"):
        entries.append(
            {
                "source_field": field,
                "target_field": f"metadata.skillstack_adapter.native_fields.{field}",
                "transform_kind": "copy",
                "required": field in {"name", "description", "tags", "content"},
            }
        )
    entries.extend(
        [
            {
                "source_field": "native_file_bytes",
                "target_field": "metadata.skillstack_adapter.native_bytes_b64",
                "transform_kind": "copy",
                "required": True,
            },
            {
                "source_field": "description+content+tags",
                "target_field": "contract.precondition.behavior_fingerprint",
                "transform_kind": "construct",
                "required": True,
            },
            {
                "source_field": "description+content+tags",
                "target_field": "contract.artifact.behavior_fingerprint",
                "transform_kind": "construct",
                "required": True,
            },
            {
                "source_field": None,
                "target_field": "contract.operation.InjectBehavioralGuidance",
                "transform_kind": "synthesize",
                "required": True,
            },
            {
                "source_field": None,
                "target_field": "contract.validator+failure_modes",
                "transform_kind": "synthesize",
                "required": True,
            },
        ]
    )
    return entries
