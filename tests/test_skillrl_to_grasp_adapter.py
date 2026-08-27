from __future__ import annotations

import copy
import unittest

from skillstack.adapters.skillrl_to_grasp import adapt_skillrl_output
from skillstack.contracts import PROPOSAL_ENVELOPE_FIELDS, require_fields


class SkillRLToGRASPAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.candidate = {
            "skill_id": "dyn_001",
            "title": "Check Containers First",
            "principle": "Inspect closed containers before searching elsewhere.",
            "when_to_apply": "When an object is not visible in the current room.",
            "extra_native_field": {"must": "survive"},
        }

    def test_valid_candidate_is_mapped_and_native_payload_is_preserved(self) -> None:
        original = copy.deepcopy(self.candidate)
        batch = adapt_skillrl_output(
            [self.candidate],
            task_type="pick_and_place",
            triggering_evidence_ids=["task-17"],
            decoding={"temperature": 0.0},
            call_usage={"prompt_tokens": 12},
        )
        proposal = batch["proposals"][0]
        require_fields(proposal, PROPOSAL_ENVELOPE_FIELDS, "test proposal")
        self.assertEqual("valid", proposal["parse_status"])
        self.assertEqual("ADD", proposal["normalized_action"])
        self.assertEqual("check_containers_first", proposal["normalized_name"])
        self.assertEqual(["pick_and_place"], proposal["normalized_tags"])
        self.assertIn("## Trigger", proposal["normalized_content"])
        self.assertIn("## Rule", proposal["normalized_content"])
        self.assertEqual(original, proposal["native_payload"])
        self.assertEqual(original, self.candidate)
        self.assertTrue(all(event["transform_kind"] in {"copy", "rename", "construct", "synthesize"}
                            for event in proposal["adapter_events"]))
        self.assertNotIn("MODIFY", {proposal["normalized_action"]})
        self.assertNotIn("REMOVE", {proposal["normalized_action"]})

    def test_missing_when_to_apply_is_rejected_without_guessing(self) -> None:
        del self.candidate["when_to_apply"]
        proposal = adapt_skillrl_output(
            [self.candidate], task_type="heat", triggering_evidence_ids=[]
        )["proposals"][0]
        self.assertEqual("rejected", proposal["parse_status"])
        self.assertEqual("A.SKILLRL_MISSING_WHEN_TO_APPLY", proposal["rejection_reason"])
        self.assertIsNone(proposal["normalized_description"])
        self.assertIsNone(proposal["normalized_content"])

    def test_parse_failure_and_empty_output_remain_explicit_noops(self) -> None:
        parse_failure = adapt_skillrl_output(
            "not parsed JSON", task_type="heat", triggering_evidence_ids=[]
        )
        empty = adapt_skillrl_output([], task_type="heat", triggering_evidence_ids=[])
        self.assertEqual("parse_error", parse_failure["parse_status"])
        self.assertEqual("not parsed JSON", parse_failure["native_output"])
        self.assertEqual("A.SKILLRL_OUTPUT_NOT_LIST", parse_failure["no_op_reason"])
        self.assertEqual("empty", empty["parse_status"])
        self.assertEqual("A.SKILLRL_EMPTY_OUTPUT", empty["no_op_reason"])

    def test_duplicate_names_are_retained_as_rejections(self) -> None:
        duplicate = dict(self.candidate, skill_id="dyn_002")
        batch = adapt_skillrl_output(
            [self.candidate, duplicate],
            task_type="pick_and_place",
            triggering_evidence_ids=[],
        )
        self.assertEqual(2, len(batch["proposals"]))
        self.assertEqual("valid", batch["proposals"][0]["parse_status"])
        self.assertEqual("rejected", batch["proposals"][1]["parse_status"])
        self.assertEqual("A.DUPLICATE_NAME", batch["proposals"][1]["rejection_reason"])
        self.assertEqual("partial_or_rejected", batch["parse_status"])

    def test_candidates_beyond_matched_cap_are_retained_but_excluded(self) -> None:
        candidates = [dict(self.candidate, skill_id=f"dyn_{index:03d}", title=f"Rule {index}")
                      for index in range(1, 5)]
        batch = adapt_skillrl_output(
            candidates, task_type="fixture", triggering_evidence_ids=[]
        )
        self.assertEqual(4, len(batch["proposals"]))
        self.assertTrue(all(proposal["parse_status"] == "valid"
                            for proposal in batch["proposals"][:3]))
        self.assertEqual("rejected", batch["proposals"][3]["parse_status"])
        self.assertEqual(
            "A.MATCHED_ADD_CAP_EXCEEDED", batch["proposals"][3]["rejection_reason"]
        )


if __name__ == "__main__":
    unittest.main()
