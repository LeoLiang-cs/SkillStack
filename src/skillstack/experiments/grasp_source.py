"""Read-only source checks and native repository smoke helpers for pinned GRASP."""

from __future__ import annotations

import hashlib
import importlib
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Mapping, Sequence

import yaml

from skillstack.experiments.splits import build_strict_disjoint_split


EXPECTED_GRASP_COMMIT = "9d7d125a3e9b46ed591692475eb07aff4ae67d34"
AGENTBENCH_RELATIVE = Path("benchmarks/AgentBench")
CONFIG_RELATIVE = Path("configs/grasp_alfworld.yaml")
TEST_SPLIT_RELATIVE = Path("data/alfworld/split_test.json")


def load_grasp_alfworld_manifest(
    grasp_root: Path, *, expected_commit: str = EXPECTED_GRASP_COMMIT
) -> Dict[str, Any]:
    """Load the released split files and materialize the strict epoch-0 13/13 split."""

    root = grasp_root.resolve()
    commit = _git_commit(root)
    if commit != expected_commit:
        raise ValueError(f"GRASP commit mismatch: expected {expected_commit}, received {commit}")

    agentbench = root / AGENTBENCH_RELATIVE
    config_path = agentbench / CONFIG_RELATIVE
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    cycle = config["cycle"]
    dev_path = agentbench / config["data"]["dev"]
    val_path = agentbench / config["data"]["val"]
    test_path = agentbench / TEST_SPLIT_RELATIVE
    dev = _load_json_list(dev_path, "dev")
    val = _load_json_list(val_path, "val")
    test = _load_json_list(test_path, "test")

    split_ids = {
        "dev": _unique_ids(dev, "dev"),
        "val": _unique_ids(val, "val"),
        "test": _unique_ids(test, "test"),
    }
    _ensure_partition_disjoint(split_ids)
    dev_records = [
        {
            "task_id": str(record["id"]),
            "description": record.get("description"),
            "task_type": record.get("type"),
            "native_record": deepcopy(record),
        }
        for record in dev
    ]
    strict_split = build_strict_disjoint_split(
        dev_records,
        seed=int(cycle["seed"]),
        epoch=0,
        history_size=13,
        proposal_size=13,
    )
    return {
        "grasp_root": str(root),
        "grasp_commit": commit,
        "config_path": str(config_path),
        "config_sha256": _file_hash(config_path),
        "split_paths": {"dev": str(dev_path), "val": str(val_path), "test": str(test_path)},
        "split_sha256": {
            "dev": _file_hash(dev_path),
            "val": _file_hash(val_path),
            "test": _file_hash(test_path),
        },
        "split_counts": {name: len(values) for name, values in (("dev", dev), ("val", val), ("test", test))},
        "all_partition_task_ids": split_ids,
        "strict_dev_split": strict_split,
        "val_test_access_in_component_split": False,
        "cycle_source_axes": {
            "seed": cycle["seed"],
            "max_proposals": cycle["max_proposals"],
            "max_learned_skills": cycle["max_learned_skills"],
            "update_every": cycle["update_every"],
        },
    }


def run_native_repository_smoke(
    grasp_root: Path,
    native_proposal: Mapping[str, Any],
    *,
    expected_commit: str = EXPECTED_GRASP_COMMIT,
) -> Dict[str, Any]:
    """Pass one handcrafted ADD through released validate/fork/apply/cleanup."""

    root = grasp_root.resolve()
    commit = _git_commit(root)
    if commit != expected_commit:
        raise ValueError(f"GRASP commit mismatch: expected {expected_commit}, received {commit}")
    agentbench = root / AGENTBENCH_RELATIVE
    config = yaml.safe_load((agentbench / CONFIG_RELATIVE).read_text(encoding="utf-8"))
    base_dir = agentbench / config["skills"]["base_dir"]

    sys.path.insert(0, str(agentbench))
    try:
        repository_module = importlib.import_module("src.skills.repository")
        updater_module = importlib.import_module("src.skills.updater")
        repository_type = repository_module.SkillRepository
        updater_type = updater_module.SkillUpdater
        import tempfile
        with tempfile.TemporaryDirectory(prefix="skillstack_grasp_smoke_") as directory:
            learned_dir = Path(directory) / "learned"
            repository = repository_type(base_dir=base_dir, learned_dir=learned_dir)
            updater = updater_type(
                agent=None,
                max_proposals=3,
                max_learned_skills=int(config["cycle"]["max_learned_skills"]),
            )
            original_snapshot = repository.snapshot()
            raw_native = deepcopy(dict(native_proposal))
            skillstack_provenance = raw_native.pop("_skillstack_provenance", {})
            validated = updater.validate([raw_native], repository)
            if len(validated) != 1:
                raise ValueError("Native GRASP validator rejected the handcrafted ADD")

            forked = repository.fork()
            fork_root = Path(getattr(forked, "_tmp_root"))
            try:
                winner = dict(validated[0])
                winner["_provenance"] = {
                    "source_smoke": True,
                    "skillstack": deepcopy(skillstack_provenance),
                }
                applied = updater.apply([winner], forked)
                fork_snapshot = forked.snapshot()
                learned_file = forked.learned_dir / f"{validated[0]['name']}.md"
                learned_file_text = learned_file.read_text(encoding="utf-8")
            finally:
                forked.cleanup()

            original_after = repository.snapshot()
            return {
                "grasp_commit": commit,
                "native_raw_proposal": deepcopy(dict(native_proposal)),
                "native_validated_proposals": deepcopy(validated),
                "native_applied_proposals": deepcopy(applied),
                "original_snapshot_before": original_snapshot,
                "original_snapshot_after": original_after,
                "fork_snapshot_after_apply": fork_snapshot,
                "learned_file_text": learned_file_text,
                "original_repository_unchanged": original_snapshot == original_after,
                "fork_cleaned_up": not fork_root.exists(),
                "boundary_success": (
                    original_snapshot == original_after
                    and not fork_root.exists()
                    and len(applied) == 1
                    and len(fork_snapshot) == 1
                ),
            }
    finally:
        if sys.path and sys.path[0] == str(agentbench):
            sys.path.pop(0)


