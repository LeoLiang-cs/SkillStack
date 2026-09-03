"""Opaque SkillOps contract -> byte-identical GRASP Markdown exporter."""

from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping


def export_payloads(payloads: Iterable[Mapping[str, Any]], output_dir: Path) -> List[Dict[str, Any]]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for payload in sorted(payloads, key=lambda item: str(item["skill_id"])):
        skill_id = str(payload["skill_id"])
        adapter = payload.get("metadata", {}).get("skillstack_adapter", {})
        if adapter.get("native_id") != skill_id:
            raise ValueError(f"Opaque exporter refuses changed native ID: {skill_id}")
        encoded = adapter.get("native_bytes_b64")
        if not isinstance(encoded, str):
            raise ValueError(f"Opaque exporter requires original bytes: {skill_id}")
        raw = base64.b64decode(encoded, validate=True)
        expected_hash = adapter.get("native_sha256")
        actual_hash = hashlib.sha256(raw).hexdigest()
        if actual_hash != expected_hash:
            raise ValueError(f"Stored byte hash mismatch for {skill_id}")
        target = output_dir / f"{skill_id}.md"
        target.write_bytes(raw)
        records.append(
            {
                "skillops_id": skill_id,
                "output_id": target.stem,
                "output_file": target.name,
                "sha256": actual_hash,
            }
        )
    return records


def build_id_mapping(
    before: Iterable[Mapping[str, Any]], after: Iterable[Mapping[str, Any]]
) -> List[Dict[str, Any]]:
    """Recover identity-level merge mapping omitted by released sweep report."""

    before_by_id = {str(item["skill_id"]): item for item in before}
    after_by_id = {str(item["skill_id"]): item for item in after}
    after_by_fingerprint: Dict[str, List[str]] = {}
    for skill_id, item in after_by_id.items():
        fingerprint = _fingerprint(item)
        after_by_fingerprint.setdefault(fingerprint, []).append(skill_id)

    mapping = []
    for skill_id, item in sorted(before_by_id.items()):
        if skill_id in after_by_id:
            survivor = skill_id
            status = "retained"
        else:
            candidates = after_by_fingerprint.get(_fingerprint(item), [])
            if len(candidates) != 1:
                raise ValueError(
                    f"Cannot identify unique survivor for {skill_id}: {candidates}"
                )
            survivor = candidates[0]
            status = "merged"
        mapping.append(
            {
                "input_id": skill_id,
                "skillops_id": skill_id,
                "output_id": survivor,
                "status": status,
            }
        )
    return mapping


def _fingerprint(payload: Mapping[str, Any]) -> str:
    return str(
        payload.get("metadata", {})
        .get("skillstack_adapter", {})
        .get("behavior_fingerprint", "")
    )
