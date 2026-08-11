# Phase 6 — P0.0 Pilot Audit

## Scope and evidence

This audit summarizes the fixed five-task `valid_unseen` P0.0 pilot.

- **C0 run:** `20260810T223523023307Z_c0_no_skill`
- **C1 run:** `20260810T223529379013Z_c1_debug_lexical`
- **Source summary:** [`phase5_pilot_summary.json`](phase5_pilot_summary.json)
- **Action source:** one recorded, admissible `look` action per task.

The runs test operational interchangeability and trace completeness. They do
not measure task-solving performance: neither configuration has an action
policy that attempts to complete an ALFWorld goal.

## Result table

| Configuration | Episodes | Pipeline complete | Runner exceptions | Environment actions | Task success |
|---|---:|---:|---:|---:|---|
| C0 — no skill | 5 | 5/5 | 0 | 5 (1.0/episode) | Not evaluated |
| C1 — lexical Top-2 | 5 | 5/5 | 0 | 5 (1.0/episode) | Not evaluated |

The C1 retriever was swapped into the same runner and
`RecordedActionExecutor` used by C0. Thus, the observed operational successful
swap rate is **5/5 episodes** for this P0.0 path.

### C1 selection agreement

The reference label is the frozen task-family-to-static-skill mapping in
`configs/p0_tasks.json`; it is a selection-agreement proxy, not ground truth
for downstream utility.

| Task family | Expected skill | C1 Top-2 | Top-1 match | Expected in Top-2 |
|---|---|---|---:|---:|
| `look_at_obj_in_light` | `skill_light_inspection` | light inspection; clean then place | Yes | Yes |
| `pick_and_place_simple` | `skill_pick_and_place` | light inspection; pick and place | No | Yes |
| `pick_clean_then_place_in_recep` | `skill_clean_then_place` | clean then place; cool then place | Yes | Yes |
| `pick_heat_then_place_in_recep` | `skill_heat_then_place` | cool then place; clean then place | No | No |
| `pick_cool_then_place_in_recep` | `skill_cool_then_place` | cool then place; pick and place | Yes | Yes |

**Observed agreement:** Top-1 = 3/5; Top-2 containment = 4/5.

## Trace samples

### Trace A — selection agreement

**Task:** `look_at_obj_in_light` — “Hold the clock and turn on the lamp.”

- C1 ranked `skill_light_inspection` first (score 4.506).
- Observed overlap tokens were `lamp` and `turn`.
- The second-ranked clean skill only matched `hold` (score 2.253).
- The adapter recorded `dropped=[]`, `approximated=[]`, and `warnings=[]`.
- The executor replayed `look` and stopped at `recorded_actions_exhausted`.

This is evidence that task text can enter the native-text retriever, survive
the adapter, and reach the shared executor path without a format failure.

### Trace B — transformation mismatch

**Task:** `pick_heat_then_place_in_recep` — “Put the cooked green apple in the
fridge.”

- The expected static skill was `skill_heat_then_place`.
- C1 ranked `skill_cool_then_place` first (score 3.589) and
  `skill_clean_then_place` second (score 1.336); the expected heat skill was
  absent from Top-2.
- The cooling skill matched `fridge` and `put`; the heat skill matched only
  `put`.
- The adapter again recorded no dropped, approximated, or defaulted fields.
- The fixed `look` action did not test whether an executor could recover from
  this selection.

This is an observed **retrieval mismatch**, not an observed execution failure
or a proven adapter failure.

## Adapter-friction ledger v0

| ID | Boundary | Observed evidence | Classification | Candidate information to test later | Status |
|---|---|---|---|---|---|
| F-01 | Task → retriever | In the simple placement task, `desk` gave the lamp skill the same score as `move` gave the placement skill; stable tie order placed the lamp skill first. | Goal-intent granularity mismatch | `goal_operation` / task intent such as place, inspect, clean, heat, cool | Observed selection mismatch; no execution test |
| F-02 | Task → retriever | In the heat task, destination term `fridge` dominated the required transformation implied by `cooked`; expected heat skill was outside Top-2. | Transformation/postcondition leakage | `required_transformation` and possibly explicit desired postcondition | Observed selection mismatch; no execution test |
| F-03 | State → retriever | C1 explicitly used `task_instruction_only`; raw observation was logged but excluded from its score. | State applicability is untested | current held object, appliance state, container openness, object location | Coverage gap, not a failure claim |
| F-04 | Retriever → adapter | All C1 adapter events reported `dropped=[]`, `approximated=[]`, `defaulted=[]`. Native Markdown passed into flat context. | No adapter semantic loss observed in this path | None added yet | Negative finding for this adapter only |
| F-05 | Adapter/executor → outcome | Both configurations replayed the same one-step `look`; selected skills could not change action choice or success. | Causal attribution unavailable | executor decision rationale; multi-step policy/action trace | Measurement limitation |

## Phase 6 conclusion

P0.0 now has a reproducible, traceable interchangeability pilot: swapping C0
for C1 does not require a runner or executor rewrite, and all episodes produce
the same trace shape. The pilot also identifies two concrete selection failures
whose likely missing semantics are **goal operation** and **required
transformation**.

These are candidate interface fields, not yet Canonical Skill Interface v1
fields. They should be retained only if a state-aware retriever or multi-step
executor reproduces and explains the same failures.

