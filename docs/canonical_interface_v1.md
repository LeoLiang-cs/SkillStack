# Canonical Skill Interface v1 (Draft for Induction Review)

**Status:** draft. This document is the *empirical output* of SkillStack's
implementation-first, schema-later method. Every field below entered because
of concrete evidence from the friction ledger (F-numbers) or because ≥2
independent implementations required it — not by design fiat.

Induction rule (framework §4.2): a field enters the shared interface only if
**(a) at least two mechanism-different implementations need it**, or
**(b) it explains a reproduced component failure**.

## Tiers

| Tier | Meaning |
|---|---|
| **required** | ≥2 implementations need it and/or it explains a reproduced failure; must be present in a conforming skill payload |
| **optional** | Some implementations use it; safe to omit with recorded degradation |
| **extension** | Trace/portability semantics that implementations may add without breaking conformance |

---

## required

### `goal_operation`
- **Definition:** the task-level operation the skill implements, from a fixed
  vocabulary: `place`, `inspect`, `clean_then_place`, `heat_then_place`,
  `cool_then_place`, `place_two`.
- **Needed by:** `TaskSemanticRetriever` (field-match scoring);
  `SkillPlanExecutor` (task-family → plan skeleton); ReAct executor prompt
  (task statement).
- **Evidence:** F-01 (lexical tie ranked the inspection skill first for a
  placement task), F-09 (that mismatch produced a downstream task failure),
  R1 resolves both by matching the operation.

### `required_transformation`
- **Definition:** the object-state transformation the skill performs before
  placement, or `null`: `clean`, `heat`, `cool`.
- **Needed by:** `TaskSemanticRetriever` (scoring); `SkillPlanExecutor`
  (transform plan step).
- **Evidence:** F-02 (destination term `fridge` dominated lexical scoring so
  the heat task retrieved the cooling skill), F-08 (measured downstream
  failure), R1 resolves by transformation matching.

### `procedure` (ordered steps)
- **Definition:** the skill's execution procedure as an ordered list of
  steps, each with a short action-oriented sentence. Currently the static
  library carries this only as human prose under `## Procedure`; the
  interface requires a machine-readable ordered form.
- **Needed by:** `SkillPlanExecutor` (currently hard-codes per-skill plan
  skeletons — F-06), `StructuredReActExecutor` (E1, step injection and
  action grounding).
- **Evidence:** F-06 (executor hard-codes skill-id → plan skeleton because
  prose is not parseable), F-07 (appliance names hard-coded for the same
  reason), F-18 (flat prose injection was insufficient for strategy
  correction), E1's step grounding makes procedure consumption observable.

---

## optional

### `required_appliance`
- **Definition:** the appliance the transformation step needs
  (`microwave`, `fridge`, `sinkbasin`, `desklamp`), or `null`.
- **Needed by:** `TaskSemanticRetriever` (applicability check against the
  current room), `SkillPlanExecutor` (hard-coded today — F-07).
- **Evidence:** F-07, F-11 (random heat skill on bedroom tasks: no microwave
  exists → `plan_step_unavailable`).
- **Note:** derivable from `procedure` steps; keep separate only while
  procedure is still being standardized.

### `task_instruction` canonicalization
- **Definition:** one canonical task text used by all components. Today the
  environment's own `Your task is to:` sentence and the human annotation
  differ (F-13) and carry different information.
- **Evidence:** F-13 ("move a mug from the shelves…" vs "put a mug in desk";
  the executor used the env line).
- **Note:** a consistency requirement rather than a new field; the interface
  should name the canonical source.

### state applicability
- **Definition:** the preconditions a skill assumes about the environment
  state (held object, appliance state, container openness, object location).
- **Evidence:** F-03 (state → retriever coverage gap, untested),
  F-11 (appliance presence mismatch).
- **Note:** only partially exercised so far (R1 uses appliance presence);
  keep optional until a state-aware retriever or executor reproduces the gap.

---

## extension

### `grounded_step` (trace field)
- **Definition:** per-action mapping to the procedure step it implements.
- **Added by:** `StructuredReActExecutor` (E1).
- **Evidence:** F-18; enables action ↔ skill attribution.

### command-validity contract (portability requirement)
- **Definition:** the executor's assumption that the backend emits
  verbatim-admissible actions with high reliability; documented so backend
  swaps are risk-assessed (few-shot may be required).
- **Evidence:** F-15 (GLM zero-shot failure), F-19 (prompt variants),
  D3 (2-shot restores 97.96% validity → prompt coupling, not capability).

### adapter losslessness + selection semantics
- **Definition:** the retrieval→execution adapter preserves native payloads
  verbatim (F-04) and the executor uses only the Top-1 skill by default
  (F-14, F-20 cost-model caveats).
- **Evidence:** F-04, F-14.

---

## Rejected / deferred fields

| Candidate | Why deferred |
|---|---|
| `skill_id`-specific plan skeletons (as an interface field) | F-06 shows this is executor-side coupling; the fix is machine-readable `procedure`, not new fields |
| destination/receptacle type as a separate field | folded into `goal_operation` parameters |
| token-level similarity scores | lexical-only concern; not needed by R1 or executors |
| pricing / peak-谷 metadata | operational (F-20), not a skill interface concern |

## Open items for the induction review

1. Confirm `procedure` step granularity (sentence-level vs action-level).
2. Decide whether `required_appliance` stays independent or derives from
   `procedure`.
3. **Week3_2 factorial findings (added after pilot):** R1 ranks the expected
   skill first on all five frozen tasks (resolving F-01/F-02), yet on the 9
   pick_two tasks at a 20-step budget, R0 vs R1 showed **no success
   difference** (5/9 = 5/9) and only a small efficiency gain. Same for E0 vs
   E1. Interaction I ≈ 0 (approximately independent). Interpretation: at
   this budget, task success is dominated by the executor's general
   capability; selection quality only matters when the executor *depends* on
   the skill — which neither flat nor lightweight-structured injection
   forces. This is evidence **for** `procedure` (machine-readable ordered
   steps) as the lever that would make skill content binding, and it refines
   the claim in `goal_operation`/`procedure`: they are *needed by*
   implementations, but their downstream effect is currently masked by the
   measurement regime.
