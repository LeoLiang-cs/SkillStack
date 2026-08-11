# SkillStack P0.0 — Advisor Update

**Status:** P0.0 vertical slice complete.  
**Environment:** ALFWorld text-only, `valid_unseen`, five fixed tasks.  
**Purpose of this update:** demonstrate an executable interoperability harness
and identify the first evidence-backed interface questions. This is not yet a
task-solving or SOTA comparison result.

## 1. Research question

> Can independently designed Skill Agent components be swapped and composed in
> a shared harness? If not, what hidden assumptions or missing semantics does
> the failure expose?

The immediate P0.0 question is narrower:

> Can a no-skill control and a transparent lexical skill retriever use the same
> static library, adapter, executor, environment, and trace format without
> rewriting downstream components?

## 2. What is now implemented

```mermaid
flowchart LR
    A["Fixed ALFWorld task"] --> B["Native static skill library"]
    B --> C["C0: no-skill / C1: lexical retriever"]
    C --> D["Explicit retrieval-to-execution adapter"]
    D --> E["Recorded-action executor"]
    E --> F["ALFWorld text environment"]
    F --> G["Immutable JSONL trace + run manifest"]
    G --> H["Pilot audit + friction ledger"]
```

Concrete artifacts:

- ALFWorld text-only environment is installed and verified through real reset
  and action execution.
- Five fixed, loadable `valid_unseen` tasks are frozen in
  `configs/p0_tasks.json`.
- Six hand-authored native-text skills cover ALFWorld task families.
- C0 and C1 retrievers share one runner, adapter, executor, action fixture,
  task set, seed, and trace format.
- Every run has a manifest, append-only JSONL trace, and summary.

## 3. Pilot design and results

| Configuration | Skill selection | Episodes | Pipeline complete | Runner exceptions | Task success |
|---|---|---:|---:|---:|---|
| C0 | No-skill control | 5 | 5/5 | 0 | Not evaluated |
| C1 | Task-instruction lexical Top-2 | 5 | 5/5 | 0 | Not evaluated |

The shared executor replayed exactly one admissible `look` action in every
episode. Therefore the pilot verifies component interchangeability and trace
completeness; it does **not** compare task success rates.

For C1, agreement with the frozen task-family-to-static-skill mapping is:

| Metric | Result |
|---|---:|
| Expected skill ranked Top-1 | 3/5 |
| Expected skill present in Top-2 | 4/5 |
| C1 episodes completing the shared pipeline | 5/5 |

This produces a limited but concrete finding: replacing C0 with C1 required no
runner or executor rewrite, yet C1's task-text-only selection is imperfect in
interpretable ways.

## 4. Most informative trace case

**Heat task:** “Put the cooked green apple in the fridge.”

- Expected static skill: `skill_heat_then_place`.
- C1 Top-2: `skill_cool_then_place`, then `skill_clean_then_place`.
- Evidence: lexical scoring emphasized `fridge` and `put`; the intended heat
  transformation did not enter Top-2.
- Adapter event: `dropped=[]`, `approximated=[]`, `defaulted=[]`.
- Execution impact: not yet measured, because the recorded `look` action does
  not use selected skills to choose a plan.

Interpretation: this is an observed **retrieval mismatch**, not evidence that
the adapter or executor caused a failure.

## 5. Current evidence-backed claims

We can claim:

1. SkillStack now has an executable ALFWorld P0.0 harness with reproducible
   task selection, native skill artifacts, swappable retrieval, explicit
   adapter logging, and immutable traces.
2. C0 and C1 are operationally interchangeable on the shared path for all five
   pilot tasks.
3. Native-text-to-flat-context adaptation did not lose or fabricate fields in
   this particular path.
4. Task-text-only lexical retrieval exposes two interpretable mismatch modes:
   goal-operation ambiguity and transformation/postcondition ambiguity.

We cannot yet claim:

