"""Minimal zero-dependency OpenAI-compatible LLM client for executor backends.

Reads backend definitions from `configs/llm_backends.json` and API keys from
environment variables (populated from the git-ignored `.env`). Every call
reports usage and latency so episode traces can estimate cost.
"""

from __future__ import annotations

import json
import importlib.resources as package_resources
import math
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
BACKENDS_PATH = REPOSITORY_ROOT / "configs" / "llm_backends.json"
PACKAGED_BACKENDS = package_resources.files("skillstack.resources").joinpath(
    "config/llm_backends.json"
)


class LlmError(RuntimeError):
    """Raised when a backend call fails after retries."""


class BudgetExceededError(LlmError):
    """Raised before or after a call would exceed the configured run budget."""


@dataclass
class RunBudget:
    """Small run-level guard for provider calls and measured usage."""

    max_calls: Optional[int] = None
    max_prompt_tokens: Optional[int] = None
    max_completion_tokens: Optional[int] = None
    max_cost_usd: Optional[float] = None
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "RunBudget":
        def optional_int(name: str) -> Optional[int]:
            value = values.get(name)
            return None if value is None else max(0, int(value))

        def optional_float(name: str) -> Optional[float]:
            value = values.get(name)
            return None if value is None else max(0.0, float(value))

        return cls(
            max_calls=optional_int("max_calls_per_run"),
            max_prompt_tokens=optional_int("max_prompt_tokens_per_run"),
            max_completion_tokens=optional_int("max_completion_tokens_per_run"),
            max_cost_usd=optional_float("max_cost_usd_per_run"),
        )

    def reserve_call(self) -> None:
        if self.max_calls is not None and self.calls >= self.max_calls:
            raise BudgetExceededError(
                f"run call budget exhausted ({self.calls}/{self.max_calls} calls)"
            )
        self.calls += 1

    def record(self, usage: Mapping[str, Any], cost_usd: float) -> None:
        self.prompt_tokens += int(usage.get("prompt_tokens", 0) or 0)
        self.completion_tokens += int(usage.get("completion_tokens", 0) or 0)
        self.cost_usd += float(cost_usd)
        if (
            self.max_prompt_tokens is not None
            and self.prompt_tokens > self.max_prompt_tokens
        ):
            raise BudgetExceededError(
                "run prompt-token budget exhausted "
                f"({self.prompt_tokens}/{self.max_prompt_tokens})"
            )
        if (
            self.max_completion_tokens is not None
            and self.completion_tokens > self.max_completion_tokens
        ):
            raise BudgetExceededError(
                "run completion-token budget exhausted "
                f"({self.completion_tokens}/{self.max_completion_tokens})"
            )
        if self.max_cost_usd is not None and self.cost_usd > self.max_cost_usd:
            raise BudgetExceededError(
                f"run cost budget exhausted (${self.cost_usd:.6f}/${self.max_cost_usd:.6f})"
            )

    def snapshot(self) -> Dict[str, Any]:
        return {
            "max_calls": self.max_calls,
            "max_prompt_tokens": self.max_prompt_tokens,
            "max_completion_tokens": self.max_completion_tokens,
            "max_cost_usd": self.max_cost_usd,
            "calls": self.calls,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cost_usd": round(self.cost_usd, 6),
        }


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
        budget: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self.backend = backend
        self.api_key = api_key or backend.resolve_api_key()
        self.timeout_seconds = (
            float(timeout_seconds)
            if timeout_seconds is not None
            else float(backend.defaults.get("request_timeout_seconds", 120))
        )
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.max_retries = max(1, min(int(backend.defaults.get("max_retries_per_call", 3)), 8))
        self.backoff_seconds = max(
            0.0, float(backend.defaults.get("retry_backoff_seconds", 2.0))
        )
        self.max_backoff_seconds = max(
            0.0, float(backend.defaults.get("max_retry_backoff_seconds", 30.0))
        )
        self.budget = RunBudget.from_mapping(budget or backend.defaults)

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

        self.budget.reserve_call()
        for attempt in range(1, self.max_retries + 1):
            started = time.monotonic()
            try:
                body = self._post(payload)
                latency_seconds = time.monotonic() - started
                response = self._parse_response(body, latency_seconds)
                self.budget.record(
                    response["usage"], self.estimate_cost_usd(response["usage"])
                )
                return response
            except urllib.error.HTTPError as error:
                detail = _safe_error_detail(error)
                if error.code in (408, 429) or 500 <= error.code < 600:
                    if attempt < self.max_retries:
                        time.sleep(
                            min(
                                self.max_backoff_seconds,
                                self.backoff_seconds * (2 ** (attempt - 1)),
                            )
                        )
                        continue
                raise LlmError(
                    f"{self.backend.name} call failed after {attempt} attempt(s): "
                    f"HTTP {error.code} {detail}"
                ) from error
            except (urllib.error.URLError, TimeoutError, OSError) as error:
                if attempt < self.max_retries:
                    time.sleep(
                        min(
                            self.max_backoff_seconds,
                            self.backoff_seconds * (2 ** (attempt - 1)),
                        )
                    )
                    continue
                detail = _redact_sensitive_text(str(error))
                raise LlmError(
                    f"{self.backend.name} call failed after {attempt} attempt(s): {detail}"
                ) from error
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
    """Load metadata with explicit > env > user > checkout > package priority."""

    if path is not None:
        source = path.expanduser().resolve()
    elif os.environ.get("SKILLSTACK_LLM_CONFIG"):
        source = Path(os.environ["SKILLSTACK_LLM_CONFIG"]).expanduser().resolve()
    else:
        user_source = _user_backend_config_path()
        if user_source.is_file():
            source = user_source
        elif BACKENDS_PATH.exists():
            source = BACKENDS_PATH
        else:
            source = PACKAGED_BACKENDS
    if not source.is_file():
        raise FileNotFoundError(f"LLM backend config does not exist: {source}")
    try:
        document = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid LLM backend config {source}: JSON line {error.lineno}, "
            f"column {error.colno}"
        ) from error
    _validate_backend_document(document, source)
    defaults = document.get("defaults", {})
    return {
        name: BackendConfig(name, definition, defaults)
        for name, definition in document.get("backends", {}).items()
    }


