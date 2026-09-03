"""Minimal zero-dependency OpenAI-compatible LLM client for executor backends.

Reads backend definitions from `configs/llm_backends.json` and API keys from
environment variables (populated from the git-ignored `.env`). Every call
reports usage and latency so episode traces can estimate cost.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
BACKENDS_PATH = REPOSITORY_ROOT / "configs" / "llm_backends.json"


class LlmError(RuntimeError):
    """Raised when a backend call fails after retries."""


class BackendConfig:
    """One configured backend: endpoint, model id, prices, request defaults."""

    def __init__(self, name: str, definition: Dict[str, Any], defaults: Dict[str, Any]) -> None:
        self.name = name
        self.label = definition.get("label", name)
        self.base_url = definition["base_url"]
        self.model = definition["model"]
        self.api_key_env = definition["api_key_env"]
        self.thinking_disabled = bool(definition.get("thinking_disabled", False))
        self.prices = definition.get("prices_usd_per_1m", {})
        self.defaults = dict(defaults)

    def resolve_api_key(self) -> str:
        api_key = os.environ.get(self.api_key_env)
        if not api_key:
            raise LlmError(
                f"Missing API key for backend {self.name!r}: set {self.api_key_env} "
                "(e.g. via the git-ignored .env file)."
            )
        return api_key


class LlmClient:
    """OpenAI-compatible chat completion client with retries and accounting."""

    def __init__(
        self,
        backend: BackendConfig,
        api_key: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ) -> None:
        self.backend = backend
        self.api_key = api_key or backend.resolve_api_key()
        self.timeout_seconds = timeout_seconds or float(backend.defaults.get("request_timeout_seconds", 120))
        self.max_retries = int(backend.defaults.get("max_retries_per_call", 3))
        self.backoff_seconds = float(backend.defaults.get("retry_backoff_seconds", 2.0))

    def chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Send one chat completion and retain content or native tool calls."""

        max_tokens = max_tokens if max_tokens is not None else int(self.backend.defaults.get("max_tokens_per_step", 512))
        temperature = temperature if temperature is not None else float(self.backend.defaults.get("temperature", 0))
        payload: Dict[str, Any] = {
            "model": self.backend.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if self.backend.thinking_disabled:
            payload["thinking"] = {"type": "disabled"}
        if tools:
            payload["tools"] = tools

        for attempt in range(1, self.max_retries + 1):
            started = time.monotonic()
            try:
                body = self._post(payload)
                latency_seconds = time.monotonic() - started
                return self._parse_response(body, latency_seconds)
            except urllib.error.HTTPError as error:
                detail = _safe_error_detail(error)
                if error.code in (408, 429) or 500 <= error.code < 600:
                    if attempt < self.max_retries:
                        time.sleep(self.backoff_seconds * (2 ** (attempt - 1)))
                        continue
                raise LlmError(
                    f"{self.backend.name} call failed after {attempt} attempt(s): "
                    f"HTTP {error.code} {detail}"
                ) from error
            except (urllib.error.URLError, TimeoutError, OSError) as error:
                if attempt < self.max_retries:
                    time.sleep(self.backoff_seconds * (2 ** (attempt - 1)))
                    continue
                raise LlmError(f"{self.backend.name} call failed after {attempt} attempt(s): {error}") from error
        raise LlmError("Unreachable retry loop exit")

    def estimate_cost_usd(self, usage: Dict[str, Any]) -> float:
        """Estimate one call's cost from the recorded price table."""

        prices = self.backend.prices
        prompt_tokens = int(usage.get("prompt_tokens", 0))
        completion_tokens = int(usage.get("completion_tokens", 0))
        cached = int(usage.get("cached_prompt_tokens", 0))
        input_price = float(prices.get("input", 0.0)) / 1_000_000
        cached_price = float(prices.get("cached_input", input_price)) / 1_000_000
        output_price = float(prices.get("output", 0.0)) / 1_000_000
        uncached = max(prompt_tokens - cached, 0)
        return uncached * input_price + cached * cached_price + completion_tokens * output_price

    def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        request = urllib.request.Request(
            self.backend.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _parse_response(body: Dict[str, Any], latency_seconds: float) -> Dict[str, Any]:
        try:
            native_message = body["choices"][0]["message"]
            content = native_message.get("content") or ""
            tool_calls = native_message.get("tool_calls") or []
            if not content and not tool_calls:
                raise KeyError("message has neither content nor tool_calls")
        except (KeyError, IndexError, TypeError) as error:
            raise LlmError(f"Malformed completion response: {error}") from error
        usage = body.get("usage") or {}
        message = {
            "role": native_message.get("role") or "assistant",
            "content": content,
        }
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {
            "content": content,
            "message": message,
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "cached_prompt_tokens": _cached_prompt_tokens(usage),
            },
            "latency_seconds": round(latency_seconds, 3),
        }


def load_backends(path: Optional[Path] = None) -> Dict[str, BackendConfig]:
    """Load all backends from configs/llm_backends.json."""

    config_path = (path or BACKENDS_PATH).resolve()
    document = json.loads(config_path.read_text(encoding="utf-8"))
    defaults = document.get("defaults", {})
    return {
        name: BackendConfig(name, definition, defaults)
        for name, definition in document.get("backends", {}).items()
    }


def load_env_file(path: Optional[Path] = None) -> None:
    """Populate os.environ from a git-ignored .env file (never overrides)."""

    env_path = (path or REPOSITORY_ROOT / ".env").resolve()
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip('"').strip("'")


def _cached_prompt_tokens(usage: Dict[str, Any]) -> int:
    for key in ("prompt_cache_hit_tokens", "cached_tokens"):
        if usage.get(key):
            return int(usage[key])
    details = usage.get("prompt_tokens_details") or {}
    if details.get("cached_tokens"):
        return int(details["cached_tokens"])
    return 0


def _safe_error_detail(error: urllib.error.HTTPError) -> str:
    try:
        body = error.read().decode("utf-8", errors="replace")[:200]
        return body.replace("\n", " ")
    except Exception:
        return str(error)
