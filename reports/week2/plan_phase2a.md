# Phase 2A (Week 2) — Committed Plan: Skill-Conditioned Execution

**Status:** committed before runs. This plan freezes the experiment before any
week-2 pilot traces are produced.

## 1. Objective

P0.0 proved structural interchangeability: C0 and C1 completed the same
pipeline with the same trace shape, and swapping the retriever required no
runner/executor rewrite. It could not say anything about skill *utility*,
because the recorded one-step `look` fixture never depended on the selected
skill.

Phase 2A closes that gap with one question:

> **Does the selected skill change the agent's actions and task outcomes, and
> if so, how?**

Everything else in Phase 2A exists to answer this question cleanly.

## 2. Why a deterministic executor first

`reports/week1/phase0_manifest.json` records `model_access_status:
not_configured`. Two executor routes exist:

| Route | Pros | Cons |
|---|---|---|
| LLM ReAct executor | Matches the framework's B00 target; real compositional behavior | Blocked on model access; decoding nondeterminism; cost |
| Deterministic skill-plan executor | Runs offline today; attribution is clean; no model confound | Hand-coded; not a paper reproduction |

**Decision (this plan):** build the deterministic executor first. It is a
SkillStack-authored, hand-coded policy, explicitly labelled
`method-authored` / not a reproduction of ReAct or any paper. It consumes
`flat_skill_context` and derives its plan skeleton from the selected skill's
`Procedure`. The LLM ReAct executor becomes a follow-up swap target once model
access is configured (the executor slot, not the experiment design, changes).

This order mirrors the advisor-brief recommendation: establish that the skill
channel causally affects execution before touching retrieval semantics.

## 3. Design

### 3.1 Four skill-input conditions (shared executor, shared tasks)

| Condition | Retriever | Intervention |
|---|---|---|
| C-no-skill | `NoSkillRetriever` | Lower bound: no skill guidance |
| C-random | `RandomSkillRetriever(seed)` | Wrong-skill control: any guidance effect is content-specific |
| C-lexical | `DebugLexicalRetriever` (Top-2) | Current P0.0 retriever |
| C-oracle | `OracleSkillRetriever` | Upper bound: the frozen `expected_skill_id` |

The frozen mapping in `configs/p0_tasks.json` supplies `expected_skill_id` for
the oracle. All four share: the six-artifact static library, the retrieval →
execution adapter, the executor, the five frozen tasks, seed 42, step budget
50, and the JSONL trace format.

### 3.2 Executor

`SkillPlanExecutor` (new, `src/skillstack/execution/skillplan.py`):

- Reads the top-ranked selected skill's `Procedure` and instantiates a plan
  skeleton keyed by skill id (a hard-coded executor-side mapping, recorded in
  the adapter event as executor knowledge, not hidden).
- Binds task-specific object / destination / appliance names by parsing the
  task instruction.
- Each turn selects one admissible ALFWorld command that advances the current
  plan step; unmatched mandatory steps trigger bounded exploration fallback
  (`go to` unexplored receptacles, `open` closed containers, `look`).
- With no selected skill, it falls back to a generic explore–take–place plan
  that performs **no transformations**, which is the honest no-skill baseline.
- Every action records `action_rationales`: which skill id, which plan step,
  why the command was chosen, and which admissible commands matched.

### 3.3 Metrics

- **Primary:** task success (environment `done` with positive score) — first
  time success is measurable in SkillStack.
- Steps per episode, invalid/non-admissible action rate, stop-reason
  distribution (`environment_done`, `max_steps_exhausted`,
  `plan_step_unavailable`, `runner_exception`).
- Action ↔ skill-step correspondence (rationale coverage).
- Retrieval selection for the record (Top-1/Top-2 vs frozen mapping).

### 3.4 Gate hypothesis H1 (run-order enforced)

> C-oracle must strictly outperform C-no-skill and C-random on the frozen
> five tasks.

If H1 fails, the skill channel is not actually consumed by the executor:
**fix the executor and re-run; do not proceed to retrieval semantics.** A
failed H1 is itself a reportable negative result about this executor.

## 4. Fixed items

Task manifest (`configs/p0_tasks.json`), static library v0, runner glue,
adapter, trace format, seed 42, step budget 50, `top_k=2`, no retries, no
decoding parameters (no LLM), ALFWorld `valid_unseen` text assets.

## 5. Explicit non-goals (deferred)

- Acquisition / governance dual implementations (Phase 3).
- Graph planner; `flat_skill_context` only (B01/B11 cells deferred).
- Retrieval semantics intervention: no synonym normalization, no
  `goal_operation`/`required_transformation` extraction, no state-aware
  scoring this week (Phase 2B).
- Canonical Skill Interface v1 freeze (friction ledger only).
- Second environment, statistical significance claims, paper reproductions.

## 6. Artifacts

- `src/skillstack/retrieval/random.py`, `oracle.py` — two new retrieval slots.
- `src/skillstack/execution/skillplan.py` — deterministic multi-step executor.
- `scripts/run_w2_skill_conditions.py` — 5 tasks × 4 conditions batch run.
- `runs/` — immutable per-condition runs (manifest + JSONL + summary).
- `reports/week2/w2_pilot_summary.json` — one-time pilot summary.
- `reports/week2/w2_friction_ledger.md` — friction ledger v1 additions.
- `reports/week2/w2_advisor_brief.md` (+ `_zh.md`) — second advisor update.
- `tests/` — unit tests for new retrievers and the executor.

## 7. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Hand-coded executor overfits the five tasks | Labelled as method-authored; plan skeletons come from skill Procedures, not task ids; success/failure analysed per step rationale |
| Executor silently ignores skill context | H1 gate + `action_rationales` make consumption observable |
| No-skill baseline too weak to be informative | Report it as the no-skill policy, not a tuned agent |
| 1 sample per task family | Report raw counts only; no percentage extrapolation (expansion is Phase 2B) |
| Plan-step parser misreads instruction wording | Parsing warnings go into executor warnings; failure traces retained |
