# Week 4 Day 3 — Six-Paper Architecture Crosswalk

**Date:** 2026-08-25  
**Scope:** SkillReranker, GraSP, SkillCAT, SkillRL, GRASP, SkillOps  
**Evidence boundary:** mechanisms and experiment results attributed to papers
are paper-reported. Only released interfaces/source behavior explicitly marked
as such were inspected. No native benchmark result was reproduced here.

## 1. Cross-paper conclusion

The six methods share an eight-primitive control pattern:

1. **Observe:** collect task, trace, outcome, library or runtime evidence.
2. **Represent:** normalize it into typed skills, contracts, patches, states or
   graph nodes.
3. **Generate:** recall candidates or propose edits/plans.
4. **Structure:** align, rank, compile, group or stitch candidates.
5. **Assess:** score relevance, replay outcomes, verify execution or diagnose
   library health.
6. **Gate:** select, admit, reject, route, fall back or no-op.
7. **Act:** execute a plan or commit a library/policy change.
8. **Persist:** version artifacts, preserve evidence/failures and feed results
   into the next cycle.

This is a shared **analysis vocabulary**, not a universal implementation. A
paper-specific primitive remains swappable only when its input/output semantics,
authority and state are preserved through an explicit adapter.

## 2. Method-to-primitive crosswalk

| Paper | Observe | Represent | Generate | Structure | Assess | Gate | Act | Persist |
|---|---|---|---|---|---|---|---|---|
| SkillReranker | task + large skill pool | task states; parsed preconditions/effects | Top-30 recall | state-alignment graph; adaptive split | cross-encoder relevance/advance | ordered variable-size selection; discard non-advancing skills | inject selected skills into frozen host | parser cache, scores, split/discard trace |
| GraSP | task, state, memory, retrieved skills | typed predicates, schemas and skill invocations | retrieve skills; instantiate candidate nodes | compile executable dependency DAG | graph validation; node/output verification; confidence | execution mode, local repair, replan or ReAct fallback | topological execution | memory, confidence and repair trace |
| SkillCAT | multi-trajectory outcomes and source-task replay | causal evidence, skill patch, capability nodes/topology | CCE patch proposal | group/merge admitted patches; compile topology | AAE replay transition score | threshold admission; Top-k node route | commit evolved skill; assemble runtime skill text | evidence, versions, topology and route provenance |
| SkillRL | successful/failed trajectories; validation failures | hierarchical general/task-specific SkillBank | teacher distillation and update proposals | consolidate hierarchy; group RL rollouts | outcome reward and category success threshold | retrieve skills; trigger or skip evolution | SFT/GRPO policy update; append bank updates | bank snapshots coupled to policy checkpoints |
| GRASP | dev outcomes and earlier passing/failing examples | Markdown skill/edit schema and mechanism labels | grouped best-of-K ADD/MODIFY/REMOVE proposals | balanced held-out probe; forked candidate libraries | fresh baseline/candidate replay; fixes/regressions | hard regression gate, best candidate, revision or no-op | commit at most one edit per batch | full edit history; validation checkpoints; restore best |
| SkillOps | library, contracts, relations, logs and task state | `(P,O,A,V,F)` contracts; typed graph | task candidates or maintenance actions | constrained stitch; health/risk graph analysis | validation, compatibility and five health dimensions | plan/action choice; threshold skip/no-op | execute/repair plan or maintain library | action report, ID map, lineage and new library version |

## 3. Similar names that must not share an untyped port

