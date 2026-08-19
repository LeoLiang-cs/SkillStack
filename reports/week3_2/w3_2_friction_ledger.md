# Week 3_2 — Friction Ledger (Phase 3 additions)

Week-1 (F-01…F-05), week-2 (F-06…F-14) and week-3 (F-15…F-21) entries remain
in their respective files. Phase 3 adds:

| ID | Boundary | Observed evidence | Classification | Candidate information to test later | Status |
|---|---|---|---|---|---|
| F-22 | Retriever quality ↔ downstream success | `TaskSemanticRetriever` (R1) ranks the expected skill first on all five frozen tasks (resolving F-01/F-02), yet on the 9 pick_two tasks at a 20-step budget, R0 and R1 produced identical success (5/9 = 5/9) and only ~1 step / ~$0.004 per episode efficiency difference. | Selection quality is not the binding constraint in this regime: the executor does not depend on the skill text | Make skill content binding on the executor (procedure steps, per F-06/F-23); measure selection utility where the executor must use the skill | Observed null main effect |
| F-23 | Skill injection form ↔ executor | Lightweight structured step injection (E1, numbered Procedure steps + grounding) showed no success effect vs flat prose (5/9 = 5/9), a small efficiency gain (~1 step/episode), and produced `grounded_step` trace fields. Flat-text vs structured consumption remains unresolved at this budget. | Prompt-level skill consumption is weak for both forms | Harder step locking, or a deterministic executor that reads steps (week-2 skill-plan style) | Observed; consistent with F-18 |
| F-24 | RQ3 interaction | I = Y11 − Y10 − Y01 + Y00 = 0 on success rate (all cells 5/9); ≈ 0 on cost; +0.32 steps on mean steps (slightly sub-additive efficiency, ~2%, noise-level). | Retrieval × composition are approximately independent at this resolution; no synergy or redundancy observed | Wider budgets / harder tasks / more instances to raise resolution | Observed |
| F-25 | Skill channel (re-confirmed) | Control (no-skill) cell: 3/9 vs all four skill-bearing cells 5/9. The skill channel effect first seen in Phase 2D persists under the factorial. | Skill presence matters; skill identity does not (yet) | See F-22 | Observed |

## Notes

- F-22/F-23 together are the strongest evidence yet for the induction's
  `procedure` field: the mechanism that makes skill *content* matter to an
  LLM executor is not flat prose, and not lightweight step lists — it is
  either hard step enforcement or a deterministic reader.
- The adapter remains structurally lossless (F-04) across all 45 factorial
  episodes.
