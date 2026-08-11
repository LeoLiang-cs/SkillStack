from __future__ import annotations

import unittest

from skillstack.library import load_static_library
from skillstack.retrieval import DebugLexicalRetriever, NoSkillRetriever
from skillstack.tasks import load_p0_tasks


class RetrieverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.task = load_p0_tasks()[0]
        self.library = load_static_library()

    def test_no_skill_control_uses_shared_response_shape(self) -> None:
        response = NoSkillRetriever().retrieve(self.task, "A raw observation.", self.library, top_k=2)
        self.assertEqual("no_skill", response["retriever_name"])
        self.assertEqual([], response["ranked_candidates"])
        self.assertTrue(response["warnings"])

    def test_lexical_retrieval_is_deterministic_and_preserves_payload(self) -> None:
        retriever = DebugLexicalRetriever()
        first = retriever.retrieve(self.task, "Ignored for this baseline.", self.library, top_k=2)
        second = retriever.retrieve(self.task, "A different ignored observation.", self.library, top_k=2)
        self.assertEqual(first["ranked_candidates"], second["ranked_candidates"])
        self.assertEqual(2, len(first["ranked_candidates"]))
        scores = [candidate["score"] for candidate in first["ranked_candidates"]]
        self.assertEqual(scores, sorted(scores, reverse=True))
        for candidate in first["ranked_candidates"]:
            self.assertTrue(candidate["native_payload"].startswith("# "))


if __name__ == "__main__":
    unittest.main()

