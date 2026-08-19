# Week 2 — Adapter-Friction Ledger v1

Week-1 ledger items F-01 to F-05 remain in
[`../week1/phase6_pilot_audit.md`](../week1/phase6_pilot_audit.md). Week 2 adds
the following entries from the skill-conditioned execution pilot. Week-1 items
F-01 and F-02 now have measured downstream consequences (see F-08 and F-09).

| ID | Boundary | Observed evidence | Classification | Candidate information to test later | Status |
|---|---|---|---|---|---|
| F-06 | Skill representation → executor | The executor did not parse the native `Procedure` text; it used a hard-coded skill-id → plan-skeleton table. A new native skill would be ignored or mis-executed. | Executor-side coupling to the six known skill ids | Machine-readable procedure structure (ordered steps, argument slots) in native payload or an adapter that extracts it | Structural dependency observed; no third skill library tested |
| F-07 | Skill representation → executor | Appliance names (`sinkbasin`, `microwave`, `fridge`, `desklamp`) are hard-coded per skill id. | Executor-side coupling to known task families | `required_appliance` field or explicit precondition on the transformation step | Structural dependency observed |
| F-08 | Task → retriever (downstream) | Heat task: lexical Top-1 selects `skill_cool_then_place`; the executor cools the apple and places it in the fridge; the goal requires `ishot(apple)` → **task failure** (15 steps, plan completed without success). | Week-1 F-02 now has a measured downstream consequence | `required_transformation`, desired postcondition | Reproduced selection mismatch AND downstream failure |
| F-09 | Task → retriever (downstream) | Placement task: lexical Top-1 selects `skill_light_inspection`; the executor takes the mug, searches for a lamp, and uses it → **task failure** (7 steps). | Week-1 F-01 now has a measured downstream consequence | `goal_operation` | Reproduced selection mismatch AND downstream failure |
| F-10 | No-skill → executor | Light task: the generic no-skill plan has no appliance step and no destination → `plan_step_unavailable` (9 steps). The no-skill baseline cannot express lamp goals at all. | Baseline expressiveness gap, not a failure claim | Goal structure beyond pick-place (inspect/toggle) | Observed; expected by design |
| F-11 | Random skill → executor | Random `skill_heat_then_place` on bedroom tasks: `go to microwave` is never admissible → `plan_step_unavailable`. Skill procedures assume appliances that may not exist in the room. | Applicability/precondition mismatch (room type) | `required_appliance` + environment capability check | Observed wrong-skill control failure |
| F-12 | Executor ↔ environment | Object search uses a hand-coded receptacle-type priority (surfaces before appliances before containers) and a per-plan-step budget of 24 actions. | Hand-coded exploration heuristic, reported as executor knowledge | None yet (a search policy is out of scope for interface induction) | Recorded for reproducibility |
| F-13 | Task record → executor | The executor binds object/destination/appliance names from the environment's own `Your task is to:` sentence, not the frozen human annotation ("move a mug from the shelves…" vs "put a mug in desk"). The human annotation carries extra hints (`shelves`) the executor did not use. | Two task descriptions with different information content | Which task text is the interface's canonical `task_instruction`? | Structural choice recorded; not a failure |
| F-14 | Retriever → executor | Top-2 information is dropped: only the Top-1 skill's plan skeleton is used; the second candidate and all scores are ignored by this executor. | Composition policy (first-skill-only) is executor-side | Multi-skill composition semantics | Structural choice recorded; not a failure |

## Observations carried from week 1

F-04 (adapter shows no drops/approximations/defaults) also held in all 20
week-2 episodes: the retrieval→execution adapter remains structurally
lossless, while the *executor* is where method-specific knowledge is
hard-coded. The friction is moving from the adapter boundary to the
representation boundary.
