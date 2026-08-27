# Algorithm Card — SkillOps

## A. Identity and evidence

- **Paper:** *SkillOps: Managing LLM Agent Skill Libraries as Self-Maintaining
  Software Ecosystems*
- **arXiv:** 2605.13716, v1, submitted 2026-05-13
- **Authors/year:** Hongji Pu, Xinyuan Song, Liang Zhao (2026)
- **Paper:** <https://arxiv.org/abs/2605.13716>
- **Official repository:** <https://github.com/Hik289/SkillOps>
- **Source snapshot:** commit `c80b05246369c0b9d82a293390ca5add675c516a`,
  inspected 2026-08-25
- **Evidence read:** problem setup, Method §3, Algorithms 1–5, Experiments
  §§4–5, Limitations §7 and Appendices A–K; repository graph, planner,
  maintenance actions/engine, CLI, tests and artifact notes.
- **Released assets verified:** small Python API, 12-skill demo library, planner,
  maintenance actions, smoke tests and CLI.
- **Evidence gaps:** the inspected repository does not include paper-scale
  ALFWorld grids, 200–2000-skill libraries, table-generation scripts/raw runs,
  CGPD implementation, or a full automatic maintenance loop matching Algorithm
  4. Exact paper-result reproduction is therefore blocked by the current
  public snapshot.

## B. Claimed contribution

- **Problem:** growing skill libraries accumulate persistent technical debt—
  redundancy, stale/broken operations, incompatible interfaces, missing
  validators and propagated risk.
- **Claimed unit:** a method-agnostic library-time maintenance plug-in, with an
  optional typed task-time planner.
- **New mechanism:** five-field Skill Contracts; a hierarchical graph of
  internal contracts and typed cross-skill relationships; five-dimensional
  health diagnosis; typed maintenance actions; optional risk propagation.
- **Not claimed:** universal benefit for every downstream agent. The paper
  reports method-conditional effects and possible conflict with task-time
  self-repair.

## C. Native pipeline context

- **Upstream:** raw skill library, typed contracts/relations or contract-mining
  inputs, execution/utility/failure logs and maintenance thresholds.
- **Downstream:** any retrieval/planning host can consume the maintained
  library; the optional Graph-of-Graphs planner can also execute plans.
- **Persistent state:** versioned skill contracts, external edges, health/risk
  scores, trace buffer and maintained library.
- **Task-time loop:** match, precondition filter, stitch, insert
  validators/adapters, execute, local repair, log unrecovered failures.
- **Library-time loop:** diagnose health, optionally propagate graph risk,
  merge/repair/retire/add validators/add adapters, emit maintained library.
- **Update clock:** per task for planner trace; periodic or threshold-triggered
  maintenance sweep outside downstream task execution.

## D. Algorithm anatomy

### Inputs

- Library `L=(S,R)`.
- Per-skill contract `s=(P,O,A,V,F)`: preconditions, operation sequence,
  produced artifact type, validators and known failure modes.
- Typed relations: dependency, compatibility, redundancy, alternative; source
  also represents lineage.
- Task/current state for the optional planner.
- Recent usage/failure/validation logs and health/action thresholds.
- Optional CGPD propagation coefficient and convergence threshold.

### State and intermediate artifacts

- Internal contract graph for each skill; external graph-of-graphs.
- Candidate skills/relevance/precondition results and constrained plan.
- Inserted validator/adapter nodes, plan trace and local repair result.
- Per-skill utility, redundancy, compatibility, failure-risk and validation-gap
  measurements; aggregate library health.
- Local and propagated risk scores.
- Typed maintenance decision/action, mutation report and new library snapshot.

### Ordered task-time mechanism / paper pseudocode

1. Score skills by a lexical/semantic mixture for the task.
2. Keep high-scoring skills whose preconditions hold in the current state.
3. Stitch a plan only across dependency edges that also satisfy compatibility.
4. Insert a validator for an unverifiable non-terminal artifact when possible.
5. Insert a typed adapter node when dependency exists but artifact/input types
   do not match; accept it only if its output satisfies the consumer type.
6. Execute the plan and validate outputs.
7. On a recoverable failure, substitute an alternative neighbor or repair the
   failed skill locally; re-execute the affected plan.
