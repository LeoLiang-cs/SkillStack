# Phase 4 (Week 4) — Paper-Derived Plug-and-Play Protocol

> **归档说明（2026-08-27）：** 这是研究目标修正与实验完成前的原始计划，
> 用于保留决策过程。当前目标以
> `../01_planning/decisions/week4_research_goal_corrected_zh.md` 为准；文中提到的
> Day 4、Day 5 独立过程总结已被正式协议、矩阵和最终总结替代并删除。

**Status:** Day 5 complete on 2026-08-26. The corrected primary intervention is
a **single-slot cross-paper component swap** with all neighboring components
frozen. The historical-trace dry-run and proposer-swap specification are
complete; contract/fixture implementation remains gated by review. Whole-method
host portability stays a native/auxiliary control, not the main contribution.

## 0. Meeting-locked decisions

1. SkillStack does **not** treat "whether skills are useful" as the primary
   research question.
2. The primary target is component **plug-and-play behavior**: whether a
   paper-derived component can replace another implementation in the same
   declared slot through an explicit adapter while all neighboring algorithms
   remain unchanged.
3. Performance remains necessary, but it is interpreted as a compatibility
   and portability measurement rather than a standalone skill-utility claim.
4. Performance matrices must inherit their experimental axes, controls, and
   metrics from the main papers whose components are selected for composition.
5. Before changing the current architecture, the project will derive common
   algorithmic structure from the paper corpus and audit whether the current
   five responsibilities are adequate.
6. The primary experimental unit is one component inside one declared
   `A/D/C/L` slot. A complete paper system may establish a native baseline but
   does not by itself satisfy the cross-paper plug-and-play objective.

## 1. Phase-4 research question

> When all neighboring components, tasks, library, evaluator and budgets are
> fixed, can a component derived from paper A replace another implementation
> in the same SkillStack slot through an explicit adapter, without rewriting
> adjacent algorithms, and which behavior, cost and failure properties remain
> portable?

The result of a cell may be successful execution, conditional compatibility,
or an informative incompatibility. A higher task score is not required for a
cell to be scientifically useful.

## 2. Primary evidence

Phase 4 will report four evidence families:

1. **Interchangeability:** whether the swap runs and whether unrelated code
   changes are required.
2. **Interface friction:** information read, generated, dropped, approximated,
   defaulted, or represented by method-specific adapter branches.
3. **Performance portability:** task metric, environment steps, tokens, model
   calls, latency, and estimated cost under a matched host configuration.
4. **Failure localization:** whether incompatibility originates in
   representation, retrieval, planning, execution, verification, maintenance,
   or the adapter.

## 3. Explicit non-goals

- No new no-skill-versus-skill-utility study as the main experiment.
- No prompt tuning whose only objective is to increase task success.
- No claim that the current heuristic retriever or structured prompt is a
  reproduction of SkillReranker or GraSP.
- No full Cartesian product across all papers.
- No use of whole-agent or whole-method migration as the primary plug-and-play
  result; it is a fidelity/host-portability control.
- No architecture rewrite before the paper-to-structure crosswalk is reviewed.
- No silent removal of failed cells, missing outputs, or incompatible methods.

## 4. Week plan

| Day | Work | Exit artifact |
|---|---|---|
| 1 | Freeze scope, corpus, extraction schema, evidence status, and Day-2 queue | `day1_scope_and_corpus.md`, `algorithm_card_template.md` |
| 2 | Deep-read SkillReranker, GraSP, and SkillCAT | Three completed algorithm cards |
| 3 | Deep-read SkillRL, GRASP, and SkillOps; map all six to common primitives | Three cards plus `architecture_crosswalk.md` |
| 4 | Derive paper-native and SkillStack plug-in matrices; freeze controls and failure labels | `performance_matrix_protocol.md` |
| 5 | Dry-run the matrix schema on retained traces; specify the first `A`-slot proposer swap under a fixed GRASP gate | `matrix_dryrun.md` and proposer-swap integration specification |
| Weekend | Audit claims and prepare the Chinese advisor update | Week-4 advisor brief |

## 5. Day-1 checklist

- [x] D1.1 Record the meeting decisions as the controlling scope.
- [x] D1.2 Freeze the Phase-4 research question and interpretation of
  performance.
- [x] D1.3 Lock six main algorithm papers and four supporting papers.
- [x] D1.4 Classify each paper as a component method, composite system, or
  taxonomy/reference source.
- [x] D1.5 Define one algorithm-card template shared by all papers.
- [x] D1.6 Define the experimental axes that must be extracted for the
  performance matrices.
- [x] D1.7 Freeze the Day-2 reading order and exit criteria.

## 6. Gates

- **G0 Scope:** no primary conclusion is phrased as "skills are useful."
- **G1 Source fidelity:** algorithm claims come from the paper or released
  source; simplified local variants are labelled `paper_inspired`.
- **G2 Boundary clarity:** every selected component has explicit inputs,
  outputs, persistent state, invariants, and native host dependencies.
- **G3 Matrix comparability:** within one comparison, task set, library,
  backbone, decoding, budget, retry, and failure handling are fixed.
