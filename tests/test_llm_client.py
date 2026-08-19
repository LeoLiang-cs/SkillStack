from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from skillstack.llm import BackendConfig, LlmClient, LlmError, load_backends, load_env_file
from skillstack.llm.client import _cached_prompt_tokens


class CachedTokenTests(unittest.TestCase):
    def test_flat_key(self):
        self.assertEqual(7, _cached_prompt_tokens({"prompt_cache_hit_tokens": 7}))

    def test_nested_details_key(self):
        self.assertEqual(3, _cached_prompt_tokens({"prompt_tokens_details": {"cached_tokens": 3}}))

    def test_missing(self):
        self.assertEqual(0, _cached_prompt_tokens({"prompt_tokens": 5}))


class ParseResponseTests(unittest.TestCase):
    def test_parses_content_and_usage(self):
        result = LlmClient._parse_response(
            {
                "choices": [{"message": {"content": "hello"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 4},
            },
            0.5,
        )
        self.assertEqual("hello", result["content"])
        self.assertEqual(10, result["usage"]["prompt_tokens"])
        self.assertEqual(0.5, result["latency_seconds"])

    def test_malformed_body_raises(self):
        with self.assertRaises(LlmError):
            LlmClient._parse_response({}, 0.1)


class BackendConfigTests(unittest.TestCase):
    def test_load_backends_from_repo_config(self):
        backends = load_backends()
        self.assertIn("zhipu_glm_flashx", backends)
        self.assertIn("deepseek_v4_flash", backends)
        glm = backends["zhipu_glm_flashx"]
        self.assertEqual("glm-4.7-flashx", glm.model)
        self.assertTrue(glm.thinking_disabled)
        deepseek = backends["deepseek_v4_flash"]
        self.assertEqual("deepseek-v4-flash", deepseek.model)
        self.assertGreater(deepseek.prices["output"], 0)

    def test_missing_key_raises_clear_error(self):
        backend = BackendConfig(
            "test",
            {"base_url": "http://x", "model": "m", "api_key_env": "NO_SUCH_KEY_ENV"},
            {},
        )
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("NO_SUCH_KEY_ENV", None)
            with self.assertRaises(LlmError):
                backend.resolve_api_key()


class CostEstimateTests(unittest.TestCase):
    def test_mixes_cached_and_uncached_input(self):
        backend = BackendConfig(
            "test",
            {
                "base_url": "http://x",
                "model": "m",
                "api_key_env": "K",
                "prices_usd_per_1m": {"input": 0.10, "cached_input": 0.02, "output": 0.40},
            },
            {},
        )
        client = LlmClient(backend, api_key="dummy")
        # 1000 prompt tokens, 300 cached, 200 completion tokens.
        cost = client.estimate_cost_usd(
            {"prompt_tokens": 1000, "completion_tokens": 200, "cached_prompt_tokens": 300}
        )
        expected = 700 * 0.10 / 1e6 + 300 * 0.02 / 1e6 + 200 * 0.40 / 1e6
        self.assertAlmostEqual(expected, cost, places=9)


class EnvFileTests(unittest.TestCase):
    def test_load_env_file_never_overrides(self):
        with tempfile.TemporaryDirectory() as directory:
            env_path = Path(directory) / ".env"
            env_path.write_text("SK_TEST_KEY=secret-value\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {"SK_TEST_KEY": "already-set"}):
                load_env_file(env_path)
                self.assertEqual("already-set", os.environ["SK_TEST_KEY"])
            os.environ.pop("SK_TEST_KEY", None)
            load_env_file(env_path)
            self.assertEqual("secret-value", os.environ["SK_TEST_KEY"])
            os.environ.pop("SK_TEST_KEY", None)


if __name__ == "__main__":
    unittest.main()