| Term | Paper-specific meanings | Required distinction |
|---|---|---|
| `graph` | SkillReranker state-alignment graph; GraSP executable invocation DAG; SkillCAT capability-routing topology; SkillOps contract/relation graph | require `artifact_kind`, node/edge schema and executable flag |
| `repair` | GraSP runtime-local plan repair; SkillOps temporary task repair; SkillOps persistent operation repair; GRASP contrastive proposal revision | record mutation scope, authority, persistence and rollback behavior |
| `verify/assess` | relevance score; node/output verifier; task replay evaluator; reward; regression probe; library health rules | evaluator type, data split and decision authority must be explicit |
| `update` | SkillCAT patch admission; SkillRL policy plus additive bank evolution; GRASP bounded edit; SkillOps maintenance | preserve action algebra, checkpoint coupling and admissible no-op |
| `skill` | prompt text, parsed capability, executable typed operation, hierarchical rule, patchable file or software-like contract | adapters must log fields generated, dropped, defaulted or approximated |

## 4. Paper-native component boundaries

| Paper | Native method boundary | Independently visible internal ports | Portability evidence | First defensible test |
|---|---|---|---|---|
| SkillReranker | recall → parse → graph → split → rerank selector | recall and reranker are conceptually visible | no verified official source; internal swaps not demonstrated | reconstruct native selector, then change only host injection adapter |
| GraSP | retrieve/confidence → compile → execute → verify → repair/fallback | compiler, verifier, executor and repair are conceptually visible | no verified official source; strong semantic coupling | deterministic typed-plan smoke, then swap only host action adapter |
| SkillCAT | CCE → AAE → TTE evolution/deployment system | CCE, AAE and TTE are ablated modules | no verified official source; cross-implementation swaps not shown | reproduce composite path, then test AAE on preserved raw patches |
| SkillRL | distill → hierarchy → SFT → retrieve/GRPO → evolve | released distiller, retriever and additive updater | code exposes ports, but paper outcome entangles policy training | source-component smoke; full pipeline for paper-faithful baseline |
| GRASP | `Method.run(config, run_dir, Task)` self-improvement method | classifier, proposer, gate/revision, repository | official source has explicit method/task contracts and fork/version logic | native method baseline, then proposer-under-fixed-gate swap |
| SkillOps | paper: `library + logs → maintained library`; optional planner separate | contracts and five typed actions; partial sweep | official source implements primitives but not full paper loop/experiments | round-trip copied library, then raw-vs-maintained fixed-host cell |

GRASP's released whole-method boundary is the strongest **native fidelity
control** because it exposes a host-facing interface, retained rejects, fork
isolation and versioned changes. It is not the primary SkillStack plug-in
result. The first slot-level experiment uses the native method to establish a
reference, then freezes the GRASP gate/probe/evaluator and swaps only the
proposer. This internal boundary is a SkillStack experimental decomposition;
its portability is not already demonstrated by the paper.

SkillOps is the clearest library-maintenance boundary in the paper, but the
released implementation is partial. It is suitable for a source-component
test, not a claim of reproducing the full paper loop.

## 5. `R-A-D-C-L` assessment

### Keep

Keep the five labels as **coarse responsibilities**:

- `R` — representation/interchange contract;
- `A` — acquisition and skill evolution;
- `D` — discovery, selection and routing;
- `C` — composition and runtime execution;
- `L` — admission and ongoing lifecycle governance.

All six papers can declare one or more of these responsibilities. Composite
methods are allowed to occupy several ports; they should not be forced into a
single slot.

### Refine

Use these paper-derived internal primitives:

| Responsibility | Required internal sequence |
|---|---|
| `A` | `Observe/Evidence → Diagnose/Distill → Propose/Transform` |
| `D` | `Recall → Parse/Normalize → Align/Rank/Route` |
| `C` | `Compile/Bind → Execute → Verify → Repair/Replan/Fallback` |
| `L` | `Assess → Admit/Reject → Merge/Version → Maintain/Retire/Rollback` |

The sequence is an interface vocabulary; a method may combine or omit stages
when that behavior is declared.

### Revise

1. Treat `R` as a **cross-cutting typed artifact contract**, not merely another
   selectable algorithm. Every other responsibility reads and writes it.
