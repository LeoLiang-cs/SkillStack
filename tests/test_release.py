from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from skillstack.cli import build_parser
from skillstack.release import collect_release_files, copy_release_snapshot, release_metadata


class ReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]

    def test_release_metadata_preserves_license_gate(self) -> None:
        metadata = release_metadata(self.root)
        expected_status = "pass" if metadata["license_present"] else "fail"
        self.assertEqual(expected_status, metadata["status"])
        self.assertEqual([], metadata["held_files_selected"])
        self.assertEqual("v0.1.0-alpha", metadata["target_tag"])
        self.assertEqual("0.1.0a0", metadata["package_version"])

    def test_snapshot_excludes_held_and_untracked_research(self) -> None:
        paths = {
            path.relative_to(self.root).as_posix()
            for path in collect_release_files(self.root)
        }
        self.assertIn("README.md", paths)
        self.assertIn("data/.gitkeep", paths)
        self.assertIn("runs/.gitkeep", paths)
        self.assertIn(".agents/skills/weekly-lab-update/SKILL.md", paths)
        self.assertFalse(any(path.startswith("docs/final_cards/") for path in paths))
        self.assertFalse(any(path.startswith(".agents/skills/idea-spark/") for path in paths))
        self.assertFalse(any(path.startswith("papers/") for path in paths))
        self.assertFalse(any(path.startswith("ideaspark_run/") for path in paths))
        self.assertFalse(any(Path(path).name == ".DS_Store" for path in paths))

    def test_snapshot_copy_has_no_held_cards(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            count = copy_release_snapshot(self.root, Path(directory))
            self.assertGreater(count, 0)
            self.assertTrue((Path(directory) / "pyproject.toml").is_file())
            self.assertFalse((Path(directory) / "docs" / "final_cards").exists())

    def test_fidelity_register_uses_declared_labels(self) -> None:
        register = yaml.safe_load(
            (self.root / "configs" / "component_fidelity.yaml").read_text(encoding="utf-8")
        )
        labels = set(register["labels"])
        for component in register["components"].values():
            self.assertIn(component["fidelity"], labels)

    def test_cli_exposes_release_check(self) -> None:
        args = build_parser().parse_args(["release-check", "--allow-license-pending"])
        self.assertEqual("release-check", args.command)
        self.assertTrue(args.allow_license_pending)


if __name__ == "__main__":
    unittest.main()
