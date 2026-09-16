from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from skillstack.quality import check_text, inspect_repository


class PublicRepositoryQualityTests(unittest.TestCase):
    def test_current_repository_passes(self) -> None:
        root = Path(__file__).resolve().parents[1]
        result = inspect_repository(root)
        self.assertEqual([], result["findings"])
        self.assertEqual("pass", result["status"])
        self.assertEqual(0, result["network_calls"])
        self.assertEqual(0, result["model_calls"])

    def test_detects_private_path_and_secret(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / ".env.example"
            private_path = "/" + "Users/example/private/file"
            secret_assignment = "API_" + "KEY=abcdefghijklmnop"
            text = f"{private_path}\n{secret_assignment}\n"
            findings = check_text(path, text, root)
        self.assertEqual(
            {"credential_like_value", "private_absolute_path"},
            {finding["kind"] for finding in findings},
        )

    def test_repo_only_scan_rejects_non_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = inspect_repository(Path(directory))
        self.assertEqual("fail", result["status"])
        self.assertEqual("repo_only_command_requires_checkout", result["findings"][0]["kind"])

    def test_detects_broken_relative_markdown_link(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "README.md"
            findings = check_text(path, "[missing](docs/missing.md)\n", root)
        self.assertEqual("broken_local_markdown_link", findings[0]["kind"])

    def test_accepts_existing_relative_markdown_link(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "docs" / "present.md"
            target.parent.mkdir()
            target.write_text("ok\n", encoding="utf-8")
            path = root / "README.md"
            findings = check_text(path, "[present](docs/present.md)\n", root)
        self.assertEqual([], findings)


if __name__ == "__main__":
    unittest.main()
