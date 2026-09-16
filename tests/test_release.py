from __future__ import annotations

import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

import yaml

from skillstack.cli import build_parser
from skillstack.release import (
    ReleaseError,
    collect_release_files,
    copy_release_snapshot,
    release_manifest,
    release_metadata,
)


FIXTURE_POLICY = textwrap.dedent(
    """
    schema_version: 1
    public:
      - README.md
      - LICENSE
      - pyproject.toml
      - configs/**
      - src/**
      - tests/**
    held_research:
      - held/**
    external_data:
      - data/**
    generated:
      - generated/**
    required:
      - LICENSE
      - README.md
      - pyproject.toml
      - configs/public_release_scope.yaml
      - src/skillstack/__init__.py
      - tests/test_release.py
    """
).strip()


class ReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]

    def _make_repo(self, directory: str, policy: str = FIXTURE_POLICY) -> tuple[Path, str]:
        root = Path(directory)
        files = {
            "README.md": "public readme\n",
            "LICENSE": "MIT\n",
            "pyproject.toml": "[project]\nname = 'fixture'\nversion = '0'\n",
            "configs/public_release_scope.yaml": policy + "\n",
            "src/skillstack/__init__.py": "__version__ = '0'\n",
            "tests/test_release.py": "# fixture test\n",
            "held/research.md": "private\n",
            "data/external.bin": "external\n",
            "generated/output.json": "generated\n",
        }
        for relative, content in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Release Test"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "release-test@example.invalid"], cwd=root, check=True)
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=root, check=True)
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        return root, commit

    def test_release_metadata_has_commit_and_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, commit = self._make_repo(directory)
            metadata = release_metadata(root, ref=commit)
            self.assertEqual("pass", metadata["status"])
            self.assertEqual(commit, metadata["resolved_commit"])
            self.assertTrue(metadata["content_sha256"])
            self.assertTrue(metadata["manifest_sha256"])
            self.assertEqual([], metadata["held_files_selected"])

    def test_untracked_file_does_not_change_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, commit = self._make_repo(directory)
            before = release_manifest(root, ref=commit)
            (root / "src" / "untracked_research.md").write_text("private\n", encoding="utf-8")
            after = release_manifest(root, ref=commit)
            self.assertEqual(before["content_sha256"], after["content_sha256"])
            self.assertEqual(before["files"], after["files"])
            self.assertNotIn("src/untracked_research.md", {item["path"] for item in after["files"]})

    def test_held_external_and_generated_files_are_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, commit = self._make_repo(directory)
            manifest = release_manifest(root, ref=commit)
            self.assertIn("held/research.md", manifest["categories"]["held_research"]["paths"])
            self.assertIn("data/external.bin", manifest["categories"]["external_data"]["paths"])
            self.assertIn("generated/output.json", manifest["categories"]["generated"]["paths"])
            self.assertNotIn("held/research.md", {item["path"] for item in manifest["files"]})

    def test_worktree_modification_does_not_pollute_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, commit = self._make_repo(directory)
            (root / "README.md").write_text("dirty worktree\n", encoding="utf-8")
            with tempfile.TemporaryDirectory() as destination:
                copy_release_snapshot(root, Path(destination), ref=commit)
                self.assertEqual("public readme\n", (Path(destination) / "README.md").read_text())

    def test_symlink_in_public_scope_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, _commit = self._make_repo(directory)
            target = root / "outside.txt"
            target.write_text("outside\n", encoding="utf-8")
            os.symlink(target, root / "src" / "external_link.txt")
            subprocess.run(["git", "add", "-A"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "symlink"], cwd=root, check=True)
            metadata = release_metadata(root)
            self.assertEqual("fail", metadata["status"])
            self.assertIn("unsupported file modes", metadata["error"])

    def test_policy_path_traversal_fails_closed(self) -> None:
        policy = FIXTURE_POLICY.replace("- README.md", "- ../secret\n      - README.md", 1)
        with tempfile.TemporaryDirectory() as directory:
            root, _commit = self._make_repo(directory, policy=policy)
            with self.assertRaises(ReleaseError):
                release_manifest(root)

    def test_snapshot_copy_has_only_selected_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, commit = self._make_repo(directory)
            with tempfile.TemporaryDirectory() as destination:
                count = copy_release_snapshot(root, Path(destination), ref=commit)
                self.assertGreater(count, 0)
                self.assertTrue((Path(destination) / "pyproject.toml").is_file())
                self.assertFalse((Path(destination) / "held").exists())

    def test_fidelity_register_uses_declared_labels(self) -> None:
        register = yaml.safe_load(
            (self.root / "configs" / "component_fidelity.yaml").read_text(encoding="utf-8")
        )
        labels = set(register["labels"])
        for component in register["components"].values():
            self.assertIn(component["fidelity"], labels)

    def test_cli_exposes_commit_ref(self) -> None:
        args = build_parser().parse_args(["release-check", "--ref", "abc123", "--allow-license-pending"])
        self.assertEqual("release-check", args.command)
        self.assertEqual("abc123", args.ref)
        self.assertTrue(args.allow_license_pending)


if __name__ == "__main__":
    unittest.main()
