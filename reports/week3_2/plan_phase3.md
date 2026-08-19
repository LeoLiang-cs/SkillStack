# Phase 3 (week3_2) — Committed Plan: RQ3 2×2 Factorial + Canonical Interface v1

**Status:** committed before runs. All four locked decisions are recorded here.

## 0. Locked decisions (advisor-resolved 2026-08-18)

1. Reports live in `reports/week3_2/`.
2. R1 retriever = transparent heuristic (regex field extraction, no LLM,
   reproducible).
3. E1 executor = lightweight structured step injection (numbered Procedure
   steps + "follow in order" guidance; no hard step locking).
4. Discriminative task set = 9 `pick_two_obj_and_place` instances.

Fixed stack: `deepseek-v4-flash`, 20-step budget, seed 42, temperature 0,
frozen 2C prompt (v1.1) as the base for E0; E1 adds only a `Steps:` block.

## 1. Objective

Phase 2D localized the discriminating regime (pick_two + tight budget) and
found the first skill-channel signal (no-skill 1/3 vs skill-bearing 2/3).
Phase 3 turns the project toward the paper mainline:

- **RQ3 (Composability):** first 2×2 factorial — two mechanism-different
  retrievers × two mechanism-different executors — and the interaction
  measure I.
- **RQ4 / contribution #3:** induct `docs/canonical_interface_v1.md` from the
  friction ledger using the framework's rule: a field enters the interface
  only if ≥2 implementations need it or it explains a reproduced failure.

## 2. Phase 3A — the two missing implementations

### A1 `TaskSemanticRetriever` (R1)

- Extract the task-parsing helpers from `skillplan.py` into a shared module
  `src/skillstack/task_semantics.py` (single source of truth).
- Task → structured fields: `goal_operation`, `required_transformation`,
  `destination`, `object(s)`.
- Observation → state fields: held object, required appliance present in the
  room, reachable containers.
- Score = field-match + precondition-applicability (does the skill's required
  appliance exist in this room; is the state admissible).
- `raw_output` records the extracted fields and per-skill score breakdowns —
  raw evidence for interface induction.
- Mechanism differs from lexical (field-match + applicability vs token
  overlap).

### A2 `StructuredReActExecutor` (E1)

- Parameterize the existing `ReActExecutor` (same strict validation, retry,
  accounting); new prompt mode: numbered Procedure steps injected as a
  `Steps:` block plus one line "the skill lists steps; follow them in order".
- New trace field per rationale: `grounded_step` (which skill step the action
  implements, or null).
- Mechanism differs from E0 (structured step consumption vs flat prose).

### A3 Tests

`tests/test_task_semantic.py`, `tests/test_react_structured.py` (fake client).
Gate: full suite green (35 existing + new).

## 3. Phase 3B — freeze and validate the 9 pick_two tasks

- Select 9 of the 17 solvable `pick_two` trials covering distinct object
  types; freeze `configs/p0_tasks_picktwo9.json`.
- Parameterize `scripts/validate_hard_tasks.py` with `--manifest/--report`
  and run it. Gate: 9/9 real resets pass.

## 4. Phase 3C — 2×2 factorial

| | E0 flat-text ReAct | E1 structured ReAct |
|---|---|---|
| R0 lexical | B00 | B01 |
| R1 task-semantic | B10 | B11 |

- Plus one no-skill control (E0, no skills) as an ablation reference; **not**
  part of the interaction calculation.
- `scripts/run_w3_2_factorial.py`: 4 cells + control, 9 tasks × 20 steps,
  immutable runs under `runs/`.
- `scripts/summarize_w3_2_factorial.py`: per-cell success/steps/cost; then
  I = Y11 − Y10 − Y01 + Y00 computed on success rate, steps, and cost;
  verdict synergy (>0) / independent (≈0) / redundancy or interference (<0).
- Gate: 4 cell raw runs reproducible; I values + verdicts produced.

## 5. Phase 3D — Canonical Interface v1 induction

- D1: cluster friction entries F-01…F-21 (+ new week3_2 entries) by candidate
  field: `goal_operation`, `required_transformation`, `procedure` (ordered
  steps), `required_appliance`, command-validity contract,
  `task_instruction` canonicalization, state-applicability.
- D2: apply the framework rule (field enters only if ≥2 implementations need
  it or it explains a reproduced failure); everything else stays in native
  payload.
- D3: write `docs/canonical_interface_v1.md` with required/optional/extension
  tiers; each required field cites the implementations needing it and the
  F-number evidence.
- Gate: every required field has an evidence chain; no pre-designed fields.

## 6. Phase 3E — reports

- `reports/week3_2/plan_phase3.md` (this file), 2×2 summary, ledger
  continuation, fifth advisor brief (zh + en).
- A short RQ1 assessment: do the five responsibilities describe this
  implementation mapping without over-constraining it?

## 7. Dependencies

```
A1 ─┬─→ C1 → C2 → D1 → D2 → D3 → E1
A2 ─┘        ↑
A3          B1 → B2   (B parallel with A)
```

## 8. Non-goals

- No LLM task decomposition (R1 stays deterministic).
- No hard step locking in E1 (lightweight only).
- No new backends; no acquisition/governance; no second environment.
