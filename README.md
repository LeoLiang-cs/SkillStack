# SkillStack Experimental Harness

SkillStack studies whether independently designed Skill Agent components can be
swapped and composed without hidden assumptions breaking execution.

## Current milestone: P0.0 vertical slice

P0.0 is an operational validation, not a performance claim. It will establish
a reproducible ALFWorld text-environment pipeline with a small static skill
library, a control configuration, structured traces, and an adapter-friction
ledger.

### In scope tonight

- A text-only ALFWorld smoke test.
- Five fixed `valid_unseen` tasks and reproducibility settings.
- A six-skill static library spanning the ALFWorld task families.
- A no-skill control and one transparent debug retriever.
- Raw episode traces and an adapter-friction ledger.

### Explicitly out of scope tonight

- Reproducing SkillReranker or GraSP.
- A full Retrieval x Composition factorial experiment.
- Acquisition, governance, or a canonical skill schema.
- Any claim of statistically significant performance improvement.

## Repository layout

```text
configs/                 Reproducible experiment settings
skills/alfworld_static/  Native static skill artifacts
src/skillstack/          Environment, retrieval, execution, and tracing code
scripts/                 Runnable entry points
runs/                    Immutable raw run outputs (git-ignored)
reports/week1/           P0.0 milestone reports (Phases 0–7)
reports/week2/           Phase 2A plan and results
tests/                   Lightweight checks
```

## Phase 0 preflight

No external dependency is required for the current preflight check:

```bash
uv run python scripts/preflight.py
```

The check verifies that the P0.0 experiment skeleton and its declared
configuration are present. ALFWorld installation and a real environment step
begin in Phase 1.

## Phase 1: ALFWorld text environment

The P0.0 configuration keeps ALFWorld assets inside `data/alfworld`. After
dependencies are synchronized, download the text-environment assets and run
the smoke test with the project scripts. Visual assets and model checkpoints
are deliberately excluded from P0.0.

```bash
uv run python scripts/alfworld_smoke.py
```

This validates a deterministic `valid_unseen` game reset and one admissible
environment action. Its raw result is written to
`reports/week1/phase1_alfworld_smoke.json`.

## Experiment discipline

- Every run receives a unique `run_id` and stores its effective configuration.
- Fixed task identifiers and seeds are committed before comparing configurations.
- Raw traces are retained for successes and failures alike.
- Adapter transformations record information read, generated, dropped,
  approximated, or defaulted.
- Paper-inspired implementations are labelled as such unless faithful source
  code and settings are available.

## Phase 3: static skill library

The first library is intentionally a set of human-readable native artifacts,
not a canonical schema. Validate it with:

```bash
uv run python scripts/check_static_library.py
```

See [`skills/alfworld_static/README.md`](skills/alfworld_static/README.md) for
its scope and known representational limits.

## Phase 4 foundation: fixed tasks and runtime boundaries

P0.0's five evaluation tasks are frozen in
[`configs/p0_tasks.json`](configs/p0_tasks.json). Validate their metadata and
perform one genuine ALFWorld reset for each with:

```bash
uv run python scripts/validate_p0_tasks.py
```

[`docs/p0_runtime_contracts.md`](docs/p0_runtime_contracts.md) defines the
small P0.0 boundary payloads used by the loader and forthcoming retriever,
adapter, executor, and trace writer. These are not a Canonical Skill Interface.

The native static library loader is available as `skillstack.library` and can
be tested without environment interaction:

```bash
PYTHONPATH=src uv run python -m unittest tests/test_library.py
```

## Phase 4.3–4.6: deterministic retrieval-to-execution slice

The first swappable pipeline uses a no-skill control and a transparent,
task-instruction-only lexical retriever. Both feed the same explicit adapter
and recorded-action executor. The action fixture contains a single valid
`look` action per task solely to validate the environment data flow; it is not
an agent policy or a task-success result.

```bash
uv run python scripts/run_p0_episode.py --retriever no_skill --task-index 0
uv run python scripts/run_p0_episode.py --retriever debug_lexical --task-index 0
```