2. Split `L` internally into **admission** of proposed skills and
   **maintenance** of existing library objects. GRASP/SkillCAT and SkillOps
   show that these have different evidence and mutation semantics.
3. Make evaluation authority a shared service contract. Relevance scorers,
   task evaluators, runtime verifiers and health rules are not interchangeable.
4. Make confidence, no-op, rejection, fallback and failure typed control
   outputs. They do not justify a sixth top-level responsibility yet.
5. Require composite-method manifests to state which internal stages are
   native, exposed, reconstructed or adapter-supplied.

**Verdict:** `KEEP` the five responsibilities, `REFINE` their internal
primitives, and `REVISE` the definitions of `R` and `L`. Do not add a sixth
top-level slot based on the current six-paper evidence.

## 6. Minimum port envelope

Every paper-derived component exchange should preserve at least:

- `artifact_kind`, `schema_version`, producer method/source version;
- task ID, split, environment state version and library ID/version;
- native input and raw component output before adapter conversion;
- candidate IDs, ordering, scores/confidence and decision/no-op reason;
- evaluator/verifier identity and evidence/trajectory/probe IDs;
- mutation action, parent version, removed/merged ID map and rollback target;
- fields dropped, synthesized, approximated or defaulted by the adapter;
- failure origin/type, retry/fallback behavior and retained error output;
- model, decoding, seed, token/call/latency/cost budget;
- compatibility/fidelity label and unchanged neighboring components.

## 7. Day-4 experiment design freeze

Day 4 must produce two linked matrices rather than one blended score table:

### Matrix A — paper-native reproduction

- one row per selected paper-native method/baseline;
- preserve each paper's benchmark, split, model, budget, metrics, ablations,
  transfer/stress axes and reporting gaps;
- label cells `reproduced`, `source_variant`, `reconstructed`, or `blocked`;
- establish a native baseline before making portability claims.

### Matrix B — single-slot component portability

- compare native host, explicit-adapter host and incompatible/no-op cells;
- fix task set, library, backbone, decoding, retry and evaluator within a swap;
- report execution compatibility, adapter loss/friction, performance delta,
  resource cost and localized failure;
- retain negative and rejected cells rather than averaging them away.

### Initial priority

1. GRASP native `Method.run()` only as the fidelity/artifact reference.
2. GRASP native proposer under a fixed native gate, then the released SkillRL
   additive updater through an explicit ADD-only adapter under the same gate;
   keep failure evidence, task, probe, evaluator and library start fixed.
3. SkillOps copied-library round trip and partial maintenance smoke, explicitly
   separated from the full paper method.
4. SkillRL additive-updater/retriever smoke as a source variant; do not call it
   SkillRL reproduction without SFT/GRPO and checkpoint coupling.
5. Keep SkillReranker, GraSP and SkillCAT exact-reproduction cells blocked until
   the missing source/artifact assumptions are resolved or declared.

## 8. Architecture decision gate

Day 3 resolves the architecture-reading question but does not authorize an
implementation rewrite. The refined port schema and the two Day-4 matrices
must be reviewed before code changes. Any first integration specification must
identify its fidelity label, frozen neighbors, adapter loss log, native
baseline and stop conditions.

## 9. Implemented A-slot assessment

The first cross-paper swap supports the proposed responsibility split. GRASP
and SkillRL candidates both reached the same unchanged repository and admission
contract through proposal-only adapters. No producer-specific rewrite was added
to Lifecycle Management.

Observed adapter asymmetry is useful evidence rather than an architecture
failure. GRASP already emits the target ADD fields, so its boundary is mainly
copy plus provenance. SkillRL emits a title/principle/trigger record, so action
synthesis, deterministic rename, Markdown construction and task-type tag
construction are explicit. These differences belong in the friction ledger;
they do not justify merging `A` and `L`.

The common proposal envelope should remain an experiment boundary rather than
a canonical skill representation. No additional universal fields are justified
until another swap requires them or a reproducible failure cannot otherwise be
explained.
