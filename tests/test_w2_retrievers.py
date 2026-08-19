from __future__ import annotations

import unittest

from skillstack.library import load_static_library
from skillstack.retrieval import OracleSkillRetriever, RandomSkillRetriever
from skillstack.tasks import load_p0_tasks


class OracleRetrieverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.library = load_static_library()
        self.tasks = load_p0_tasks()

    def test_returns_frozen_expected_skill(self) -> None:
        task = self.tasks[0]
        response = OracleSkillRetriever().retrieve(task, "obs", self.library, top_k=2)
        self.assertEqual("oracle_skill", response["retriever_name"])
        self.assertEqual([task["expected_skill_id"]], [c["skill_id"] for c in response["ranked_candidates"]])
        self.assertEqual([], response["warnings"])

    def test_missing_expected_skill_id_warns_and_returns_empty(self) -> None:
        task = dict(self.tasks[0])
        task.pop("expected_skill_id")
        response = OracleSkillRetriever().retrieve(task, "obs", self.library, top_k=2)
        self.assertEqual([], response["ranked_candidates"])
        self.assertTrue(response["warnings"])


class RandomRetrieverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.library = load_static_library()
        self.task = load_p0_tasks()[0]

    def test_deterministic_for_fixed_seed(self) -> None:
        first = RandomSkillRetriever(seed=42).retrieve(self.task, "obs", self.library, top_k=2)
        second = RandomSkillRetriever(seed=42).retrieve(self.task, "obs", self.library, top_k=2)
        self.assertEqual(first["ranked_candidates"], second["ranked_candidates"])

    def test_preserves_native_payload(self) -> None:
        response = RandomSkillRetriever(seed=42).retrieve(self.task, "obs", self.library, top_k=3)
        self.assertEqual(3, len(response["ranked_candidates"]))
        for candidate in response["ranked_candidates"]:
            self.assertTrue(candidate["native_payload"].startswith("# "))


if __name__ == "__main__":
    unittest.main()
