# Week 4 Day 3 — Six-Paper Crosswalk and Architecture Verdict

**Date:** 2026-08-25  
**Status:** complete  
**Scope:** SkillRL, GRASP, SkillOps deep dive plus the six-paper crosswalk  
**Evidence boundary:** paper numbers are paper-reported; source audits describe
the inspected snapshots. No benchmark result was reproduced in SkillStack.

## 1. Day-3 deliverables

- [x] Verify paper versions, primary text and official repositories for
  SkillRL, GRASP and SkillOps.
- [x] Complete three algorithm cards with ordered mechanism/pseudocode, inputs,
  outputs, intermediate state, invariants and failure behavior.
- [x] Extract native benchmarks, controls, metrics, experimental axes and key
  ablations.
- [x] Audit paper/source agreement and reproduction blockers.
- [x] Map all six papers to shared primitives without collapsing their
  paper-specific semantics.
- [x] Assess `R-A-D-C-L` as keep/refine/revise.
- [x] Freeze the architecture and experiment-design inputs required by Day 4.

Artifacts:

1. [`algorithm_cards/skillrl.md`](../02_paper_analysis/algorithm_cards/skillrl.md)
2. [`algorithm_cards/grasp_gate.md`](../02_paper_analysis/algorithm_cards/grasp_gate.md)
3. [`algorithm_cards/skillops.md`](../02_paper_analysis/algorithm_cards/skillops.md)
4. [`architecture_crosswalk.md`](../02_paper_analysis/architecture_crosswalk.md)

## 2. Source and fidelity status

| Paper | Version/source inspected | Main source finding | Current fidelity status |
|---|---|---|---|
| SkillRL | arXiv 2602.08234 v1; official source `8e66726` | retriever and additive updater exist; source updater does not implement paper-described refinement/admission/rollback | full composite is possible with substantial compute; frozen-host or updater-only use is paper-inspired/source-variant |
| GRASP | arXiv 2605.29668 v3; official source `9d7d125` | explicit `Method.run()` plug-in interface, proposal/gate cycle, forked libraries and version history | strongest native fidelity reference; proposer/gate split selected for slot-level testing |
| SkillOps | arXiv 2605.13716 v1; official source `c80b052` | contracts/actions and partial sweep exist; full health, CGPD, planner and paper-scale artifacts are absent | released primitives testable; full paper reproduction blocked |

## 3. Direct answer to the Day-2 questions

1. `A` consistently benefits from
   `Observe/Evidence → Diagnose/Distill → Propose/Transform`; SkillRL and GRASP
   confirm that this is not unique to SkillCAT.
2. `L` must distinguish proposal admission from ongoing maintenance, and make
   versioning, retirement and rollback explicit.
3. `R` is best modeled as a cross-cutting typed artifact/interchange contract,
   while representation transforms may still be selectable components.
4. Confidence, verification, rejection and fallback are typed control/evidence
   outputs shared across boundaries, not a new sixth responsibility yet.
5. GRASP provides the clearest released whole-method **native reference**.
   SkillRL exposes a narrower additive updater for the first proposer swap.
   SkillOps exposes maintenance primitives but not the full paper loop.
6. Composite methods may declare multiple ports; no internal stage receives a
   portability claim merely because it appears as a box or ablation.

## 4. Architecture verdict

- **KEEP:** five coarse responsibilities `R-A-D-C-L`.
- **REFINE:** internal sequences for evidence/proposal, discovery/routing,
  compile/execute/verify/repair, and admission/maintenance.
- **REVISE:** make `R` cross-cutting; split `L` admission versus maintenance;
  type evaluator authority and fallback/no-op outputs.
- **DO NOT ADD:** no sixth top-level responsibility is supported yet.

The architecture remains frozen until the Day-4 matrices and first integration
specification are reviewed.

## 5. Paper-derived experiment axes added for Day 4

### SkillRL

- task family and ID/OOD search split;
- hierarchy, raw-trajectory, cold-start SFT and dynamic-evolution ablations;
- policy checkpoint × bank version coupling;
- success/score, convergence, context length and library growth.

### GRASP

- proposal grouping, candidate count, probe size and regression budget;
- no-grouping, no-regression-budget, fixes-only, append-only and no-gate
  ablations, including matched-compute controls;
- admitted/rejected/no-op rate, fixes/regressions, library size, calls/cost;
- writer/executor model, in-domain/OOD, transfer direction and seed.

### SkillOps

- raw versus maintained library under an unchanged downstream host;
- library size, degradation density and information availability;
- task-time/library-time loop, graph level, CGPD and individual-action
  ablations;
- success/subgoal, tokens/calls, maintenance cost/precision and scale slope.

## 6. Day-4 frozen inputs

Day 4 will build:

1. a **paper-native matrix** that preserves each method's own experimental
   design and fidelity status; and
2. a **single-slot component portability matrix** measuring runnability,
   adapter friction/loss, performance delta, cost and localized failure under
   matched controls. Whole-method host transfer is auxiliary.

The complete GRASP interface provides the native reference, not the primary
plug-in claim. The first primary component experiment freezes its gate, probe,
evaluator and task/library state, then compares the native proposer with the
released SkillRL additive updater through an explicit ADD-only adapter.
SkillOps follows as a library-maintenance composition. Missing-code methods
remain blocked/reconstructed rather than silently approximated.

## 7. Day-3 completion verdict

Day 3 is complete. All six main papers now have extracted mechanisms, I/O,
intermediate artifacts, invariants, experiment axes, ablations, fidelity limits
and candidate boundaries. The crosswalk supports a refinement—not a wholesale
replacement—of the current architecture. No implementation code or experiment
result was changed today.
