from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from skillstack.cli import main
from skillstack.preflight import (
    REQUIRED_CONFIG_MARKERS,
    REQUIRED_DIRECTORIES,
    REQUIRED_FILES,
    evaluate_preflight,
)


class PreflightTests(unittest.TestCase):
    def test_repository_preflight_passes(self) -> None:
        root = Path(__file__).resolve().parents[1]
        result = evaluate_preflight(root)
        self.assertEqual("pass", result["status"])
        self.assertEqual(0, result["network_calls"])
        self.assertEqual(0, result["model_calls"])

    def test_missing_repository_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = evaluate_preflight(Path(directory))
        self.assertEqual("fail", result["status"])
        self.assertEqual(
            len(REQUIRED_DIRECTORIES) + len(REQUIRED_FILES), len(result["missing"])
        )
        self.assertEqual(list(REQUIRED_CONFIG_MARKERS), result["missing_configuration_markers"])
        self.assertFalse(result["repository_marker_present"])
        self.assertIn("repo-only", result["diagnostic"])

    def test_cli_preflight_uses_explicit_root(self) -> None:
        root = Path(__file__).resolve().parents[1]
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["preflight", "--root", str(root)])
        self.assertEqual(0, exit_code)
        self.assertIn('"status": "pass"', output.getvalue())


if __name__ == "__main__":
    unittest.main()
