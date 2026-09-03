from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from skillstack.adapters.grasp_to_skillops import render_grasp_markdown
from skillstack.experiments.skillops_maintenance import (
    build_stress_fixture,
    run_m1,
    run_m2,
)


SKILLOPS_ROOT = Path("/Users/leo/Project/Research/USC/FORTIS/_external/week6/SkillOps")


@unittest.skipUnless((SKILLOPS_ROOT / "skillops" / "maintenance.py").is_file(), "pinned SkillOps checkout unavailable")
class OfficialSkillOpsIntegrationTests(unittest.TestCase):
    def _write_clean(self, path: Path):
        for identifier, marker in (("grasp-001", "goal"), ("skillrl-001", "action")):
            fields = {
                "name": marker,
                "description": f"description {marker}",
                "tags": [marker],
                "version": 1,
                "provenance": {"candidate_id": identifier},
                "content": f"# {marker}\n\nGuidance for {marker}.",
            }
            (path / f"{identifier}.md").write_bytes(render_grasp_markdown(fields))

    def test_clean_noop_and_controlled_duplicate_merge(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            clean = root / "clean"
            clean.mkdir()
            self._write_clean(clean)
            m1 = run_m1(clean, root / "m1", SKILLOPS_ROOT)
            self.assertTrue(m1["accepted"])
            debt = build_stress_fixture(clean, root / "stress")
            m2 = run_m2(root / "stress", root / "m2", SKILLOPS_ROOT, debt["debt"])
            self.assertTrue(m2["accepted"])
            self.assertEqual(1.0, m2["merge_precision"])
            self.assertEqual(1.0, m2["merge_recall"])
            self.assertEqual(2, m2["sweep_report"]["merged"])


if __name__ == "__main__":
    unittest.main()
