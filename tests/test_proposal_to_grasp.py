from __future__ import annotations

import unittest

from skillstack.adapters.proposal_to_grasp import envelope_to_grasp_add
from skillstack.adapters.skillrl_to_grasp import adapt_skillrl_output


class ProposalToGRASPTests(unittest.TestCase):
    def _valid_envelope(self):
        return adapt_skillrl_output(
            [{
                "skill_id": "dyn_001",
                "title": "Systematic Container Search",
                "principle": "Open containers before leaving.",
                "when_to_apply": "When the object is not visible.",
            }],
            task_type="pick_and_place",
            triggering_evidence_ids=["task-1"],
        )["proposals"][0]

    def test_maps_only_declared_fields_and_preserves_skillstack_provenance(self) -> None:
        envelope = self._valid_envelope()
        native = envelope_to_grasp_add(envelope)
        self.assertEqual("ADD", native["action"])
        self.assertEqual("systematic_container_search", native["name"])
        self.assertEqual(["pick_and_place"], native["tags"])
        self.assertEqual(envelope["native_payload"], native["_skillstack_provenance"]["native_payload"])

    def test_rejects_invalid_or_non_add_envelopes(self) -> None:
        invalid = self._valid_envelope()
        invalid["parse_status"] = "rejected"
        with self.assertRaisesRegex(ValueError, "valid proposal"):
            envelope_to_grasp_add(invalid)

        non_add = self._valid_envelope()
        non_add["normalized_action"] = "REMOVE"
        with self.assertRaisesRegex(ValueError, "ADD only"):
            envelope_to_grasp_add(non_add)


if __name__ == "__main__":
    unittest.main()
