from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from skillstack.execution import RecordedActionExecutor, SkillPlanExecutor
from skillstack.library import load_static_library
from skillstack.retrieval import NoSkillRetriever, OracleSkillRetriever, RandomSkillRetriever
from skillstack.runner import EpisodeRunner
from skillstack.tracing import JsonlTraceWriter, status_counts

try:
    from tests.test_blm_r1_00_replay import TASK, create_environment
except ModuleNotFoundError:  # unittest discovery imports tests as top-level modules.
    from test_blm_r1_00_replay import TASK, create_environment


SCHEMA = "skillstack-blm-intervention-v1"


class SpySkillPlanExecutor(SkillPlanExecutor):
    """Keep the C1 identity while proving rejected requests never execute."""

    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    def execute(self, *args, **kwargs):
        self.calls += 1
        return super().execute(*args, **kwargs)


class R101BoundaryInstrumentationTests(unittest.TestCase):
    def _runner(self, retriever, executor=None):
        return EpisodeRunner(
            data_root=Path("."),
            native_skills=load_static_library(),
            retriever=retriever,
            executor=executor or SkillPlanExecutor(),
            environment_factory=create_environment,
        )

    def _run(self, retriever, request=None, executor=None):
        return self._runner(retriever, executor).run(
            TASK,
            top_k=1,
            max_steps=12,
            blm_intervention=request,
        )

    @staticmethod
    def _capture_request(arm_id):
        return {
            "schema_version": SCHEMA,
            "arm_id": arm_id,
            "operation": "capture",
            "atom": None,
            "expected_state_sha256": None,
            "donor": None,
        }

    @staticmethod
    def _donor(kind, state_sha256, retrieval_response, **overrides):
        donor = {
            "kind": kind,
            "task_id": TASK["task_id"],
            "task_family": TASK["task_family"],
            "state_sha256": state_sha256,
            "retrieval_response": copy.deepcopy(retrieval_response),
        }
        donor.update(overrides)
        return donor

    def _reference_capture(self):
        return self._run(
            OracleSkillRetriever(), self._capture_request("reference")
        )

    def _crossed_capture(self):
        return self._run(
            RandomSkillRetriever(seed=1), self._capture_request("crossed")
        )

    @staticmethod
    def _behavior(trace):
        report = trace.get("executor_report", {})
        return {
            "actions": trace.get("actions", []),
            "raw_observations": trace.get("raw_observations", []),
            "rewards": trace.get("rewards", []),
            "success": trace.get("success"),
            "stop_reason": trace.get("stop_reason"),
            "plan_skill_id": report.get("plan_skill_id"),
            "plan_steps": report.get("plan_steps"),
        }

    @staticmethod
    def _hash_json(value):
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def test_default_off_and_reference_capture_are_exact(self) -> None:
        baseline = self._run(OracleSkillRetriever())
        captured = self._reference_capture()

        self.assertNotIn("blm_boundary", baseline)
        self.assertEqual(self._behavior(baseline), self._behavior(captured))
        boundary = captured["blm_boundary"]
        self.assertEqual("skillstack-blm-boundary-v1", boundary["schema_version"])
        self.assertEqual("r1_00_c1_skillplan", boundary["boundary_id"])
        self.assertEqual("capture", boundary["validity_reason"])
        self.assertEqual("valid", boundary["validity"])
        self.assertFalse(boundary["changed"])
        self.assertEqual(
            boundary["original_input_sha256"], boundary["effective_input_sha256"]
        )
        self.assertEqual("skill_heat_then_place", boundary["consumer_branch"])
        self.assertTrue(boundary["outcome_observation"]["success"])

    def test_reference_capture_reconstructs_three_times(self) -> None:
        traces = [self._reference_capture() for _ in range(3)]
        projections = [
            (self._behavior(trace), trace["blm_boundary"])
            for trace in traces
        ]
        self.assertEqual(projections[0], projections[1])
        self.assertEqual(projections[0], projections[2])

    def test_crossed_noop_is_exact(self) -> None:
        crossed = self._run(RandomSkillRetriever(seed=1))
        captured = self._crossed_capture()
        boundary = captured["blm_boundary"]
        request = {
            "schema_version": SCHEMA,
            "arm_id": "crossed_noop",
            "operation": "copy_atom_from_donor",
            "atom": "selected_skill_ids[0]",
            "expected_state_sha256": boundary["state_sha256"],
            "donor": self._donor(
                "producer_output",
                boundary["state_sha256"],
                captured["retrieval_response"],
            ),
        }
        noop = self._run(RandomSkillRetriever(seed=1), request)

        self.assertEqual(self._behavior(crossed), self._behavior(noop))
        self.assertFalse(noop["blm_boundary"]["changed"])
        self.assertEqual(
            noop["blm_boundary"]["original_input_sha256"],
            noop["blm_boundary"]["effective_input_sha256"],
        )

    def test_identity_is_the_only_semantic_atom_restored(self) -> None:
        reference = self._reference_capture()
        crossed = self._run(RandomSkillRetriever(seed=1))
        state_sha256 = reference["blm_boundary"]["state_sha256"]
        request = {
            "schema_version": SCHEMA,
            "arm_id": "crossed_single_atom",
            "operation": "copy_atom_from_donor",
            "atom": "selected_skill_ids[0]",
            "expected_state_sha256": state_sha256,
            "donor": self._donor(
                "calibration_oracle",
                state_sha256,
                reference["retrieval_response"],
            ),
        }
        restored = self._run(RandomSkillRetriever(seed=1), request)

        self.assertTrue(restored["success"])
        self.assertEqual("environment_done", restored["stop_reason"])
        self.assertEqual("skill_heat_then_place", restored["selected_skill_ids"][0])
        self.assertEqual(
            crossed["retrieval_response"], restored["retrieval_response"]
        )
        self.assertEqual(
            crossed["selected_native_payloads"], restored["selected_native_payloads"]
        )
        self.assertEqual(self._behavior(reference), self._behavior(restored))
        self.assertTrue(restored["blm_boundary"]["changed"])
        self.assertTrue(restored["blm_boundary"]["donor_provenance"]["calibration_only"])

    def test_unread_atoms_are_negative_controls(self) -> None:
        reference = self._reference_capture()
        crossed = self._run(RandomSkillRetriever(seed=1))
        state_sha256 = reference["blm_boundary"]["state_sha256"]
        for atom in (
            "selected_scores[0]",
            "selected_native_skills[0]",
            "flat_skill_context",
        ):
            request = {
                "schema_version": SCHEMA,
                "arm_id": "irrelevant_unread_information",
                "operation": "copy_atom_from_donor",
                "atom": atom,
                "expected_state_sha256": state_sha256,
                "donor": self._donor(
                    "calibration_oracle",
                    state_sha256,
                    reference["retrieval_response"],
                ),
            }
            probe = self._run(RandomSkillRetriever(seed=1), request)
            self.assertEqual(self._behavior(crossed), self._behavior(probe), atom)
            self.assertTrue(probe["blm_boundary"]["changed"], atom)
            self.assertEqual("valid", probe["blm_boundary"]["validity"], atom)

    def test_invalid_requests_stop_before_consumer(self) -> None:
        reference = self._reference_capture()
        state_sha256 = reference["blm_boundary"]["state_sha256"]
        valid_donor = self._donor(
            "calibration_oracle", state_sha256, reference["retrieval_response"]
        )
        invalid_requests = (
            (
                "invalid_donor_task",
                dict(
                    schema_version=SCHEMA,
                    arm_id="crossed_single_atom",
                    operation="copy_atom_from_donor",
                    atom="selected_skill_ids[0]",
                    expected_state_sha256=state_sha256,
                    donor=dict(valid_donor, task_id="other-task"),
                ),
            ),
            (
                "invalid_donor_state",
                dict(
                    schema_version=SCHEMA,
                    arm_id="crossed_single_atom",
                    operation="copy_atom_from_donor",
                    atom="selected_skill_ids[0]",
                    expected_state_sha256="0" * 64,
                    donor=valid_donor,
                ),
            ),
            (
                "invalid_donor_payload",
                dict(
                    schema_version=SCHEMA,
                    arm_id="crossed_single_atom",
                    operation="copy_atom_from_donor",
                    atom="selected_skill_ids[0]",
                    expected_state_sha256=state_sha256,
                    donor=dict(
                        valid_donor,
                        retrieval_response=dict(
                            valid_donor["retrieval_response"],
                            ranked_candidates=[
                                dict(
                                    valid_donor["retrieval_response"]["ranked_candidates"][0],
                                    native_payload="tampered",
                                )
                            ],
                        ),
                    ),
                ),
            ),
            (
                "invalid_donor_score",
                dict(
                    schema_version=SCHEMA,
                    arm_id="irrelevant_unread_information",
                    operation="copy_atom_from_donor",
                    atom="selected_scores[0]",
                    expected_state_sha256=state_sha256,
                    donor=dict(
                        valid_donor,
                        retrieval_response=dict(
                            valid_donor["retrieval_response"],
                            ranked_candidates=[
                                dict(
                                    valid_donor["retrieval_response"]["ranked_candidates"][0],
                                    score="not-a-score",
                                )
                            ],
                        ),
                    ),
                ),
            ),
            (
                "forbidden_outcome_content",
                dict(
                    schema_version=SCHEMA,
                    arm_id="crossed_single_atom",
                    operation="copy_atom_from_donor",
                    atom="selected_skill_ids[0]",
                    expected_state_sha256=state_sha256,
                    donor=dict(
                        valid_donor,
                        retrieval_response=dict(
                            valid_donor["retrieval_response"],
                            raw_output=dict(
                                valid_donor["retrieval_response"]["raw_output"],
                                success=True,
                            ),
                        ),
                    ),
                ),
            ),
            (
                "invalid_atom_type",
                dict(
                    schema_version=SCHEMA,
                    arm_id="irrelevant_unread_information",
                    operation="copy_atom_from_donor",
                    atom=[],
                    expected_state_sha256=state_sha256,
                    donor=valid_donor,
                ),
            ),
            (
                "invalid_request_schema",
                dict(
                    schema_version=SCHEMA,
                    arm_id="crossed_single_atom",
                    operation="copy_atom_from_donor",
                    atom="selected_skill_ids[0]",
                    expected_state_sha256=state_sha256,
                    donor=valid_donor,
                    outcome_observation={"success": True},
                ),
            ),
        )
        for expected_reason, request in invalid_requests:
            executor = SpySkillPlanExecutor()
            trace = self._run(RandomSkillRetriever(seed=1), request, executor)
            self.assertEqual("invalid_input", trace["stop_reason"], expected_reason)
            self.assertEqual(expected_reason, trace["blm_boundary"]["validity_reason"])
            self.assertEqual(0, executor.calls, expected_reason)
            self.assertEqual([], trace["actions"], expected_reason)
            self.assertEqual(
                1, status_counts(trace)["invalid"], expected_reason
            )

    def test_empty_crossed_input_is_rejected_and_consumer_is_not_called(self) -> None:
        reference = self._reference_capture()
        state_sha256 = reference["blm_boundary"]["state_sha256"]
        request = {
            "schema_version": SCHEMA,
            "arm_id": "crossed_single_atom",
            "operation": "copy_atom_from_donor",
            "atom": "selected_skill_ids[0]",
            "expected_state_sha256": state_sha256,
            "donor": self._donor(
                "calibration_oracle",
                state_sha256,
                reference["retrieval_response"],
            ),
        }
        executor = SpySkillPlanExecutor()
        trace = self._run(NoSkillRetriever(), request, executor)
        self.assertEqual("invalid_input", trace["stop_reason"])
        self.assertEqual("invalid_list_alignment", trace["blm_boundary"]["validity_reason"])
        self.assertEqual(0, executor.calls)

    def test_non_skillplan_consumer_is_unsupported(self) -> None:
        request = self._capture_request("reference")
        trace = self._run(OracleSkillRetriever(), request, RecordedActionExecutor())
        self.assertEqual("invalid_input", trace["stop_reason"])
        self.assertEqual("unsupported_consumer", trace["blm_boundary"]["validity_reason"])
        self.assertIsNone(trace["blm_boundary"]["consumer_branch"])

    def test_state_hash_is_key_order_independent(self) -> None:
        first = self._reference_capture()
        second = self._reference_capture()
        self.assertEqual(
            first["blm_boundary"]["state_sha256"],
            second["blm_boundary"]["state_sha256"],
        )
        self.assertEqual(
            first["blm_boundary"]["original_input_sha256"],
            self._hash_json(
                {
                    "selected_skill_ids": ["skill_heat_then_place"],
                    "selected_scores": [1.0],
                    "selected_native_skills": first["selected_native_payloads"],
                    "flat_skill_context": (
                        "### Selected skill 1: skill_heat_then_place\n\n"
                        + first["selected_native_payloads"][0]
                    ),
                }
            ),
        )

    def test_invalid_trace_is_written_as_measurement_invalid(self) -> None:
        reference = self._reference_capture()
        state_sha256 = reference["blm_boundary"]["state_sha256"]
        request = {
            "schema_version": SCHEMA,
            "arm_id": "crossed_single_atom",
            "operation": "copy_atom_from_donor",
            "atom": "selected_skill_ids[0]",
            "expected_state_sha256": "0" * 64,
            "donor": self._donor(
                "calibration_oracle",
                state_sha256,
                reference["retrieval_response"],
            ),
        }
        trace = self._run(RandomSkillRetriever(seed=1), request)
        with tempfile.TemporaryDirectory() as directory:
            writer = JsonlTraceWriter(Path(directory), "r1_01", run_id="fixed-run")
            trace.update(
                {
                    "run_id": "fixed-run",
                    "episode_id": "episode-0",
                }
            )
            writer.append_episode(trace)
            self.assertEqual("invalid", trace["measurement_status"])
            self.assertIsNone(trace["task_success"])
            self.assertEqual(1, writer.recompute_status_counts()["invalid"])


if __name__ == "__main__":
    unittest.main()
