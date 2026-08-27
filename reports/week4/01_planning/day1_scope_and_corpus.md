# Week 4 Day 1 — Scope, Paper Corpus, and Extraction Contract

**Date:** 2026-08-25  
**Status:** complete  
**Evidence boundary:** paper descriptions below are source-reading targets,
not independent reproductions of paper results.

**2026-08-26 correction:** the primary unit is one component in one fixed
`A/D/C/L` slot. Whole-method host transfer remains an auxiliary fidelity
control and cannot alone establish the project contribution.

## 1. Controlling scope

### Primary question

When the host and all neighboring slots are fixed, can independently designed
Skill Agent components replace one another inside the same responsibility
through an explicit adapter, while preserving runnable behavior and measurable
performance characteristics without rewriting adjacent algorithms?

### Operational meaning of plug-and-play

A component/host pairing receives one of five labels:

| Label | Meaning |
|---|---|
| `native` | The component is evaluated in its original paper stack. |
| `plug_and_play` | Only configuration/registration changes are needed. |
| `adapter_compatible` | An explicit boundary adapter is needed; unrelated host components remain unchanged. |
| `adjacent_rewrite_required` | The swap requires changes inside a neighboring component. |
| `semantically_incompatible` | The required information or execution semantics cannot be supplied without changing the method. |

`pipeline_complete` alone does not establish plug-and-play. The trace must also
show what the adapter changed and whether the host retained its original
behavioral contract.

### Role of performance

Task score, reward, success, steps, tokens, runtime, and cost are retained.
They answer whether behavior remains portable after a swap. They are not used
to establish a general claim that skills are beneficial.

## 2. Locked paper corpus

### 2.1 Main algorithm papers

These six papers receive complete algorithm cards and drive the architecture
and matrix design.

