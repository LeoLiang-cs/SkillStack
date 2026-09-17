from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.run_blm_calibration import _run
from skillstack.experiments.blm_calibration import evaluate_calibration_case


def case(case_id, measurement_status="valid", **fields):
    record = {
        "case_id": case_id,
        "measurement_status": measurement_status,
        "claim_id": fields.pop("claim_id", "local-c1"),
        "claim": fields.pop(
            "claim",
            {"claim_id": "local-c1", "type": "conformance", "explicit": True,
             "scope": "frozen heat fixture / SkillPlanExecutor"},
        ),
        "verdict_scope": fields.pop("verdict_scope", "frozen heat fixture / SkillPlanExecutor"),
        "gates_complete": fields.pop("gates_complete", True),
        "observed_relation": fields.pop("observed_relation", "exact_match"),
        "evidence_refs": ["fixture"],
        "excluded_claims": ["natural cases", "model-internal reads"],
        "calibration_only": True,
    }
    record.update(fields)
    return record


class R105BoundedVerdictTests(unittest.TestCase):
    def test_identity_and_unread_cases_are_limited_not_falsified(self) -> None:
        for relation in ("single_atom_exact", "no_change"):
            verdict = evaluate_calibration_case(case(relation, observed_relation=relation))
            self.assertEqual("valid", verdict["measurement_status"])
            self.assertEqual("not_falsified", verdict["contract_verdict"])
            self.assertTrue(verdict["calibration_only"])

    def test_invalid_and_abstained_cases_never_falsify(self) -> None:
        for status, reason in (
            ("invalid", "adapter_transport_nonconformance"),
            ("abstained", "replay_state_incomplete"),
        ):
            verdict = evaluate_calibration_case(
                case("invalid", measurement_status=status, reason_code=reason)
            )
            self.assertEqual("abstained", verdict["contract_verdict"])
            self.assertEqual(reason, verdict["reason_code"])

    def test_no_claim_or_incomplete_gate_abstains(self) -> None:
        no_claim = case("no-claim", claim=None)
        no_claim.pop("claim")
        self.assertEqual(
            "abstained", evaluate_calibration_case(no_claim)["contract_verdict"]
        )
        incomplete = evaluate_calibration_case(case("incomplete", gates_complete=False))
        self.assertEqual("incomplete_gate", incomplete["reason_code"])
        self.assertEqual("abstained", incomplete["contract_verdict"])

    def test_only_explicit_synthetic_joint_case_can_be_falsified(self) -> None:
        synthetic = case(
            "synthetic-joint",
            claim={
                "claim_id": "synthetic-independent-sufficiency",
                "type": "synthetic_independent_sufficiency",
                "explicit": True,
                "scope": "test-only synthetic classifier record",
            },
            claim_id="synthetic-independent-sufficiency",
            verdict_scope="test-only synthetic classifier record",
            synthetic_test_only=True,
            observed_relation="joint_only",
        )
        verdict = evaluate_calibration_case(synthetic)
        self.assertEqual("falsified", verdict["contract_verdict"])
        self.assertEqual("synthetic_independent_sufficiency_failed", verdict["reason_code"])

        broad = copy.deepcopy(synthetic)
        broad["claim"]["type"] = "sufficiency"
        broad["synthetic_test_only"] = False
        self.assertEqual(
            "abstained", evaluate_calibration_case(broad)["contract_verdict"]
        )

    def test_diagnostics_and_missing_outcomes_abstain(self) -> None:
        for diagnostic in (
            "consumer_semantic_read_unverified",
            "no_op_changed_result",
            "incomplete_arm",
            "budget_exhausted",
        ):
            verdict = evaluate_calibration_case(case("diagnostic", diagnostic=diagnostic))
            self.assertEqual("abstained", verdict["contract_verdict"])
            self.assertEqual(diagnostic, verdict["reason_code"])
        missing = evaluate_calibration_case(case("missing", observed_relation="unknown"))
        self.assertEqual("abstained", missing["contract_verdict"])
        self.assertNotIn("supported", str(missing).lower())

    def test_interrupted_run_resumes_without_duplicate_episode_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _run(root)
            run_dir = root / "r1_05_calibration_run"
            episodes = run_dir / "episodes.jsonl"
            lines = episodes.read_text(encoding="utf-8").splitlines()
            episodes.write_text("\n".join(lines[:5]) + "\n", encoding="utf-8")
            for name in ("summary.json", "verdicts.json", "atom_census.json"):
                (run_dir / name).unlink()
            _run(root, resume=True)
            resumed = episodes.read_text(encoding="utf-8").splitlines()
            ids = [json.loads(line)["episode_id"] for line in resumed]
            self.assertEqual(27, len(ids))
            self.assertEqual(27, len(set(ids)))

    def test_resume_rejects_manifest_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _run(root)
            manifest_path = root / "r1_05_calibration_run" / "run_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["stage"] = "tampered"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(ValueError):
                _run(root, resume=True)


if __name__ == "__main__":
    unittest.main()
