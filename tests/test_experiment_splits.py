from __future__ import annotations

import unittest

from skillstack.experiments.splits import (
    build_strict_disjoint_split,
    validate_disjoint_task_ids,
)


class StrictExperimentSplitTests(unittest.TestCase):
    def test_26_records_split_reproducibly_into_disjoint_13_and_13(self) -> None:
        records = [{"task_id": f"dev-{index:02d}", "payload": index} for index in range(26)]
        first = build_strict_disjoint_split(records, seed=2)
        second = build_strict_disjoint_split(records, seed=2)
        self.assertEqual(first, second)
        self.assertEqual("2:shuffle:0", first["source_shuffle_seed"])
        self.assertEqual(13, len(first["history_probe_source"]))
        self.assertEqual(13, len(first["proposal_source"]))
        self.assertFalse(
            set(first["history_probe_task_ids"]).intersection(first["proposal_task_ids"])
        )

    def test_overlap_and_duplicate_ids_fail_preflight(self) -> None:
        with self.assertRaisesRegex(ValueError, "overlap"):
            validate_disjoint_task_ids(["a", "b"], ["b", "c"])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validate_disjoint_task_ids(["a", "a"], ["b", "c"])

    def test_wrong_dev_record_count_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Expected 26"):
            build_strict_disjoint_split([{"task_id": "only-one"}])


if __name__ == "__main__":
    unittest.main()
