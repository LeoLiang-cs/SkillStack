from __future__ import annotations

import io
import os
import importlib.resources as package_resources
import json
import tempfile
import urllib.error
import unittest
from pathlib import Path
from unittest import mock

from skillstack.llm import (
    BackendConfig,
    BudgetExceededError,
    LlmClient,
    LlmError,
    load_backend,
    load_backends,
    load_env_file,
)
from skillstack.llm.client import _cached_prompt_tokens, _redact_sensitive_text


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
        self.assertIn("asu_glm_5_2", backends)
        self.assertIn("asu_qwen3_235b_thinking_2507", backends)
        self.assertIn("zhipu_glm_flashx", backends)
        self.assertIn("deepseek_v4_flash", backends)
        asu = backends["asu_glm_5_2"]
        self.assertEqual("https://openai.rc.asu.edu/v1/chat/completions", asu.base_url)
        self.assertEqual("glm-5-2", asu.model)
        self.assertEqual("ASU_API_KEY", asu.api_key_env)
        self.assertFalse(asu.thinking_disabled)
        asu_qwen = backends["asu_qwen3_235b_thinking_2507"]
        self.assertEqual("qwen3-235b-a22b-thinking-2507", asu_qwen.model)
        self.assertEqual("ASU_API_KEY", asu_qwen.api_key_env)
        self.assertFalse(asu_qwen.thinking_disabled)
        glm = backends["zhipu_glm_flashx"]
        self.assertEqual("glm-4.7-flashx", glm.model)
        self.assertTrue(glm.thinking_disabled)
        deepseek = backends["deepseek_v4_flash"]
        self.assertEqual("deepseek-v4-flash", deepseek.model)
        self.assertGreater(deepseek.prices["output"], 0)

    def test_explicit_config_path_takes_precedence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "backends.json"
            path.write_text(
                '{"backends": {"local": {"base_url": "http://x", '
                '"model": "m", "api_key_env": "K"}}, "defaults": {}}',
                encoding="utf-8",
            )
            self.assertEqual(["local"], sorted(load_backends(path)))

    def test_environment_config_path_overrides_checkout_default(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "backends.json"
            path.write_text(
                '{"backends": {"env": {"base_url": "http://x", '
                '"model": "m", "api_key_env": "K"}}, "defaults": {}}',
                encoding="utf-8",
            )
            with mock.patch.dict(os.environ, {"SKILLSTACK_LLM_CONFIG": str(path)}):
                self.assertEqual(["env"], sorted(load_backends()))

    def test_user_config_overrides_checkout_default(self):
        with tempfile.TemporaryDirectory() as directory:
            config_home = Path(directory) / "config"
            path = config_home / "skillstack" / "llm_backends.json"
            path.parent.mkdir(parents=True)
            path.write_text(
                '{"backends": {"user": {"base_url": "http://x", '
                '"model": "m", "api_key_env": "K"}}, "defaults": {}}',
                encoding="utf-8",
            )
            with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": str(config_home)}):
                self.assertEqual(["user"], sorted(load_backends()))

    def test_package_defaults_are_available_without_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing" / "llm_backends.json"
            with mock.patch("skillstack.llm.client.BACKENDS_PATH", missing):
                self.assertIn("asu_glm_5_2", load_backends())

    def test_packaged_and_checkout_backend_metadata_match(self):
        checkout = json.loads(
            (Path(__file__).resolve().parents[1] / "configs" / "llm_backends.json").read_text(
                encoding="utf-8"
            )
        )
        packaged = json.loads(
            package_resources.files("skillstack.resources")
            .joinpath("config/llm_backends.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(checkout["backends"], packaged["backends"])
        self.assertEqual(checkout["defaults"], packaged["defaults"])

    def test_invalid_config_fails_before_provider_call(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "backends.json"
            path.write_text(
                '{"backends": {"broken": {"base_url": "file:///tmp/x", '
                '"model": "m", "api_key_env": "K"}}, "defaults": {}}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "base_url must use http"):
                load_backends(path)

    def test_malformed_json_has_stable_diagnostic(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "backends.json"
            path.write_text('{"backends": ', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "JSON line 1"):
                load_backends(path)

    def test_unknown_backend_fails_before_client_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "backends.json"
            path.write_text(
                '{"backends": {"known": {"base_url": "http://x", '
                '"model": "m", "api_key_env": "K"}}, "defaults": {}}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "Unknown LLM backend 'missing'"):
                load_backend("missing", path)

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


class RetryAndBudgetTests(unittest.TestCase):
    def _backend(self, **defaults):
        return BackendConfig(
            "test",
            {"base_url": "http://x", "model": "m", "api_key_env": "K"},
            {"max_retries_per_call": 2, "retry_backoff_seconds": 0, **defaults},
        )

    def test_retries_transient_http_error_then_returns(self):
        backend = self._backend()
        client = LlmClient(backend, api_key="dummy")
        transient = urllib.error.HTTPError(
            "http://x", 503, "unavailable", {}, io.BytesIO(b"temporary")
        )
        with mock.patch.object(
            client,
            "_post",
            side_effect=[
                transient,
                {"choices": [{"message": {"content": "ok"}}], "usage": {}},
            ],
        ) as post:
            self.assertEqual("ok", client.chat([])["content"])
            self.assertEqual(2, post.call_count)

    def test_does_not_retry_configuration_http_error(self):
        backend = self._backend()
        client = LlmClient(backend, api_key="dummy")
        error = urllib.error.HTTPError(
            "http://x", 401, "unauthorized", {}, io.BytesIO(b"bad key")
        )
        with mock.patch.object(client, "_post", side_effect=error) as post:
            with self.assertRaises(LlmError):
                client.chat([])
            self.assertEqual(1, post.call_count)

    def test_run_call_budget_blocks_the_next_request(self):
        backend = self._backend(max_calls_per_run=1)
        client = LlmClient(backend, api_key="dummy")
        response = {"choices": [{"message": {"content": "ok"}}], "usage": {}}
        with mock.patch.object(client, "_post", return_value=response):
            client.chat([])
            with self.assertRaises(BudgetExceededError):
                client.chat([])
        self.assertEqual(1, client.budget.snapshot()["calls"])

    def test_token_budget_preserves_usage_before_failure(self):
        backend = self._backend(max_completion_tokens_per_run=1)
        client = LlmClient(backend, api_key="dummy")
        response = {
            "choices": [{"message": {"content": "too much"}}],
            "usage": {"completion_tokens": 2},
        }
        with mock.patch.object(client, "_post", return_value=response):
            with self.assertRaises(BudgetExceededError):
                client.chat([])
        snapshot = client.budget.snapshot()
        self.assertEqual(2, snapshot["completion_tokens"])


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


class ErrorRedactionTests(unittest.TestCase):
    def test_redacts_bearer_and_key_like_values(self):
        bearer = "secret-" + "token"
        api_key_like = "sk-" + "abcdefghijklmnop"
        detail = _redact_sensitive_text(
            "authorization: Bearer " + bearer + " api_key=" + api_key_like + " cookie=session-secret"
        )
        self.assertNotIn(bearer, detail)
        self.assertNotIn(api_key_like, detail)
        self.assertNotIn("session-secret", detail)
        self.assertIn("[REDACTED]", detail)


if __name__ == "__main__":
    unittest.main()
