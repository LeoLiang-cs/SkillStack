# Week 4 Day 2 — Algorithm Deep Dive and Plug-in Boundary Audit

**Date:** 2026-08-25  
**Status:** complete  
**Scope:** SkillReranker, GraSP, SkillCAT  
**Evidence boundary:** all mechanisms and numbers attributed to papers are
paper-reported. No native paper result has been reproduced in SkillStack.

## 1. Day-2 deliverables

- [x] Verify current paper versions and primary text.
- [x] Check arXiv/Hugging Face metadata and exact-title search for official
  repositories.
- [x] Complete the SkillReranker algorithm card.
- [x] Complete the GraSP algorithm card.
- [x] Complete the SkillCAT algorithm card.
- [x] Extract ordered mechanism, inputs, outputs, state, invariants, native
  dependencies, experiments, unknowns, and failure behavior.
- [x] Classify each method as component or composite and propose the smallest
  faithful initial swap boundary.
- [x] Record provisional implications for `R-A-D-C-L` without changing the
  architecture.

Cards:

1. [`algorithm_cards/skillreranker.md`](../02_paper_analysis/algorithm_cards/skillreranker.md)
2. [`algorithm_cards/grasp.md`](../02_paper_analysis/algorithm_cards/grasp.md)
3. [`algorithm_cards/skillcat.md`](../02_paper_analysis/algorithm_cards/skillcat.md)

## 2. Source and reproduction status

| Paper | Version used | Method/experiment evidence read | Verified official repository | Current fidelity status |
|---|---|---|---|---|
| SkillReranker | arXiv v1, 2026-07-07 | Method §4, Experiments §5, Limitations §7, prompt appendix headings | None linked/found in verified metadata and exact-title search | Exact reproduction blocked; reconstruction may be possible with declared gaps |
| GraSP | arXiv v1, 2026-04-20 | Architecture §2, Experiments §3, Limitations §6, Algorithms 1–4, ablation appendix | None linked/found in verified metadata and exact-title search | Exact reproduction blocked by missing code, typed libraries, memory, prompts/verifiers, full configs |
| SkillCAT | arXiv v2, 2026-07-29 | Complete Method/Algorithm 1, experiments, ablation and analyses | None linked/found in verified metadata and exact-title search | Exact reproduction blocked by missing code, prompts, artifacts, replay/topology implementations |

“None linked/found” is a bounded search statement, not proof that code does not
exist.

## 3. Mechanism-level comparison

| Dimension | SkillReranker | GraSP | SkillCAT |
|---|---|---|---|
| Native purpose | Select an adaptive ordered skill set | Compile and execute a typed skill DAG with repair | Evolve skill content selectively and route relevant content at deployment |
| Main lifecycle position | Online selection plus offline skill parsing | Online retrieval, planning, execution, verification, repair | Offline evidence/proposal/admission/merge plus online routing |
| Main persistent artifacts | Cached skill precondition/effect parses | Typed library, successful memories, confidence history | Base/evolved skill versions, patch evidence/scores, topology/node bodies |
| Structural artifact | Task states as nodes; candidate skills as alignment edges | Skill invocations as executable nodes; typed dependency edges | Capability nodes plus compact metadata/dependency topology |
| Final boundary output | Ordered, deduplicated, variable-size skill set | Task outcome plus verified execution/repair trace | Evolved skill and task-specific assembled runtime skill |
| Native fallback/gate | Discard non-advancing candidates; no typed global fallback | Confidence route, compile fallback, local repair, replan, ReAct | Non-contrastive extraction fallback and score-threshold rejection |
| Provisional type | Composite selector | Composite orchestrator | Composite evolution/deployment system |

## 4. Critical semantic distinction: three different “graphs”

The three papers cannot be joined by matching the word “graph.” Their node and
edge semantics differ:

| Paper artifact | Nodes | Edges | Executable? | Correct SkillStack role |
|---|---|---|---|---|
| SkillReranker execution graph | Parsed task states | Candidate skills aligned as possible state advances | No; used for stage detection and selection | `D` selection artifact |
| GraSP DAG | Instantiated skill invocations plus source/sink | `state`, `data`, `order` dependencies | Yes; topological execution with node verification and repair | `C` compiled plan/runtime artifact |
| SkillCAT topology | Capability sections/sub-skills | Procedural or tool-use dependencies in metadata | No action execution; used to select prompt context | `D/C` routing-and-assembly artifact |

Therefore an adapter must declare `artifact_kind` and semantic version, not
merely accept a generic `graph`. Converting between these artifacts is a method
change unless the transformation and lost information are explicit.

## 5. Shared abstract structure

At a high level, all three systems repeat a six-part pattern:

1. **Normalize evidence/artifacts:** parse tasks, skills, trajectories, states,
   contracts, or capability metadata.
2. **Propose candidates:** recall skills, instantiate graph nodes, or generate
   patches.
