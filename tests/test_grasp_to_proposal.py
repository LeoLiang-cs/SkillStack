from __future__ import annotations

import unittest

from skillstack.adapters.grasp_to_proposal import adapt_grasp_output


class GRASPToProposalTests(unittest.TestCase):
    def test_valid_add_is_losslessly_wrapped(self) -> None:
        raw = [{"action": "ADD", "name": "scan_first", "description": "When hidden.",
                "content": "Open containers.", "tags": ["pick"]}]
        batch = adapt_grasp_output(
            raw, triggering_evidence_ids=["failure-1"], writer_model="deepseek-v4-flash",
            decoding={"temperature": 0.8}, call_usage={"prompt_tokens": 1},
        )
        proposal = batch["proposals"][0]
        self.assertEqual("valid", proposal["parse_status"])
        self.assertEqual(raw[0], proposal["native_payload"])
        self.assertEqual("ADD", proposal["normalized_action"])

    def test_modify_is_retained_but_excluded_from_matched_add_cell(self) -> None:
        batch = adapt_grasp_output(
            [{"action": "MODIFY", "name": "old", "description": "d", "content": "c", "tags": []}],
            triggering_evidence_ids=[], writer_model=None, decoding=None, call_usage=None,
        )
        proposal = batch["proposals"][0]
        self.assertEqual("rejected", proposal["parse_status"])
        self.assertEqual("MODIFY", proposal["native_action"])
        self.assertEqual("A.GRASP_NON_ADD_EXCLUDED_MATCHED_CELL", proposal["rejection_reason"])

    def test_empty_output_is_an_explicit_noop(self) -> None:
        batch = adapt_grasp_output(
            [], triggering_evidence_ids=[], writer_model=None, decoding=None, call_usage=None,
        )
        self.assertEqual("empty", batch["parse_status"])
        self.assertEqual("A.GRASP_EMPTY_OUTPUT", batch["no_op_reason"])


if __name__ == "__main__":
    unittest.main()