1. Any task-success improvement from skills.
2. Synergy or negative interaction between retrieval and composition.
3. Faithful reproduction of SkillReranker, GraSP, or another paper.
4. A finalized Canonical Skill Interface.

## 6. First interface-friction ledger

| Observed issue | Boundary | Candidate information to test | Current status |
|---|---|---|---|
| Placement task ranks inspection skill first under lexical tie | Task → retriever | `goal_operation` (place / inspect / clean / heat / cool) | Observed selection mismatch |
| Heat task ranks cooling skill first because of destination wording | Task → retriever | `required_transformation`, desired postcondition | Observed selection mismatch |
| Raw observation is logged but intentionally excluded from C1 scoring | State → retriever | held object, appliance state, container openness, object location | Untested coverage gap |
| Adapter events show no drops/guesses | Retriever → adapter | No field added yet | Negative finding for this path |
| Fixed `look` cannot show how a selected skill changes actions | Adapter/executor → outcome | multi-step policy/action rationale | Attribution unavailable |

These are candidates for future tests, not schema fields to freeze now.

## 7. Recommended next experiment

Run a tightly scoped **state-aware retrieval intervention** before graph
composition:

1. Keep the five tasks, skill library, runner, executor interface, trace
   format, decoding policy, and action budget fixed.
2. Replace only `DebugLexicalRetriever` with a method that explicitly extracts
   `goal_operation` and `required_transformation` from task text.
3. Compare Top-1/Top-2 agreement against the same frozen mapping.
4. Log whether the added fields resolve the heat and placement cases without
   creating new errors.
5. Only after that, introduce a multi-step executor whose action selection can
   actually depend on selected skills.

This ordering isolates retrieval semantics before adding planner/executor
confounds.

## 8. Decisions requested from the advisor

1. Is the proposed core contribution—**empirically derived interfaces through
   controlled component swaps**—sufficiently focused for the project?
2. Should the next intervention prioritize a state-aware retriever or a
   multi-step flat executor, given that the former measures selection quality
   and the latter measures downstream utility?
3. Is ALFWorld-only P0.0 sufficient until the first retrieval/execution path
   is stable, or should a second environment be introduced earlier?

## 9. Four-slide meeting structure

### Slide 1 — Question and scope

- Problem: “skill modules” are often evaluated only inside their original
  pipeline.
- Question: can implementations be swapped without hidden coupling?
- Scope: ALFWorld P0.0, Retrieval × Execution vertical slice.

### Slide 2 — What is executable now

- Show the pipeline diagram above.
- Emphasize fixed tasks, native artifacts, explicit adapter events, and
  immutable raw traces.
- Say: “The harness is running; this is no longer only an architecture draft.”

### Slide 3 — Pilot evidence

- C0/C1: 5/5 complete pipeline runs each; 0 runner exceptions.
- C1: Top-1 3/5, Top-2 4/5 against frozen mapping.
- Heat trace: `fridge` causes cooling-skill selection; adapter did not lose
  information.

### Slide 4 — Interpretation and next decision

- Retrieval mismatch is real; task success is not yet evaluated.
- Candidate semantics: goal operation, required transformation, applicability
  state.
- Ask for decision on state-aware retrieval vs multi-step executor.

## 10. Short spoken update

“I narrowed the project from building a full skill lifecycle system to testing
whether components are actually interchangeable. I now have an ALFWorld
vertical slice with a fixed task set, six native-text skills, two swappable
retrieval configurations, an explicit adapter, and immutable episode traces.

On five `valid_unseen` tasks, both configurations complete the same pipeline
without changing the executor. The lexical retriever matches the expected skill
first on three tasks and includes it in Top-2 on four. The most useful failure
is a heat task where ‘fridge’ makes it retrieve cooling rather than heating.
Because the adapter logs no information loss, the issue currently appears to be
retrieval semantics, not data conversion.

I am not claiming task-performance gains yet: both runs replay a one-step
action. My next controlled experiment is to add explicit goal-operation and
transformation information to retrieval, then test whether those same cases are
resolved before adding a multi-step executor.”