8. Buffer unresolved failure evidence for library-time maintenance.

### Ordered library-time mechanism / paper pseudocode

1. Compute health change from the library and accumulated traces; skip the pass
   when change is below the maintenance trigger.
2. For each skill compute the five local health dimensions and local risk.
3. Optionally run CGPD until convergence, propagating upstream risk along
   dependency edges.
4. Merge redundant contract-equivalent skills.
5. Repair high-risk operations from execution feedback.
6. Retire obsolete/low-utility skills and remove incident edges.
7. Add missing validators, including preventive validators for propagated risk.
8. Add typed conversion adapter skills for incompatible dependencies.
9. Rebuild/validate graph relations and return maintained library `L'` plus
   action report.

### Outputs and failure behavior

- **Primary plug-in output:** maintained library `L'`.
- **Optional task-time output:** instantiated action plan and execution trace.
- **Auxiliary:** graph, health/risk vector, action decisions/counts, validator
  issues, adapter/repair provenance, timing/cost.
- **Failure/no-op:** stable health skips maintenance; unmatched task yields
  empty/fallback plan; unrecoverable failures enter diagnosis buffer; actions
  with insufficient evidence should be retained as unapplied decisions.
- **Confidence/evidence:** health metrics and typed inconsistency/failure logs;
  paper rule-based conditions, not a calibrated probabilistic confidence.

### Invariants

- Every dependency transition must be artifact/precondition compatible or have
  a validated adapter.
- Non-terminal outputs should be locally verifiable; gaps remain explicit.
- Merge requires equivalent exposed contract signatures.
- Retirement removes incident relations without corrupting indexes.
- Repair changes the intended operation but preserves/revalidates its exposed
  contract and lineage.
- Maintained output must remain readable by the unchanged downstream host.
- Library-time and task-time actions must be distinguished; a temporary local
  repair cannot silently masquerade as a persistent library update.

## E. Released-source audit

- `SkillContract`, `Skill`, `SkillLibrary` and typed `Edge` are explicit public
  data structures; serialization and edge rebuilding are tested.
- Each maintenance action is directly callable with a concrete signature:
  merge, repair, retire, add-validator and add-adapter.
- `MaintenanceEngine.sweep()` automatically performs signature-based merge,
  optional usage retirement and validator inheritance, then rebuilds edges.
- **Paper/source gap:** automatic repair and adapter decisions are not performed
  by `sweep()`; callers must supply domain-specific operations.
- **Paper/source gap:** no `run_maintenance(L)->L'` function exists under that
  name. The engine mutates a library in place and returns an action-count report.
- **Paper/source gap:** CGPD and full five-dimensional diagnosis are not present
  in the inspected package despite Algorithm 5 in the paper.
- **Paper/source gap:** `_stage2_stitch()` in the released planner selects one
  domain candidate rather than executing the paper's constrained multi-skill
  dependency/compatibility graph search.
- The public tests establish 12-skill demo/API behavior, not the paper's
  ALFWorld performance or scale experiments.

## F. Candidate plug-in boundary

- **Responsibilities:** Representation (`R`) and Lifecycle maintenance (`L`);
  optional planner spans Discovery/Composition (`D/C`).
- **Method type:** the **library-time maintenance layer is a genuine component
  boundary**; the paper's full standalone Task-Time + Library-Time system is a
  composite.
- **Smallest claimed plug-in:** raw library + logs → maintained library +
  maintenance report, with downstream agent unchanged.
- **Smallest released working unit:** individual typed maintenance actions or
  the partial rule-based `MaintenanceEngine.sweep()`.
- **Required adapter input:** a loss-accounted conversion from native skill to
  `(P,O,A,V,F)`, stable skill IDs, relation construction, utility/failure logs
  and serialization back to the host's library format.
- **Required output:** versioned maintained artifacts, action provenance,
  removed/merged ID mapping and explicit dropped/defaulted fields.
- **Neighbors fixed:** downstream retriever/planner/executor, task set, original
  retrieval settings and prompt injection path.
- **`paper_inspired` conditions:** assigning contracts from guessed fields
  without loss logs; using only deduplication while claiming five-dimensional
  maintenance; using current partial planner as the paper Algorithm 3; or
  claiming CGPD from graph construction alone.