| Paper | arXiv | Primary algorithmic contribution | Initial SkillStack mapping | Method type | Source/code status for Day 1 |
|---|---|---|---|---|---|
| SkillReranker | [2607.06283](https://arxiv.org/abs/2607.06283) | Task/skill parsing, task-state execution graph, adaptive stage-wise reranking | Discovery/Selection, with task-decomposition dependencies | Composite selector | Paper/HTML available; code link not yet verified |
| GraSP | [2604.17870](https://arxiv.org/abs/2604.17870) | Memory-conditioned retrieval, typed DAG compilation, verified execution, local repair | Discovery + Composition/Execution | Composite orchestrator | Paper/HTML available; code link not yet verified |
| SkillCAT | [2606.13317](https://arxiv.org/abs/2606.13317) | Contrastive causal extraction, assessment-gated evolution, topology-aware execution | Acquisition + Lifecycle + Execution | Composite evolution system | Paper/HTML available; code link not yet verified |
| SkillRL | [2602.08234](https://arxiv.org/abs/2602.08234) | Experience distillation, hierarchical SkillBank, adaptive retrieval, recursive co-evolution | Acquisition/Evolution + Representation + Discovery | Composite learning system | Paper available; linked public repository found, reproduction boundary unverified |
| GRASP | [2605.29668](https://arxiv.org/abs/2605.29668) | Failure-driven proposal and held-out regression-aware admission | Acquisition/Proposal + Lifecycle/Admit | Proposer–gate system | Paper and linked public repository found; reproduction boundary unverified |
| SkillOps | [2605.13716](https://arxiv.org/abs/2605.13716) | Typed contracts, ecosystem graph, health diagnosis, maintenance actions | Representation + Lifecycle/Maintenance | Maintenance plug-in plus optional planner | Paper and public repository link found; reproduction boundary unverified |

### 2.2 Supporting papers

These papers test coverage, supply alternative experiment axes, or provide
comparison vocabulary. They do not automatically count as implemented slots.

| Paper | arXiv | Day-1 role | Why supporting rather than main this week |
|---|---|---|---|
| Graph of Skills | [2604.05333](https://arxiv.org/abs/2604.05333) | Structural-retrieval and library-size experiment reference | Overlaps the selection boundary; useful as an alternative or future implementation |
| SkillDAG | [2606.03056](https://arxiv.org/abs/2606.03056) | Typed-edge retrieval, edit-transfer, and intrinsic retrieval metrics | Extends retrieval with online graph evolution; used to stress-test boundaries |
| MUSE-Autoskill | [2605.27366](https://arxiv.org/abs/2605.27366) | End-to-end lifecycle and cross-agent transfer reference | Broad system used to check coverage rather than force one slot implementation |
| Dynamic Agent Skills Survey | [2607.10113](https://arxiv.org/abs/2607.10113) | Taxonomy, lifecycle vocabulary, reporting-gap checklist | Survey/reference source, not an algorithmic intervention |

## 3. Paper classification rules

1. A paper is a **component method** only when it exposes a boundary that can
   be invoked independently of its native host.
2. A paper is a **composite system** when its claimed method depends on several
   coupled stages. Its internal ablations do not automatically become
   independently swappable components.
3. A survey, schema, or taxonomy can validate coverage but cannot satisfy a
   dual-implementation requirement.
4. A local implementation is `paper_faithful` only when the paper's required
   mechanism, inputs, outputs, model calls, and evaluation controls are
   preserved. Otherwise it is `paper_inspired`.
5. Missing code or data is retained as a reproduction constraint, not filled
   with an unlabelled approximation.

## 4. Experiment-design axes to extract

Each main paper card must record the following before its design influences a
SkillStack matrix.

### Evaluation population

- benchmark and environment version;
- train/evolution, validation, seen, unseen, and held-out splits;
- task counts and task-family coverage;
- library source, library size, and skill-quality conditions.

### Agent and inference controls

- backbone/writer/user model roles;
- prompts, temperature, seed, number of runs, retry policy;
- environment-step and context/token budgets;
- whether required parsing, retrieval, verification, or maintenance calls are
  included in cost.

### Comparison structure

- native baseline and strongest matched baseline;
- one-at-a-time component ablations;
- cross-model, cross-domain, and OOD transfer;
- library-size, task-complexity, skill-quantity, and quality stress tests;
- writer-by-user or component-by-host matrices.

### Measurements

- paper-native task metric;
- steps/model calls/tokens/runtime/cost;
- intrinsic retrieval or verification metrics where applicable;
- regression, invalid-action, repair, rollback, and unresolved-failure rates;
- uncertainty reporting: seeds, variance, confidence intervals, or raw counts.

## 5. Preliminary architecture hypotheses to test

The current five responsibilities remain the starting hypothesis, not the
conclusion. Day 2–3 will test:

1. whether Representation is a cross-cutting artifact contract rather than an
   algorithm slot;
2. whether Acquisition/Evolution must expose evidence, proposal, and transform
   boundaries separately;
3. whether Discovery/Selection must expose recall, task decomposition,
   reranking, and routing as distinguishable primitives;
4. whether Composition/Execution must expose compile/plan, execute, verify,
   and repair boundaries;
5. whether Lifecycle must distinguish admission from ongoing maintenance,
   versioning, and rollback;
6. whether paper systems that span several responsibilities should be treated
   as composite components with multiple declared ports.

No architecture change is authorized by these hypotheses alone.

## 6. Day-2 queue

Day 2 will process the three papers closest to the current Retrieval ×
Composition stack, in this order:

1. **SkillReranker** — identify the smallest independently swappable selector
   and separate offline skill parsing from online task parsing and reranking.
2. **GraSP** — separate retrieval, DAG compilation, node verification,
   execution, and repair; identify which part is the actual composer.
3. **SkillCAT** — test whether CCE, AAE, and TTE are independent boundaries or
   one coupled evolution pipeline.

### Day-2 exit criteria

- Three cards contain paper-grounded pseudocode and native experiment design.
- Every stage has explicit inputs, outputs, state, invariants, and host
  dependencies.
- Every adopted experiment axis cites its paper section/table.
- Unknown or unavailable implementation details remain marked unknown.
- Each paper receives a provisional `component` or `composite` verdict with a
  short justification.
