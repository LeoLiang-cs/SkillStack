# Configuration and runs

The core CLI demo is deliberately configuration-free: it uses packaged,
deterministic fixtures and never contacts a model provider. Model-backed
research scripts use the small standard-library client under
`src/skillstack/llm/` and must be treated as separate, provider-dependent
experiments.

## Entry-point boundary

| Entry point | Environment | Stable status |
|---|---|---|
| `skillstack --version`, `skillstack demo` | installed package or checkout | maintained offline user path |
| `skillstack preflight`, `check-repo`, `release-check` | SkillStack checkout | contributor/release checks; fail outside a checkout |
| `scripts/run_w*.py`, provider/benchmark launchers | explicit research checkout and optional services | historical or experiment-specific; not a package guarantee |

## Backend metadata precedence

For `load_backends()` the current effective order is:

1. an explicit `Path` passed by the caller (the CLI/research caller's choice);
2. `SKILLSTACK_LLM_CONFIG`, when set to a readable JSON file;
3. the user file `$XDG_CONFIG_HOME/skillstack/llm_backends.json`, or
   `~/.config/skillstack/llm_backends.json` when `XDG_CONFIG_HOME` is unset;
4. `configs/llm_backends.json` when running from a checkout;
5. the safe package resource shipped in the wheel/sdist.

An explicitly selected path or environment override that does not exist is an
error; SkillStack does not silently fall back to a different provider
configuration. The public zero-model CLI still exposes no model-selection
flag, so an installed demo cannot accidentally become a paid run.

The loader validates the document, endpoint scheme, required backend fields,
numeric retry/budget defaults, and price metadata before a provider request can
start. Use `load_backend(name)` in a research script when an unknown backend
should produce a stable diagnostic instead of a raw dictionary `KeyError`.

Research scripts select a named backend explicitly. A live client also applies
finite timeout/retry settings and the packaged default run budget: 500 calls,
500,000 prompt tokens, 100,000 completion tokens, or USD 10, whichever is
reached first. A caller can pass a smaller `budget` mapping to `LlmClient` for
a pilot; budget exhaustion is an explicit error and the recorded usage remains
available through `client.budget.snapshot()`.

Backend JSON stores endpoint/model metadata and the *name* of the environment
variable that contains a credential. It must never contain the credential
value. A missing key or malformed backend definition must be fixed before a
provider request is attempted.

## Environment files and credentials

Research scripts may call `load_env_file()` explicitly. With no argument it
reads only `.env` in the current working directory; it does not search parent
directories or an author checkout, and an already-set environment variable is
never overwritten. Keep `.env` git-ignored and remove credentials from copied
logs, traces, issue reports, and provider error messages.

The HTTP client applies finite request timeout/retry defaults and redacts
credential-like values from provider error details. It retries only transient
HTTP/network failures and caps exponential backoff. A live experiment must
retain its raw failure evidence before it can support a research claim.

## Run directories and identity

`JsonlTraceWriter` creates one run directory below the caller's output root.
The run ID is a single safe relative component; absolute paths, `..`, and
cross-directory values are rejected. Existing `run_manifest.json` and
`summary.json` files are never overwritten. Manifest and summary writes use a
same-directory temporary file followed by an atomic replacement; episode JSONL
records are append-only and flushed before the call returns.
Episode appends reject symlink targets, use an OS append handle, and serialize
writers on maintained Linux/macOS platforms so concurrent writers cannot
interleave JSON records or admit a duplicate episode ID. A failed append is
rolled back to the previous complete-file length.

The manifest's `run_identity_sha256` is derived from canonicalized result-
relevant fields. `JsonlTraceWriter.resume(...)` reads the stored manifest and
rejects configuration drift. A changed configuration is a new run, not a
silent continuation of the old one.

## Status semantics

| Field | Meaning |
|---|---|
| `run_status` | execution state: `running`, `completed`, `error`, `timeout`, or `cancelled` |
| `measurement_status` | whether a result is usable: `valid`, `invalid`, `abstained`, or `not_applicable` |
| `task_success` | executor/environment outcome: `true`, `false`, or `null` when it is unknown; `benchmark_success_claim` separately controls whether it may be interpreted as benchmark evidence |

The summary counters are derived from raw episode lines. A runner exception,
timeout, invalid input, active abstention, and task failure remain distinct;
unknown success is not silently converted to `false`. In the zero-model demo a
`true` value means the deterministic fixture completed; its
`benchmark_success_claim=false` field keeps that outcome outside benchmark
evidence.

`skillstack-episode-trace-v1` keeps observations, selected native payloads,
adapter events, actions, warnings, and the complete executor report. Live ReAct
executor reports retain per-call usage and provider latency; the zero-model
fixture records zero model/network calls instead of inventing token or latency
measurements.

## Resume and partial evidence

Resume is currently a low-level writer contract, not a scheduler. Callers must
choose their retry policy, decide which failed episodes are eligible to rerun,
and preserve any raw lines before retrying. A duplicate episode ID is rejected.
Malformed JSONL or a missing manifest is a hard diagnostic so that partial
evidence is inspected rather than silently discarded.