- **G4 Failure retention:** incompatible cells and raw component outputs are
  retained and classified rather than omitted.
- **G5 Architecture change:** no responsibility or slot boundary is changed
  until the cross-paper mapping is reviewed.

## 6.1 Day-2 checklist

- [x] D2.1 Verify versions, primary text, and official-code status for
  SkillReranker, GraSP, and SkillCAT.
- [x] D2.2 Complete the SkillReranker algorithm card.
- [x] D2.3 Complete the GraSP algorithm card.
- [x] D2.4 Complete the SkillCAT algorithm card.
- [x] D2.5 Extract inputs, outputs, state, ordered mechanism, invariants, and
  native dependencies.
- [x] D2.6 Recover native benchmarks, controls, metrics, ablations, transfer,
  stress axes, and known reporting gaps.
- [x] D2.7 Classify component versus composite and identify the smallest
  faithful initial plug-in boundary.
- [x] D2.8 Summarize provisional effects on `R-A-D-C-L` and freeze Day-3
  questions without changing the architecture.

**Day-2 artifacts:** `algorithm_cards/skillreranker.md`,
`algorithm_cards/grasp.md`, `algorithm_cards/skillcat.md`, and
`day2_summary.md`.

## 6.2 Day-3 checklist

- [x] D3.1 Verify versions, primary text, official repositories and source
  snapshots for SkillRL, GRASP and SkillOps.
- [x] D3.2 Complete the SkillRL algorithm card.
- [x] D3.3 Complete the GRASP algorithm card and distinguish it from GraSP.
- [x] D3.4 Complete the SkillOps algorithm card.
- [x] D3.5 Extract ordered mechanism, inputs, outputs, intermediate state,
  invariants, failure behavior, experiment axes and key ablations.
- [x] D3.6 Audit paper/source mismatches and reproduction blockers.
- [x] D3.7 Map all six papers to common primitives while preserving distinct
  graph, repair, verification and update semantics.
- [x] D3.8 Produce the `R-A-D-C-L` keep/refine/revise verdict.
- [x] D3.9 Freeze the two-matrix design and first-candidate priorities for Day 4.

**Day-3 artifacts:** `algorithm_cards/skillrl.md`,
`algorithm_cards/grasp_gate.md`, `algorithm_cards/skillops.md`,
`architecture_crosswalk.md`, and `day3_summary.md`.

## 6.3 Day-4 checklist

- [x] D4.1 Build Matrix A for paper-native reproduction/fidelity evidence.
- [x] D4.2 Build Matrix B for selected single-slot component swaps; retain
  whole-method host transfer only as an auxiliary cell.
- [x] D4.3 Trace every adopted axis, control, metric and ablation to a main
  paper algorithm card.
- [x] D4.4 Freeze tasks, libraries, hosts, models, budgets, evaluators,
  neighboring components and split constraints inside matched comparisons.
- [x] D4.5 Separate execution status, compatibility class, paper fidelity and
  performance portability.
- [x] D4.6 Define field-level adapter loss and severity without a blended score.
- [x] D4.7 Define failure codes and retain blocked, rejected, no-op, partial and
  failed cells.
- [x] D4.8 Specify raw artifacts, paired aggregation and statistical reporting.
- [x] D4.9 Freeze the Day-5 historical-trace dry-run and first-integration gates.

**Day-4 artifacts:** `performance_matrix_protocol.md`,
`matrix_a_paper_native.csv`, `matrix_b_plugin_portability.csv`, and
`day4_summary.md` (later superseded and removed). The 2026-08-26 scope correction is recorded in
`week4_research_goal_corrected_zh.md`.

## 6.4 Day-5 checklist

- [x] D5.1 Audit five retained Week-3.2 runs without new model/environment calls.
- [x] D5.2 Verify task pairing, trace completeness, adapter coverage and
  outcome/failure reconstruction.
- [x] D5.3 Separate immutable cell records from reusable comparison edges.
- [x] D5.4 Record available, derivable and missing matrix fields without
  backfilling historical traces.
- [x] D5.5 Freeze the GRASP proposer versus SkillRL updater boundary.
- [x] D5.6 Define the ADD-only adapter, unsupported semantics and fixed gate.
- [x] D5.7 Require disjoint proposal/probe data and record the released-source
  first-batch variant.
- [x] D5.8 Freeze metrics, raw artifacts, fidelity labels and stop conditions.

**Day-5 artifacts:** `matrix_dryrun.md`,
`matrix_dryrun_comparisons.csv`,
`integration_spec_grasp_skillrl_proposer_swap.md`, and `day5_summary.md`
(later superseded and removed).

## 7. Week-4 completion criteria

1. Six main algorithm cards are complete and source-grounded.
2. The four supporting papers have explicit roles and cannot silently become
   experimental implementations.
3. A paper-native experiment-design matrix records provenance for every
   adopted experimental axis.
4. A SkillStack plug-in matrix specifies cell-level compatibility and
   portability measurements.
5. The current five-responsibility architecture receives a keep/refine/revise
   assessment backed by all six main papers.
6. The first paper-derived integration has a faithful native baseline and a
   controlled **single-slot** swap specification before implementation begins.
