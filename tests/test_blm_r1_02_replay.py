from __future__ import annotations

import copy
import json
import unittest

from skillstack.experiments.blm_calibration import (
    FIXTURE_SCOPE,
    materialize_first_handoff_envelope,
    replay_first_handoff_envelope,
    stable_projection,
)


class R102FirstHandoffReplayTests(unittest.TestCase):
    def test_reference_crossed_and_noop_replay_three_times_exactly(self) -> None:
        for arm_id in ("reference", "crossed", "crossed_noop"):
            envelope = materialize_first_handoff_envelope(arm_id)
            results = [replay_first_handoff_envelope(envelope) for _ in range(3)]
            self.assertTrue(all(item["measurement_status"] == "valid" for item in results))
            self.assertEqual(results[0], results[1], arm_id)
            self.assertEqual(results[0], results[2], arm_id)
            self.assertEqual(FIXTURE_SCOPE, envelope["state_scope"])
            self.assertTrue(results[0]["consumer_called"])

    def test_envelope_hash_is_key_order_independent(self) -> None:
        envelope = materialize_first_handoff_envelope("reference")
        reordered = {key: envelope[key] for key in reversed(list(envelope))}
        self.assertEqual(
            replay_first_handoff_envelope(envelope),
            replay_first_handoff_envelope(reordered),
        )
        round_trip = json.loads(json.dumps(envelope, ensure_ascii=False))
        self.assertEqual(
            replay_first_handoff_envelope(envelope),
            replay_first_handoff_envelope(round_trip),
        )

    def test_hash_and_state_drift_fail_closed_before_consumer(self) -> None:
        baseline = materialize_first_handoff_envelope("reference")
        mutations = (
            ("task", {"task_instruction": "tampered"}),
            ("environment", {"initial_observation": "tampered"}),
            ("consumer", {"max_steps": 11}),
            ("producer", {"output": {"retriever_name": "tampered"}}),
            ("adapter", {"execution_input": {"selected_skill_ids": []}}),
            ("native_library", {"sha256": "0" * 64}),
            ("code_revision", {"module_sha256": "0" * 64}),
        )
        for section, changes in mutations:
            envelope = copy.deepcopy(baseline)
            envelope[section].update(changes)
            result = replay_first_handoff_envelope(envelope)
            self.assertEqual("abstained", result["measurement_status"], section)
            self.assertFalse(result["consumer_called"], section)
            self.assertEqual("replay_state_incomplete", result["reason"], section)
            self.assertTrue(result["reason_detail"].startswith("replay_state_incomplete:"), section)

    def test_scope_does_not_claim_mid_episode_snapshot(self) -> None:
        envelope = materialize_first_handoff_envelope("crossed")
        self.assertEqual("first_handoff_reconstructed_fixture_v1", envelope["state_scope"])
        self.assertNotIn("mid_episode_snapshot", envelope)

    def test_crossed_noop_matches_uninstrumented_projection(self) -> None:
        crossed = materialize_first_handoff_envelope("crossed")
        replayed_crossed = replay_first_handoff_envelope(crossed)
        noop = materialize_first_handoff_envelope("crossed_noop")
        replayed_noop = replay_first_handoff_envelope(noop)
        self.assertEqual(
            stable_projection(replayed_crossed["trace_projection"]),
            stable_projection(replayed_noop["trace_projection"]),
        )
        self.assertFalse(replayed_noop["boundary"]["changed"])


if __name__ == "__main__":
    unittest.main()
