# SkillStack Phase 2A — Second Advisor Update

**Status:** Phase 2A (skill-conditioned execution) complete; H1 gate passed.
**Environment:** ALFWorld text-only, `valid_unseen`, five fixed tasks.
**This update answers:** does the selected skill change the agent's actions
and task outcomes? Yes, measurably.

## 1. What changed since the first brief

The P0.0 pilot could only show *structural* interchangeability: both
configurations replayed one fixed `look` action, so task success was not
measurable and skill selection had no downstream consequence.

Phase 2A replaced the recorded fixture with a **deterministic multi-step
executor** (`SkillPlanExecutor`, hand-coded, no LLM) that derives its plan
skeleton from the selected skill's `Procedure` and records an
`action_rationale` for every action. Four skill-input conditions now share
this executor:

| Condition | Retriever | Role |
|---|---|---|
| C-no-skill | `NoSkillRetriever` | lower bound |
| C-random | `RandomSkillRetriever` (seeded per task) | wrong-skill control |
| C-lexical | `DebugLexicalRetriever` Top-2 | current retriever |
| C-oracle | `OracleSkillRetriever` (frozen mapping) | upper bound |

All four share the six native skills, the adapter, the frozen five tasks,
seed 42, step budget 50, and the JSONL trace format.

## 2. Results

| Condition | Task success | Episodes | Stop reasons (episodes) |
|---|---:|---:|---|
| C-no-skill | **1/5** | 5 | env-done 1; plan-completed 3; step-unavailable 1 |
| C-random | **1/5** | 5 | env-done 1; step-unavailable 2; step-budget 2 |
| C-lexical | **3/5** | 5 | env-done 3; plan-completed 2 |
| C-oracle | **5/5** | 5 | env-done 5 |

Per task:

| Task family | no-skill | random | lexical | oracle |
|---|---|---|---|---|
| `look_at_obj_in_light` | ✗ (no appliance step) | ✗ (heat skill) | ✓ | ✓ |
| `pick_and_place_simple` | ✓ | ✓ (random draw hit) | ✗ (light skill Top-1) | ✓ |
| `pick_clean_then_place_in_recep` | ✗ (no clean step) | ✗ (heat skill) | ✓ | ✓ |
| `pick_heat_then_place_in_recep` | ✗ (no heat step) | ✗ (light skill) | ✗ (cool skill Top-1) | ✓ |
| `pick_cool_then_place_in_recep` | ✗ (no cool step) | ✗ (light skill) | ✓ | ✓ |

## 3. H1 gate

> C-oracle must strictly outperform C-no-skill and C-random.

Result: oracle 5/5 vs no-skill 1/5 and random 1/5 — **PASSED**. The skill
channel causally affects outcomes under this executor, so retrieval metrics
now have a downstream target.

## 4. Most informative finding

The two week-1 retrieval mismatches now have **measured downstream failures**:

- **Heat task** ("Put the cooked green apple in the fridge"): lexical Top-1
  selects `skill_cool_then_place`. The executor cools the apple, places it in
  the fridge, and finishes its plan — but the goal requires the apple to be
  *hot*. Task fails after 15 steps.
- **Placement task** ("Move a mug from the shelves to the desk"): lexical
  Top-1 selects `skill_light_inspection` (the week-1 tie). The executor takes
  the mug, finds a lamp, and uses it — the mug is never moved. Task fails
  after 7 steps.

Because the adapter still logs zero drops/approximations/defaults, the
failure is attributable to **retrieval semantics** rather than data
conversion — closing the attribution gap the first brief left open (F-05).

## 5. New friction findings

The friction moved one boundary downstream: the adapter remains lossless,
but the **executor hard-codes knowledge about the six specific skill ids**
(plan skeletons, appliance names). A genuinely new native skill would be
ignored or mis-executed. This is the strongest candidate so far for interface
induction: procedure structure and `required_transformation` /
`required_appliance` fields. Full ledger:
[`w2_friction_ledger.md`](w2_friction_ledger.md).

## 6. Claims we can now make

1. Task success is now measurable, and skill selection causally changes it
   under a deterministic executor (oracle 5/5 vs no-skill/random 1/5).
2. Both known week-1 retrieval mismatches produce downstream task failures.
3. Adapter losslessness persists across all 20 week-2 episodes; the coupling
   is executor-side (skill-id-specific plan skeletons), not adapter-side.
4. The no-skill baseline is interpretable: it solves only the task whose plan
   equals the generic take-place skeleton.

## 7. Claims we still cannot make

1. Any result about LLM agents: the executor is hand-coded.
2. Statistical significance or generality: 5 tasks, raw counts only.
3. That `goal_operation` / `required_transformation` are *interface* fields:
   they may only be retriever-side features (Phase 2B will test this).
4. Canonical Skill Interface v1; acquisition/governance; graph composition.

## 8. Recommended next step: Phase 2B

With the causal chain closed, retrieval semantics can be studied with a
measurable target. Hold the executor, tasks, library, seed, and budget fixed,
and swap only the retriever:

1. R1: lexical + lemmatization/synonym normalization (tests whether the heat
   failure is just `cooked`↔`heat` coverage).
2. R2: task-semantic retriever that explicitly extracts `goal_operation` and
   `required_transformation` (tests whether these are the missing semantics).
3. R3: state-aware retriever reading raw observations (tests state
   applicability, week-1 F-03).
4. Expand beyond one instance per family and add meaning-preserving task
   paraphrases before drawing distributional conclusions.

The executor-side coupling finding (F-06/F-07) argues for, in parallel,
documenting what a *third* native skill would need to be consumed correctly —
the first concrete input toward Canonical Interface v1.

## 9. Decisions requested

1. Proceed with Phase 2B retrieval interventions on the fixed executor?
2. Model access for an LLM ReAct executor (the swap target for the executor
   slot): which backbone and budget? This remains the only hard blocker.
3. Task expansion: how many instances per family and how many paraphrases
   before interface-field decisions?

## 10. Four-slide structure

1. **Question**: does the selected skill change behavior and outcomes?
2. **Design**: deterministic executor + 4 conditions + action rationales.
3. **Evidence**: H1 table; the heat task now fails measurably; friction moved
   from adapter to executor.
4. **Decision**: Phase 2B retriever swaps; LLM executor swap needs model
   access.

## 11. Short spoken update

"Last time the pipeline was structurally swappable but the skills did not
affect anything, because the executor only replayed one `look` action. This
week I built a deterministic multi-step executor that actually reads the
selected skill, and ran four inputs through it: no skill, random skill,
lexical retrieval, and an oracle.

The oracle solves all five tasks; no-skill and random each solve one. The
skill channel now measurably changes outcomes, which closes the causal gap
from the first brief. The two retrieval mistakes we saw before — the heat
task retrieving a cooling skill, and the placement task retrieving a lamp
skill — now produce measured task failures, and the adapter still loses
nothing, so the problem is retrieval semantics, not data conversion.

The new friction is one boundary downstream: the executor hard-codes plan
skeletons for our six specific skills, so a genuinely new skill would not be
consumed correctly. That is the strongest evidence yet for what belongs in a
shared interface. Next I propose to hold the executor fixed and swap only the
retriever — synonym normalization, explicit task semantics, and state-aware
scoring — to test whether those two failures come from word coverage or from
missing interface fields. I still need a decision on model access for the LLM
executor."
