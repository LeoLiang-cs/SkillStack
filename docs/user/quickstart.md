# User quickstart

This page describes the public, zero-model path. It does not require a Git
checkout, benchmark data, an API key, or a model provider.

## Install an artifact

Build artifacts in a checkout with `uv build`, then copy either artifact to the
machine that will run it. In the artifact directory, install exactly one of:

```bash
python -m pip install ./skillstack-0.1.0a0-py3-none-any.whl
# or
python -m pip install ./skillstack-0.1.0a0.tar.gz
```

The filename may include a different package version. Do not install from an
editable checkout when checking the user path.

## Run the first demo

Run from any ordinary working directory, not from the source checkout:

```bash
skillstack --version
skillstack demo --output-root ./skillstack-runs
```

The command runs two deterministic retriever cells through the same adapter,
recorded-action executor, fixture environment, and JSONL trace writer. It makes
zero model and network calls. Each cell creates:

```text
skillstack-runs/demo/<run-id>/
├── run_manifest.json
├── episodes.jsonl
└── summary.json
```

`summary.json` reports pipeline/fixture completion. It is not a benchmark
score, an ALFWorld result, or evidence that the proposed BLM method is
implemented.

## Read the output

- `run_manifest.json` records the input hashes, component IDs and sources,
  configuration hash, model/budget fields, schema version, and immutable run
  identity.
- `episodes.jsonl` is append-only raw evidence. Each line carries separate
  `run_status`, `measurement_status`, and `task_success` fields.
- `summary.json` contains derived counters that can be recomputed from the
  raw JSONL file.

The current support boundary is recorded in
[`docs/open_source/SUPPORT_MATRIX.md`](../open_source/SUPPORT_MATRIX.md).
Maintained support is targeted at Python 3.11/3.12 on Linux/macOS; Python
3.9/3.10 is historical reproduction evidence, and Windows is unverified.

## Contributor-only commands

`preflight`, `check-repo`, and `release-check` inspect a repository checkout.
They intentionally fail outside a checkout with an actionable diagnostic. Use
the package path above for ordinary users.

## What is not included

The public alpha does not bundle ALFWorld/AgentBench data, external research
repositories, provider credentials, generated runs, or the held BLM cards.
Model-backed research scripts remain separate experiment entrypoints and are
not part of the zero-model installation guarantee.
