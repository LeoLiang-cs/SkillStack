from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from skillstack.adapters.grasp_to_skillops import (
    GraspArtifact,
    adapt_artifact,
    behavior_fingerprint,
    parse_grasp_markdown,
    render_grasp_markdown,
)
from skillstack.adapters.skillops_to_grasp import build_id_mapping, export_payloads


class SkillOpsAdapterTests(unittest.TestCase):
    def setUp(self):
        self.fields = {
            "name": "use_valid_actions",
            "description": "Use an available action.",
            "tags": ["alfworld", "actions"],
            "version": 1,
            "provenance": {"producer": "test"},
            "content": "# Rule\n\nChoose only a listed action.",
        }

    def test_roundtrip_preserves_exact_bytes_and_has_zero_required_loss(self):
        raw = render_grasp_markdown(self.fields)
        artifact = GraspArtifact("skillrl-001", "skillrl-001.md", self.fields, raw)
        payload = adapt_artifact(artifact)
        with tempfile.TemporaryDirectory() as temporary:
            exported = export_payloads([payload], Path(temporary))
            self.assertEqual(raw, (Path(temporary) / "skillrl-001.md").read_bytes())
        self.assertEqual(0, payload["metadata"]["skillstack_adapter"]["ledger_summary"]["required_field_loss"])
        self.assertEqual("skillrl-001", exported[0]["output_id"])

    def test_behavior_fingerprint_ignores_name_and_provenance(self):
        clone = dict(self.fields)
        clone["name"] = "controlled_clone"
        clone["provenance"] = {"synthetic": True}
        self.assertEqual(behavior_fingerprint(self.fields), behavior_fingerprint(clone))

    def test_behavior_fingerprint_changes_with_content(self):
        changed = dict(self.fields)
        changed["content"] = "Different guidance"
        self.assertNotEqual(behavior_fingerprint(self.fields), behavior_fingerprint(changed))

    def test_parse_rendered_markdown(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "candidate.md"
            path.write_bytes(render_grasp_markdown(self.fields))
            parsed = parse_grasp_markdown(path, native_id="grasp-001")
        self.assertEqual("grasp-001", parsed.native_id)
        self.assertEqual(self.fields, parsed.fields)

    def test_id_mapping_reports_exact_clone_merge(self):
        parent = adapt_artifact(
            GraspArtifact("parent", "parent.md", self.fields, render_grasp_markdown(self.fields))
        )
        clone_fields = dict(self.fields, name="clone")
        clone = adapt_artifact(
            GraspArtifact("clone", "clone.md", clone_fields, render_grasp_markdown(clone_fields))
        )
        mapping = build_id_mapping([parent, clone], [parent])
        self.assertEqual("parent", next(item for item in mapping if item["input_id"] == "clone")["output_id"])


if __name__ == "__main__":
    unittest.main()
