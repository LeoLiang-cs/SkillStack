from __future__ import annotations

import unittest

from skillstack.library import load_static_library
from skillstack.retrieval import TaskSemanticRetriever
from skillstack.tasks import load_p0_tasks, load_task_manifest
from skillstack.task_semantics import parse_task_semantics


class TaskSemanticRetrieverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.library = load_static_library()
        self.retriever = TaskSemanticRetriever()

    def test_ranks_expected_skill_first_on_all_frozen_tasks(self) -> None:
        for task in load_p0_tasks():
            with self.subTest(task=task["task_family"]):
                response = self.retriever.retrieve(task, "raw observation text", self.library, top_k=2)
                selected = [c["skill_id"] for c in response["ranked_candidates"]]
                self.assertEqual(task["expected_skill_id"], selected[0], task["task_family"])

    def test_ranks_expected_skill_first_on_picktwo(self) -> None:
        manifest = load_task_manifest()
        picktwo_tasks = [t for t in load_task_manifest() if t["task_family"] == "pick_two_obj_and_place"]
        if not picktwo_tasks:
            self.skipTest("no pick_two tasks in default manifest")
        for task in picktwo_tasks:
            response = self.retriever.retrieve(task, "raw observation text", self.library, top_k=2)
            self.assertEqual("skill_pick_two_then_place", response["ranked_candidates"][0]["skill_id"])

    def test_raw_output_records_extracted_semantics(self) -> None:
        task = load_p0_tasks()[3]  # heat task
        response = self.retriever.retrieve(task, "raw observation text", self.library, top_k=2)
        semantics = response["raw_output"]["extracted_semantics"]
        self.assertEqual("heat_then_place", semantics["goal_operation"])
        self.assertEqual("heat", semantics["required_transformation"])
        self.assertIn("scores_by_skill_id", response["raw_output"])
        self.assertIn("breakdown_by_skill_id", response["raw_output"])

    def test_heat_task_resolves_week1_f02(self) -> None:
        # F-02: lexical picked cooling for the heat task. R1 must pick heating.
        heat_task = next(t for t in load_p0_tasks() if t["task_family"] == "pick_heat_then_place_in_recep")
        response = self.retriever.retrieve(heat_task, "raw observation text", self.library, top_k=1)
        self.assertEqual("skill_heat_then_place", response["ranked_candidates"][0]["skill_id"])


class TaskSemanticsParseTests(unittest.TestCase):
    def test_pick_two_object_parse(self) -> None:
        semantics = parse_task_semantics(
            {"task_family": "pick_two_obj_and_place", "task_instruction": "ignored"},
            "Your task is to: put two shakers in a drawer.",
        )
        self.assertEqual("place_two", semantics["goal_operation"])
        self.assertEqual("shaker", semantics["object"])
        self.assertEqual("drawer", semantics["destination"])


if __name__ == "__main__":
    unittest.main()
