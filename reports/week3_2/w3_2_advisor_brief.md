# SkillStack Phase 3 — Fifth Advisor Update

**Status:** RQ3 2×2 factorial complete; Canonical Interface v1 drafted.
**Headline:** retrieval × composition are *approximately independent*
(I ≈ 0 on success); skill presence matters, skill identity does not yet.

## 1. What was built (Phase 3)

- **R1 `TaskSemanticRetriever`** (transparent heuristic): extracts
  `goal_operation`, `required_transformation`, destination, object; scores by
  field match + appliance applicability. Ranks the expected skill first on
  all five frozen tasks — resolving week-1's F-01/F-02 selection mismatches.
- **E1 `StructuredReActExecutor`** (lightweight): injects numbered Procedure
  steps + step grounding per action.
- **9 pick_two tasks** frozen and real-reset validated.
- Shared parsing module `task_semantics.py` (single source of truth).

## 2. Factorial results (9 pick_two × 20 steps, deepseek, seed 42)

| Cell | Retriever × Executor | Success | Mean steps | Cost |
|---|---|---|---|---|
| b00 | lexical × flat ReAct | **5/9** | 16.44 | $0.0334 |
| b10 | task-semantic × flat ReAct | **5/9** | 16.00 | $0.0293 |
| b01 | lexical × structured ReAct | **5/9** | 15.56 | $0.0319 |
| b11 | task-semantic × structured ReAct | **5/9** | 15.44 | $0.0278 |
| control | no-skill × flat ReAct | **3/9** | 18.22 | $0.0326 |

### Interaction (RQ3)

| Metric | I = Y11 − Y10 − Y01 + Y00 | Reading |
|---|---|---|
| Success rate | **0.0** | approximately independent |
| Mean steps | +0.32 | slightly sub-additive (~2%, noise-level) |
| Cost | ≈ 0 | independent |

## 3. Findings

1. **RQ3 answer at this resolution:** retrieval and composition are
   approximately independent — no synergy, no redundancy. Both factors have
   small *additive* efficiency effects (R1 and E1 each shave ~1 step and a
   few thousandths of a dollar per episode; b11 is 18% cheaper than b00),
   but they do not interact.
2. **Selection quality is not the binding constraint:** R1 fixes the
   week-1 selection mismatches, yet success is identical to lexical (5/9).
   At a 20-step budget, the executor does not *depend* on the skill text.
3. **Skill presence matters; skill identity does not yet:** control (no
   skill) 3/9 < all skill-bearing cells 5/9 — the Phase-2D signal persists
   under the factorial.
4. **Interface v1 drafted** (`docs/canonical_interface_v1.md`): three
   required fields (`goal_operation`, `required_transformation`,
   `procedure`), three optional, three extension — each with implementation
   and F-number evidence.

## 4. Claims we can now make

1. RQ3: on this regime, R0/R1 × E0/E1 are approximately independent on
   success; the framework's interaction measure is operational.
2. R1 (task semantics + applicability) is a mechanism-different second
   retriever and fixes the week-1 selection mismatches in selection terms.
3. The skill channel's effect (skill presence) reproduces across three
   independent pilots (2A deterministic, 2D tight budget, 3C factorial).
4. Interface v1 has an evidence chain: every required field is needed by ≥2
   implementations or explains a reproduced failure.

## 5. Claims we still cannot make

1. That better retrieval or structured injection improves *success* — both
   null at this budget (F-22/F-23).
2. Synergy or redundancy between retrieval and composition — I ≈ 0 (could be
   resolution-limited, not absence).
3. Statistical significance (n=9, single seed).

## 6. Recommended next step

The lever that should make skill *content* binding is `procedure`: the
induction says the current injection forms (flat and lightweight-structured)
are both weak (F-23). Options:

1. **Hard step enforcement** (E2): the executor may only act on the current
   procedure step's admissible commands — the strongest test of whether
   procedure content changes outcomes, and the natural experiment for the
   interface's `procedure` field.
2. **Deterministic step reader** (revisit week-2 `SkillPlanExecutor` but
   parsing `procedure` instead of hard-coded skeletons): proves
   machine-readable procedure works end-to-end.
3. **Raise resolution**: more pick_two instances (9 → 17) and a second
   budget (10 vs 30) to give RQ3's I a wider range.

## 7. Decisions requested

1. Proceed with E2 hard step enforcement as the next experiment (it is the
   only intervention likely to move success)?
2. Freeze `docs/canonical_interface_v1.md` now (with conformance checks), or
   wait until the E2 result can feed `procedure`'s final form?
3. Paper framing: is the current empirical core — RQ2 swaps, RQ3
   independence, ceiling finding, portability attribution, interface v1 —
   sufficient, or do we need the E2 success result first?

## 8. Four-slide structure

1. **Design**: two retrievers × two executors × 9 pick_two × 20 steps.
2. **Evidence**: 5/5/5/5 vs 3/9 control; I = 0; small efficiency main
   effects.
3. **Interface v1**: 3 required fields with evidence chains.
4. **Decision**: hard step enforcement / freeze interface / paper framing.

## 9. Short spoken update

"This week I ran the first real factorial: two retrievers and two executors,
four cells plus a no-skill control, nine two-object tasks at a twenty-step
budget. The answer is clean: all four cells score five of nine, the control
scores three of nine, and the interaction measure is exactly zero — so
retrieval and composition are approximately independent at this resolution,
with only small efficiency differences.

The task-semantic retriever fixes the selection mistakes we saw in week one
— it ranks the right skill first on every task — but that did not change
success, because the executor simply does not depend on the skill text at
this budget. The no-skill control still loses, so the skill channel is real,
but its *content* is not yet binding.

I also drafted the first version of the canonical interface: three required
fields — goal operation, required transformation, and ordered procedure
steps — each backed by implementation evidence and the failure ledger.

The next experiment that could actually move success is hard step
enforcement: making the executor act only on the current procedure step. If
procedure content changes outcomes there, it closes the loop for the
interface. Otherwise we have a solid independence result and a ceiling
finding to write up."
