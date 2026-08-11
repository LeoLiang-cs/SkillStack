from __future__ import annotations

import unittest

from skillstack.adapters.retrieval_to_execution import adapt_retrieval_for_execution
from skillstack.library import load_static_library
from skillstack.retrieval import DebugLexicalRetriever
from skillstack.tasks import load_p0_tasks


class AdapterTests(unittest.TestCase):
    def test_adapter_preserves_selected_native_payloads(self) -> None:
        skills = load_static_library()
        response = DebugLexicalRetriever().retrieve(load_p0_tasks()[0], "", skills, top_k=2)
        execution_input, event = adapt_retrieval_for_execution(response)
        self.assertEqual(
            [candidate["native_payload"] for candidate in response["ranked_candidates"]],
            execution_input["selected_native_skills"],
        )
        self.assertEqual([], event["dropped"])
        self.assertEqual([], event["approximated"])
        self.assertIn("flat_skill_context", event["generated"])


if __name__ == "__main__":
    unittest.main()