## G. Native experimental design

**Paper provenance:** setup §§4.1–4.2; standalone Table 1; plug-in Table 2;
token/cost Table 3/Figure 3; scale Table 4/Figure 4; ablations Table 5;
dataset/source Appendix B; matched-information/scale Appendices H–J; CGPD
Appendix K.

- **Environment:** ALFWorld; 185 trials per cell in token appendix.
- **Library:** 200-skill main setting; 200–2000 scale stress. Clean source is
  229 SkillsBench skills across 88 tasks/58 categories, extended with synthetic
  redundant/stale/missing-validator/missing-artifact/wrong-interface/
  over-specialized variants.
- **Runs/statistics:** three seeds; mean±SD and Wilson 95% CI for main success.
- **Baselines:** ReAct/full library, BM25-only, dense-only, hybrid retrieval,
  GoS-style graph, LLM Skill Planner, SkillWeaver and other reported variants.
- **Plug-in matrix:** seven fixed downstream baselines × raw/maintained library
  at 200 skills; measures task-success delta with downstream code unchanged.
- **Scale/quality:** library size and degradation density from 15% to 90%;
  balanced-composition and gold/blind argument controls.
- **Metrics:** task success, subgoal success, task tokens/calls, library-time
  calls/tokens/cost/latency, maintenance action counts/precision, scale slope,
  CGPD delta.
- **Key ablations:** remove task-time loop; remove library-time loop; remove
  internal/external graph levels; remove CGPD; remove individual actions;
  matched information (`pddl_params`) and retrieval-k sensitivity.
- **Important control issue:** SkillOps sometimes receives structured/gold
  PDDL-style arguments unavailable to baselines. Paper appendices include blind
  and all-gold probes; our portability matrix must make this information axis
  explicit rather than average across it.

## H. Paper-reported findings

- Table 1 reports 79.5% success at 200 skills, about 8.9 points above the
  strongest listed baseline.
- Table 2 reports improvements concentrated in retrieval-heavy hosts: roughly
  +1.00 BM25, +1.12 dense and +2.90 hybrid; planner/self-repair hosts are
  smaller, flat or potentially conflicting.
- Across 35 token cells, 24 reportedly decrease and seven increase; maintenance
  is not token-improving in every cell.
- At 2000 skills/90% degradation, SkillOps reports 80.5% and a lead above 31
  points; this relies partly on the synthetic degradation design.
- Table 5 reports the largest ablation drop without task-time planning
  (79.5→15.7); without library maintenance drops to 71.9. Adapters, validators
  and repair matter most; CGPD is smaller.
- Limitations: structured/gold arguments; half-synthetic ALFWorld-centric
  library; rule-based loop misses semantic conflict; CGPD initially has limited
  effect because validators are not fully consumed in plan selection.

These results are paper-reported and not reproducible from the inspected source
snapshot alone.

## I. SkillStack architecture and integration verdict

- SkillOps is the strongest evidence that `R` is a cross-cutting typed artifact
  contract as well as a conversion boundary, not merely one selectable
  algorithm.
- It validates splitting `L` into
  `Diagnose → Decide → Apply → Version/Map IDs → Rollback/Audit` and separating
  admission of new skills from ongoing maintenance of existing ones.
- It also confirms that task-time repair (`C`) and persistent library repair
  (`L`) are semantically different even when both use the word `repair`.
- **Architecture verdict:** keep `R-A-D-C-L`; revise the definition of `R` as a
  cross-cutting contract layer and refine `L` into admission and maintenance
  subinterfaces. No sixth top-level responsibility is necessary yet.
- **Fidelity status:** released maintenance primitives are
  `paper_faithful_possible`; full paper SkillOps is `blocked` by missing
  paper-scale implementation/artifacts.
- **First safe smoke test:** convert a copied SkillStack library subset into
  explicit contracts, run only released merge/add-validator actions, round-trip
  it back, and verify ID mapping/loss log without changing the original.
- **First true plug-in test:** fixed retriever/host with raw versus maintained
  copies, measuring adapter loss, candidate-set change and task metrics. Do not
  include the optional SkillOps planner in the same first cell.