def run_native_gate_scenario(
    grasp_root: Path,
    native_proposal: Mapping[str, Any],
    probe_reference: Mapping[str, bool],
    baseline_results: Mapping[str, Mapping[str, Any]],
    candidate_results: Mapping[str, Mapping[str, Any]],
    *,
    expected_commit: str = EXPECTED_GRASP_COMMIT,
) -> Dict[str, Any]:
    """Execute released GRASP baseline/candidate methods with deterministic rollouts."""

    root = grasp_root.resolve()
    commit = _git_commit(root)
    if commit != expected_commit:
        raise ValueError(f"GRASP commit mismatch: expected {expected_commit}, received {commit}")
    agentbench = root / AGENTBENCH_RELATIVE
    config = yaml.safe_load((agentbench / CONFIG_RELATIVE).read_text(encoding="utf-8"))
    sys.path.insert(0, str(agentbench))
    try:
        cycle_module = importlib.import_module("src.skills.cycle")
        repository_type = importlib.import_module("src.skills.repository").SkillRepository
        updater_type = importlib.import_module("src.skills.updater").SkillUpdater
        import tempfile
        with tempfile.TemporaryDirectory(prefix="skillstack_grasp_gate_") as directory:
            repository = repository_type(
                base_dir=agentbench / config["skills"]["base_dir"],
                learned_dir=Path(directory) / "learned",
            )
            updater = updater_type(
                agent=None,
                max_proposals=3,
                max_learned_skills=int(config["cycle"]["max_learned_skills"]),
            )
            raw_native = deepcopy(dict(native_proposal))
            raw_native.pop("_skillstack_provenance", None)
            validated = updater.validate([raw_native], repository)
            if len(validated) != 1:
                raise ValueError("Native GRASP validator rejected parity candidate")

            harness = SimpleNamespace()
            harness.skill_repo = repository
            harness.updater = updater
            harness.skill_aware_agent = SimpleNamespace(agent=None)
            harness.batch_concurrency = 1
            harness._progress = lambda iterable, **kwargs: iterable
            probe_set = [{"id": task_id, "description": task_id} for task_id in probe_reference]
            harness._id_to_index = {task_id: task_id for task_id in probe_reference}
            harness._eval_fn = None

            output_module = importlib.import_module("src.typings.output")
            status_module = importlib.import_module("src.typings.status")

            class DeterministicTaskClient:
                def run_sample(self, task_id: str, agent: Any):
                    is_candidate = (
                        hasattr(agent, "skill_repo")
                        and agent.skill_repo.learned_count() > 0
                    )
                    result = (
                        candidate_results if is_candidate else baseline_results
                    )[str(task_id)]
                    if result["status"] == "error":
                        return output_module.TaskClientOutput(error="FIXTURE_ERROR", output=None)
                    return output_module.TaskClientOutput(
                        output=output_module.TaskOutput(
                            status=status_module.SampleStatus(result["status"]),
                            result={"is_correct": result["success"]},
                            history=[],
                        )
                    )

            harness.task_client = DeterministicTaskClient()
            failing_ids = {task_id for task_id, was_failing in probe_reference.items() if was_failing}
            baseline_fixes, baseline_regressions, baseline_error_ids = (
                cycle_module.SkillCycleRunner._run_baseline_probe(
                    harness, probe_set, failing_ids
                )
            )
            raw_score, fixes, regressions, invalid_regr, _ = (
                cycle_module.SkillCycleRunner._eval_candidate(
                    harness,
                    validated[0],
                    probe_set,
                    failing_ids,
                    baseline_error_ids,
                )
            )
            penalty = cycle_module._INVALID_ACTION_REGRESSION_PENALTY
            adjusted = (
                (fixes - baseline_fixes)
                - (regressions - baseline_regressions)
                - (penalty - 1) * invalid_regr
            )
            admitted = adjusted > 0 and regressions <= baseline_regressions
            return {
                "grasp_commit": commit,
                "baseline_fixes": baseline_fixes,
                "baseline_regressions": baseline_regressions,
                "baseline_error_ids": sorted(baseline_error_ids),
                "fixes": fixes,
                "regressions": regressions,
                "invalid_action_regressions": invalid_regr,
                "invalid_action_regression_penalty": penalty,
                "raw_score": raw_score,
                "adjusted_score": adjusted,
                "decision": "accepted" if admitted else "no_op",
            }
    finally:
        if sys.path and sys.path[0] == str(agentbench):
            sys.path.pop(0)


def _load_json_list(path: Path, label: str) -> Sequence[Mapping[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"GRASP {label} split must be a JSON list")
    return payload


def _unique_ids(records: Sequence[Mapping[str, Any]], label: str) -> list:
    ids = [str(record["id"]) for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate task IDs in GRASP {label} split")
    return ids


def _ensure_partition_disjoint(split_ids: Mapping[str, Sequence[str]]) -> None:
    names = list(split_ids)
    for index, left in enumerate(names):
        for right in names[index + 1:]:
            overlap = sorted(set(split_ids[left]).intersection(split_ids[right]))
            if overlap:
                raise ValueError(f"GRASP {left}/{right} task-ID overlap: {', '.join(overlap)}")


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_commit(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()
