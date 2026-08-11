from __future__ import annotations

import unittest

from skillstack.contracts import NATIVE_SKILL_FIELDS, require_fields
from skillstack.library import load_static_library


class StaticLibraryTests(unittest.TestCase):
    def test_loads_all_native_skill_artifacts(self) -> None:
        artifacts = load_static_library()
        self.assertEqual(6, len(artifacts))
        self.assertEqual([artifact["skill_id"] for artifact in artifacts], sorted(artifact["skill_id"] for artifact in artifacts))
        for artifact in artifacts:
            require_fields(artifact, NATIVE_SKILL_FIELDS, "test artifact")
            self.assertTrue(artifact["native_payload"].startswith("# "))
            self.assertIn("Task family", artifact["native_payload"])

    def test_skill_ids_are_unique(self) -> None:
        artifacts = load_static_library()
        skill_ids = [artifact["skill_id"] for artifact in artifacts]
        self.assertEqual(len(skill_ids), len(set(skill_ids)))


if __name__ == "__main__":
    unittest.main()