3. **Build structure:** align to task stages, compile a typed DAG, or construct a
   capability topology.
4. **Score or verify:** cross-encoder relevance, graph validity/node verifier,
   or replay outcome transition.
5. **Gate and route:** choose stage skills, select execution/fallback/repair,
   or admit patches and route capability nodes.
6. **Emit a typed artifact plus provenance:** ordered skills, verified
   execution trace, or evolved/routed skill.

This is useful as a common analysis vocabulary, not evidence that the same
implementation can serve all three. “Normalize,” “verify,” and “graph” have
paper-specific semantics.

## 6. Smallest faithful initial boundaries

| Paper | Faithful boundary for first implementation | Narrower future boundary to test | Why the narrow boundary is not yet established |
|---|---|---|---|
| SkillReranker | Full offline-parse + online recall/parse/graph/split/rerank selector | Recall model or cross-encoder as configurable ports | Removing parsing, graph edges, or splitting changes the claimed method |
| GraSP | Retrieval/confidence through compile/execute/verify/repair/fallback | Compiler + verified executor + local repair | Compiler depends on typed library, memory evidence, verifier and fallback semantics |
| SkillCAT | Full CCE→AAE→TTE pipeline | Separate CCE, AAE, and TTE ports | Paper ablates stages but does not demonstrate cross-implementation substitution |

The conservative rule for Week 4 is: first reproduce the native composite
boundary; only then test whether an internal port remains semantically valid
when swapped.

## 7. Provisional architecture assessment

No top-level architecture change is made on Day 2. The evidence currently
supports **keeping** `R-A-D-C-L` as coarse responsibilities and **refining** its
internal primitives:

| Responsibility | Paper-derived internal primitives to test |
|---|---|
| `R` Representation | Versioned artifact kind; native payload; pre/effect and schema contracts; evidence/patch provenance; graph/topology semantics; loss log |
| `A` Acquisition/Evolution | Evidence collection → causal extraction → proposal/transform |
| `D` Discovery/Selection | Recall → parse/normalize → align/structure → rerank/route |
| `C` Composition/Execution | Compile/plan → bind → execute → verify → repair/replan/fallback |
| `L` Lifecycle | Assess → admit/reject → merge/version → maintain/rollback |

Two cross-boundary signals also require explicit treatment:

- **Confidence/fallback control:** GraSP's retrieval confidence changes the
  execution mode at `D→C`.
- **Evidence/provenance:** SkillCAT's trajectory and replay evidence travels
  across `A→L`; losing it makes admission unauditable.

Whether these deserve new top-level responsibilities remains a Day-3 question.

## 8. Paper-derived experiment axes retained for Day 4

### SkillReranker contribution

- backbone × benchmark split;
- matched frozen host and skill pool;
- reward/success, environment steps, tokens, selected-skill count;
- parsing/graph/splitting ablations;
- separate fixed Top-1 and Top-2 controls, rather than only their average.

### GraSP contribution

- backbone × environment;
- flat skills versus typed compilation;
- task complexity, skill quantity, skill quality, and failure type;
- local repair versus equal-budget global replan;
- recovery, fallback, graph validity, steps/model calls, and failure
  localization.

### SkillCAT contribution

- author × user × initialization × domain;
- evolution/held-out separation and OOD/cross-family transfer;
- trajectory count/cost, replay transition bucket, admission regression;
- route budget, selected context tokens, router type, and full-skill control.

### SkillStack additions required by the plug-and-play question

- native / plug-and-play / adapter-compatible / adjacent-rewrite-required /
  semantically-incompatible cell label;
- adapter inputs/outputs, defaulted/dropped/approximated information;
- unchanged neighboring components and changed code/config surface;
- component raw output, typed failure origin, adapter failure, and host failure;
- native-versus-swapped performance delta under matched controls.

## 9. Day-3 questions

The SkillRL, GRASP, and SkillOps reading must resolve or sharpen:

1. Does `A` consistently split into evidence collection and proposal/transform,
   or is that split specific to SkillCAT?
2. Does `L` require separate admission, maintenance, versioning, rollback, and
   retirement ports?
3. Is `R` best modeled as a swappable algorithm responsibility or as a
   cross-cutting typed artifact contract used by all other components?
4. Are confidence, verification, and fallback part of their producer/consumer
   components, or a distinct control plane?
5. Which narrower boundaries are explicitly implemented or ablated in released
   code, rather than inferred from paper diagrams?
6. Can every composite declare multiple typed ports without pretending that
   its internal stages are independently portable?

## 10. Day-2 completion verdict

Day 2 is complete against its exit criteria. Three paper-grounded cards now
record mechanisms, native experiments, invariants, unknowns, and provisional
plug-in boundaries. The architecture remains unchanged pending all six cards.
No implementation code or experiment result was changed or produced today.
