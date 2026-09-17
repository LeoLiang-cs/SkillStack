from __future__ import annotations

import copy
import unittest
from pathlib import Path

from skillstack.execution import SkillPlanExecutor
from skillstack.library import load_static_library
from skillstack.retrieval import NoSkillRetriever
from skillstack.runner import EpisodeRunner
from skillstack.experiments.blm_calibration import (
    TASK,
    build_atom_census,
    create_environment,
    run_v2_calibration_arm,
    validate_atom_census,
)


class R103BoundaryAtomCensusTests(unittest.TestCase):
    def test_runtime_tracker_matches_static_consumer_reads(self) -> None:
        traces = [run_v2_calibration_arm("reference") for _ in range(3)]
        events = [trace["blm_boundary"]["consumer_reads"] for trace in traces]
        self.assertEqual(events[0], events[1])
        self.assertEqual(events[0], events[2])
        self.assertEqual(
            [event["path"] for event in events[0]],
            [
                "selected_skill_ids",
                "selected_scores",
                "selected_native_skills",
                "flat_skill_context",
                "selected_skill_ids",
                "selected_skill_ids[0]",
            ],
        )
        self.assertEqual(
            [event["read_type"] for event in events[0]],
            [
                "schema_validation_read",
                "schema_validation_read",
                "schema_validation_read",
                "schema_validation_read",
                "schema_validation_read",
                "semantic_read",
            ],
        )

    def test_only_identity_has_runtime_semantic_index_read(self) -> None:
        census = build_atom_census(run_v2_calibration_arm("reference"))
        records = {record["atom_id"]: record for record in census["records"]}
        self.assertEqual(
            [event["path"] for event in records["selected_skill_ids[0]"]["runtime_access"]],
            ["selected_skill_ids", "selected_skill_ids", "selected_skill_ids[0]"],
        )
        for atom in ("selected_scores[0]", "selected_native_skills[0]", "flat_skill_context"):
            self.assertTrue(
                all(event["read_type"] == "schema_validation_read"
                    for event in records[atom]["runtime_access"]),
                atom,
            )
            self.assertNotIn("semantic_read", [event["read_type"] for event in records[atom]["runtime_access"]])
        self.assertEqual(
            records["consumer_local_registry"]["runtime_access"]["status"],
            "static_verified_runtime_indirect",
        )

    def test_v2_wrapper_is_behavior_exact_and_default_off_is_unchanged(self) -> None:
        baseline = EpisodeRunner(
            Path("."), load_static_library(), NoSkillRetriever(), SkillPlanExecutor(),
            environment_factory=create_environment,
        ).run(TASK, top_k=1, max_steps=12)
        instrumented = EpisodeRunner(
            Path("."), load_static_library(), NoSkillRetriever(), SkillPlanExecutor(),
            environment_factory=create_environment,
        ).run(
            TASK,
            top_k=1,
            max_steps=12,
            blm_intervention={
                "schema_version": "skillstack-blm-intervention-v2",
                "arm_id": "crossed",
                "operation": "capture",
                "atom": None,
                "expected_state_sha256": None,
                "donor": None,
            },
        )
        for key in ("actions", "raw_observations", "rewards", "success", "stop_reason"):
            self.assertEqual(baseline[key], instrumented[key], key)
        self.assertNotIn("blm_boundary", baseline)
        self.assertEqual("valid", instrumented["blm_boundary"]["validity"])

    def test_top_k_two_records_only_index_zero(self) -> None:
        trace = run_v2_calibration_arm("crossed", top_k=2)
        semantic = [
            event for event in trace["blm_boundary"]["consumer_reads"]
            if event["read_type"] == "semantic_read"
        ]
        self.assertEqual([event["path"] for event in semantic], ["selected_skill_ids[0]"])

    def test_empty_identity_does_not_fabricate_index_read(self) -> None:
        trace = EpisodeRunner(
            Path("."), load_static_library(), NoSkillRetriever(), SkillPlanExecutor(),
            environment_factory=create_environment,
        ).run(
            TASK,
            top_k=1,
            max_steps=12,
            blm_intervention={
                "schema_version": "skillstack-blm-intervention-v2",
                "arm_id": "crossed",
                "operation": "capture",
                "atom": None,
                "expected_state_sha256": None,
                "donor": None,
            },
        )
        self.assertEqual(
            [],
            [event for event in trace["blm_boundary"]["consumer_reads"]
             if event["path"] == "selected_skill_ids[0]"],
        )

    def test_census_rejects_unknown_duplicate_or_missing_read_map(self) -> None:
        census = build_atom_census(run_v2_calibration_arm("reference"))
        unknown = copy.deepcopy(census)
        unknown["records"][0]["atom_id"] = "unknown"
        with self.assertRaisesRegex(ValueError, "atom_census_atom_ids"):
            validate_atom_census(unknown)
        duplicate = copy.deepcopy(census)
        duplicate["records"][1]["atom_id"] = duplicate["records"][0]["atom_id"]
        with self.assertRaisesRegex(ValueError, "atom_census_atom_ids"):
            validate_atom_census(duplicate)
        missing_map = copy.deepcopy(census)
        missing_map["records"][0]["read_map_id"] = None
        with self.assertRaisesRegex(ValueError, "atom_census_read_map_id"):
            validate_atom_census(missing_map)


if __name__ == "__main__":
    unittest.main()
