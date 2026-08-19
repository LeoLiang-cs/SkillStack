# Phase 2C (Week 3) — Committed Plan: LLM ReAct Executor Swap

**Status:** committed before runs. This plan freezes the experiment before any
week-3 pilot traces are produced.

## 1. Objective

Phase 2A closed the causal chain with a hand-coded deterministic executor
(oracle 5/5 vs no-skill/random 1/5). Phase 2C now swaps the **executor slot**
for the first time: a prompt-based **ReAct executor** backed by an external
LLM, holding every other component fixed. This tests RQ2 (interchangeability)
on the executor boundary and establishes the framework's B00 configuration
(flat skill injection + ReAct).

> **Can a full ReAct executor replace the deterministic executor without
> rewriting the runner, adapter, retrievers, tasks, or trace format? And does
> the skill-input condition ordering survive the swap?**

## 2. Backend decision (advisor-resolved)

- **Primary:** Zhipu `glm-4.7-flashx` via z.ai OpenAI-compatible endpoint.
- **Secondary (portability control):** DeepSeek `deepseek-v4-flash`.
- Both keys verified working (2026-08-18). Native thinking mode is disabled
  on both (`thinking: {type: disabled}`); the prompt itself carries the
  Thought/Action alternation.
- No peak/off-peak scheduling: the advisor chose "run anytime"; cost is
  estimated with the provider price tables in `configs/llm_backends.yaml`.

## 3. Design

### 3.1 Executor

`ReActExecutor` (new, `src/skillstack/execution/react.py`):

- Zero-shot prompt (frozen in `configs/p0_react_prompt.txt`): task text +
  admissible commands + injected `flat_skill_context` + strict
  `Thought/Action` output format. No few-shot trajectories in v1; adding
  shots is a separate, recorded prompt variant.
- Per step: one model call → parse `Action:` → validate against the current
  admissible commands → one retry on invalid output with explicit feedback →
  execute or stop.
- Records per step: thought, action, rationale, model id, prompt/completion
  and cached token counts, latency, and estimated cost from the price table.
- `Action: done` stops the episode with `agent_declared_done` (success only
  if the environment already reported done).
- Same executor report shape as `SkillPlanExecutor` so downstream trace
  consumers do not change.

### 3.2 Conditions

The four Phase-2A skill-input conditions are unchanged:

| Condition | Retriever |
|---|---|
| no_skill | `NoSkillRetriever` |
| random_skill | `RandomSkillRetriever` (seeded per task) |
| lexical | `DebugLexicalRetriever` Top-2 |
| oracle | `OracleSkillRetriever` |

### 3.3 Metrics

Task success, steps per episode, invalid-action rate, stop-reason
distribution, per-episode token counts and estimated cost, and
action-rationale coverage (thoughts preserved in traces).

### 3.4 Gates

- **G1 (format):** invalid-action rate must be interpretable and bounded;
  every format failure is a trace, not a crash.
- **G2 (skill channel):** C-oracle must strictly outperform C-no-skill and
  C-random under the ReAct executor. A failure here means skill context is
  not being consumed — reported as a negative result for the executor, not a
  retrieval conclusion.
- **G3 (swap):** the runner/adapter/retriever/trace stack must require zero
  changes for the swap.

## 4. Fixed items

Frozen five tasks, static library v0, retrieval adapter, runner glue, JSONL
trace format, seed 42, step budget 50, `top_k=2`, temperature 0, prompt text
(versioned in `configs/`), max output tokens per step (512).

## 5. Explicit non-goals

- Few-shot/prompt engineering variants (later, as a recorded prompt swap).
- Backend A/B as a model-quality comparison: DeepSeek runs are reported as a
  portability check of the executor across backends, not a model bake-off.
- Acquisition/governance, graph composition, Canonical Interface v1.

## 6. Artifacts

- `configs/llm_backends.json`, `configs/p0_react_prompt.txt`
- `src/skillstack/llm/client.py`
- `src/skillstack/execution/react.py`
- `scripts/run_w3_react_pilot.py`, `scripts/summarize_w3_react_pilot.py`
- `runs/` immutable per-condition per-backend runs
- `reports/week3/` summary, friction ledger additions, advisor brief
- `tests/` unit tests with a fake LLM client

## 7. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Zero-shot format failures dominate | G1 trace; retry policy recorded; prompt variant is the sanctioned next intervention |
| Cost overrun | max_tokens 512/step, 50-step cap, price table accounting per call; whole pilot estimated at a few USD |
| Provider rate limits / 5xx | Exponential-backoff retry (3 attempts) with full error capture |
| Model nondeterminism at temperature 0 | Reported per seed; reruns allowed only with a new run_id |

## 8. Addendum (2026-08-18, pre-full-pilot): probe evidence and primary/secondary flip

Before the full pilot, a 5-task oracle probe measured the strict-retry ReAct
executor on both backends:

| Backend | Probe result | Invalid-action retries |
|---|---|---|
| `glm-4.7-flashx` | 1/4 episodes succeeded; most died on `invalid_action_retries_exhausted` (model proposes commands absent from the admissible list, including navigation to nested receptacle-objects) | frequent |
| `deepseek-v4-flash` | 2/5 at a 30-step cap (pick-and-place, clean); zero invalid actions across all 5 tasks; remaining failures were strategy errors (early `done`, step budget) | 0 |

The probe inverts the advisor-assumed backend ordering: strict zero-shot ReAct
validity is the binding constraint, and it is met by DeepSeek but not by GLM.
**Amended decision:** the full four-condition pilot runs on
`deepseek-v4-flash` as the primary evidence; the GLM full run is still
executed and recorded, but interpreted as a **backend portability result**
(the executor does not port losslessly to the cheapest backend). Both runs
use the identical frozen prompt and stack; the pilot summary is produced
per backend, and the GLM one carries a portability interpretation. No prompt
changes were made between probe and pilot.