The single-episode command prints an in-memory trace. Use the batch command
below when persistent JSONL traces are needed.

## Phase 4.7: immutable raw traces

Run both P0.0 configurations over all five fixed tasks and persist their raw
traces with:

```bash
uv run python scripts/run_p0_batch.py --configuration all
```

Each configuration receives a new timestamped directory under `runs/` with an
immutable `run_manifest.json`, an append-only `episodes.jsonl`, and a compact
`summary.json`. These runs use the recorded one-step action fixture, so they
validate component swapping and trace completeness—not task-solving ability.

## Phase 5: register the pilot

Bind one immutable C0 run and one immutable C1 run into a reproducible pilot
summary. The command refuses to overwrite a prior summary.

```bash
uv run python scripts/summarize_pilot.py \
  --c0-run runs/<c0-run-id> \
  --c1-run runs/<c1-run-id>
```

The resulting `reports/week1/phase5_pilot_summary.json` reports pipeline
completion separately from task success and reports C1 retrieval agreement
against the frozen task-family mapping.

## Phase 6: results and friction audit

The completed pilot audit is available in
[`reports/week1/phase6_pilot_audit.md`](reports/week1/phase6_pilot_audit.md).
It separates observed retrieval mismatches from untested execution effects, and
records the first adapter-friction ledger without prematurely freezing interface
fields.

## Phase 7: advisor brief

[`reports/week1/phase7_advisor_brief.md`](reports/week1/phase7_advisor_brief.md)
packages the P0.0 evidence, the supported and unsupported claims, a
next-experiment recommendation, advisor decision questions, and a four-slide
meeting outline.

## Phase 2A (Week 2): skill-conditioned execution

Phase 2A closes the causal chain the P0.0 pilot left open: it replaces the
recorded one-step fixture with a deterministic multi-step executor that
actually consumes the selected skill context, then runs four skill-input
conditions (no-skill, random-skill, lexical Top-2, oracle) over the frozen
five tasks. Its committed plan lives in
[`reports/week2/plan_phase2a.md`](reports/week2/plan_phase2a.md), and its
results are reported under `reports/week2/`.

```bash
uv run python scripts/run_w2_skill_conditions.py --conditions all
```

Each condition receives an immutable run under `runs/`. Bind the four runs
into a reproducible pilot summary (refuses to overwrite):

```bash
uv run python scripts/summarize_w2_pilot.py \
  --no-skill-run runs/<w2-no-skill-run> \
  --random-skill-run runs/<w2-random-skill-run> \
  --lexical-run runs/<w2-lexical-run> \
  --oracle-run runs/<w2-oracle-run>
```

## Phase 2C (Week 3): LLM ReAct executor swap

Phase 2C swaps the executor slot for the first time: a zero-shot prompt-based
ReAct executor backed by an external LLM (`glm-4.7-flashx` primary,
`deepseek-v4-flash` secondary), holding retrievers, adapter, tasks, and traces
fixed. Backends and API keys are configured via
[`configs/llm_backends.json`](configs/llm_backends.json) and the git-ignored
`.env` file (keys are never committed). The committed plan lives in
[`reports/week3/plan_phase2c.md`](reports/week3/plan_phase2c.md).

```bash
uv run python scripts/run_w3_react_pilot.py --backend zhipu_glm_flashx
uv run python scripts/run_w3_react_pilot.py --backend deepseek_v4_flash
```

Bind the four runs of one backend into a reproducible summary:

```bash
uv run python scripts/summarize_w3_react_pilot.py --backend zhipu_glm_flashx \
  --no-skill-run runs/<w3-no-skill-run> \
  --random-skill-run runs/<w3-random-skill-run> \
  --lexical-run runs/<w3-lexical-run> \
  --oracle-run runs/<w3-oracle-run>
```

## Reports organization

`reports/` is organized by research week. `reports/week1/` holds the P0.0
vertical-slice milestone reports (Phases 0–7). `reports/week2/` holds the
Phase 2A plan and results. Future weeks receive their own directories.