def load_backend(name: str, path: Optional[Path] = None) -> BackendConfig:
    """Load one named backend with a deterministic unknown-name diagnostic."""

    backends = load_backends(path)
    if name not in backends:
        available = ", ".join(sorted(backends)) or "<none>"
        raise ValueError(
            f"Unknown LLM backend {name!r}; configured backends: {available}"
        )
    return backends[name]


def _validate_backend_document(document: Any, source: Path) -> None:
    """Reject malformed provider metadata before a caller can make a request."""

    if not isinstance(document, dict):
        raise ValueError(f"Invalid LLM backend config {source}: top-level object required")
    defaults = document.get("defaults", {})
    if not isinstance(defaults, dict):
        raise ValueError(f"Invalid LLM backend config {source}: defaults must be an object")
    numeric_defaults = {
        "temperature": (0.0, None),
        "max_tokens_per_step": (1.0, None),
        "request_timeout_seconds": (0.0, None),
        "max_retries_per_call": (1.0, 8.0),
        "retry_backoff_seconds": (0.0, None),
        "max_retry_backoff_seconds": (0.0, None),
        "max_calls_per_run": (0.0, None),
        "max_prompt_tokens_per_run": (0.0, None),
        "max_completion_tokens_per_run": (0.0, None),
        "max_cost_usd_per_run": (0.0, None),
    }
    for key, (minimum, maximum) in numeric_defaults.items():
        if key not in defaults:
            continue
        value = defaults[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"Invalid LLM backend config {source}: defaults.{key} must be numeric")
        if not math.isfinite(float(value)) or float(value) < minimum:
            raise ValueError(
                f"Invalid LLM backend config {source}: defaults.{key} must be finite and >= {minimum}"
            )
        if maximum is not None and float(value) > maximum:
            raise ValueError(
                f"Invalid LLM backend config {source}: defaults.{key} must be <= {maximum}"
            )

    backends = document.get("backends")
    if not isinstance(backends, dict) or not backends:
        raise ValueError(f"Invalid LLM backend config {source}: backends must be a non-empty object")
    required_fields = ("base_url", "model", "api_key_env")
    for name, definition in backends.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Invalid LLM backend config {source}: backend names must be non-empty strings")
        if not isinstance(definition, dict):
            raise ValueError(f"Invalid LLM backend config {source}: backend {name!r} must be an object")
        for field in required_fields:
            value = definition.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Invalid LLM backend config {source}: backend {name!r} requires non-empty {field}"
                )
        if not definition["base_url"].lower().startswith(("http://", "https://")):
            raise ValueError(
                f"Invalid LLM backend config {source}: backend {name!r} base_url must use http(s)"
            )
        prices = definition.get("prices_usd_per_1m", {})
        if not isinstance(prices, dict):
            raise ValueError(
                f"Invalid LLM backend config {source}: backend {name!r} prices_usd_per_1m must be an object"
            )
        for price_name, price in prices.items():
            if isinstance(price, bool) or not isinstance(price, (int, float)):
                raise ValueError(
                    f"Invalid LLM backend config {source}: backend {name!r} price {price_name!r} must be numeric"
                )
            if not math.isfinite(float(price)) or float(price) < 0:
                raise ValueError(
                    f"Invalid LLM backend config {source}: backend {name!r} price {price_name!r} must be finite and >= 0"
                )


def _user_backend_config_path() -> Path:
    config_home = os.environ.get("XDG_CONFIG_HOME")
    if config_home:
        return Path(config_home).expanduser() / "skillstack" / "llm_backends.json"
    return Path.home() / ".config" / "skillstack" / "llm_backends.json"


def load_env_file(path: Optional[Path] = None) -> None:
    """Populate os.environ from an explicit or current-directory .env file."""

    env_path = (path or Path.cwd() / ".env").expanduser().resolve()
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
        return _redact_sensitive_text(body.replace("\n", " "))
    except Exception:
        return _redact_sensitive_text(str(error))


_SENSITIVE_TEXT_PATTERNS = (
    (re.compile(r"(authorization\s*:\s*bearer\s+)[^\s,;]+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"((?:cookie|set-cookie)\s*[=:]\s*)[^\s,;]+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"((?:api[_-]?key|token|secret|password)\s*[=:]\s*)[^\s,;]+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"\b(?:sk|gh[pousr]|AIza)[-_A-Za-z0-9]{12,}\b"), "[REDACTED]"),
)


def _redact_sensitive_text(text: str) -> str:
    """Keep provider diagnostics useful without echoing credential-like values."""

    redacted = text
    for pattern, replacement in _SENSITIVE_TEXT_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted[:200]
