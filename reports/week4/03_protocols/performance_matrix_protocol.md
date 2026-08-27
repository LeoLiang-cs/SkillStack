# Week 4 Day 4 — Paper-Derived Performance Matrix Protocol

**Date:** 2026-08-25  
**Status:** corrected and frozen for Day-5 dry-run on 2026-08-26  
**Research target:** single-slot, cross-paper component interchangeability;
whole-method host portability is only a native/auxiliary control  
**Evidence boundary:** paper-native axes below are extracted from the six
algorithm cards. Paper-reported results remain unverified by SkillStack.

## 1. Decision this protocol supports

With the host and every neighboring component fixed, replace one implementation
inside one declared slot with a component derived from another paper and
determine:

1. whether the component can run through a declared adapter;
2. whether unrelated neighbors remain unchanged;
3. what information the adapter preserves, creates, approximates or loses;
4. which native performance, efficiency and failure properties remain; and
5. whether failure belongs to the component, representation, adapter, host,
   evaluator, data or infrastructure.

Task performance is a required outcome, but it is interpreted only after
compatibility and fidelity. An incompatible or rejected cell is retained as a
result rather than removed from the matrix.

## 2. Two linked matrices

### Matrix A — paper-native reproduction

Matrix A establishes what the paper's method, source release or declared
reconstruction does in its own boundary. Its purpose is to prevent a swapped
variant from becoming the only available reference.

Running a complete native method satisfies Matrix A; it does not by itself
satisfy the primary slot-level interchangeability question.

One row is one `method × benchmark/split × model × seed × ablation` cell. It
must record the source paper/section for every inherited axis and one of these
fidelity labels:

| Label | Meaning |
|---|---|
| `paper_faithful` | The paper algorithm, assets, split and required controls are preserved. |
| `source_variant` | Released source behavior differs materially from the paper and the difference is named. |
| `reconstructed` | Missing implementation is rebuilt from text with every unresolved assumption logged. |
| `paper_inspired` | Only a mechanism idea is retained; no paper-reproduction claim is permitted. |
| `blocked` | Required code, artifact, authority or configuration is unavailable. |
| `not_applicable_local` | SkillStack-native diagnostic/control component with no paper-fidelity claim. |

Matrix A may include blocked rows. A paper-reported number may be attached as a
reference field but can never populate an observed-result field.

### Matrix B — single-slot component portability

Matrix B primarily compares two component implementations inside one frozen
slot/host. A whole method across native and adapter hosts may appear only as an
auxiliary host-portability cell.
One row is one fully specified execution cell. Every swap must name:

- one component boundary and its native input/output;
- one host and the exact target port;
- the adapter and its allowed scope;
- the comparison cell;
- all frozen neighbors;
- method-specific information made available;
- the inherited paper axes and metrics; and
- the expected raw artifacts and stop conditions.

Matrix B does not run the full six-paper Cartesian product. Cells enter only
when they answer a boundary question and have a native or source-variant
reference.

**Day-5 schema amendment:** cell records are immutable execution nodes;
comparisons are separate directed edges. One cell may participate in several
slot comparisons without duplicating the underlying run.

## 3. Matrix A — six-paper axis registry

The detailed values and provenance live in the linked cards; this table
records which axes are controlling for future cells.

| Method | Boundary | Native evaluation axes | Required controls | Key ablations | Metrics that must survive into a swap | Current status |
|---|---|---|---|---|---|---|
| [SkillReranker](../02_paper_analysis/algorithm_cards/skillreranker.md) | full recall/parse/graph/split/rerank selector | ALFWorld/ScienceWorld seen-unseen; three backbones; fixed 67,884-skill pool; `K=30`; max 30 steps | same frozen agent and skill pool; separate Top-1 and Top-2 cells | no parsing; no graph edge; no adaptive split | reward/success, steps, execution tokens, selected count, discarded candidates | `blocked` exact; `reconstructed` only with assumptions |
| [GraSP](../02_paper_analysis/algorithm_cards/grasp.md) | retrieval/confidence through typed DAG execution and repair | four environments; eight backbones; complexity, skill quantity/quality, failure type | same library/memory; equal-budget global-replan control; fixed verifier/fallback | no DAG; no local repair; no confidence routing | success/reward, steps, graph validity, recovery/fallback, calls/tokens/cost | `blocked` exact; `reconstructed` only |
| [SkillCAT](../02_paper_analysis/algorithm_cards/skillcat.md) | CCE→AAE→TTE composite | writer×user×initialization×domain; evolution/held-out/OOD; trajectory count; route budget | exact evaluator; source-task clone/replay; fixed author/user/base skill/tools | no CCE; no AAE; no TTE; each module alone | held-out accuracy, replay transition bucket, admission regression, route/context cost | `blocked` exact; `reconstructed` only |
| [SkillRL](../02_paper_analysis/algorithm_cards/skillrl.md) | distillation→hierarchy→SFT→GRPO→evolution | environment/task family; search ID/OOD; policy×bank checkpoint; library growth and training step | hierarchy and retrieval budget fixed; SFT/reference policy; category split and reward fixed | no hierarchy; raw trajectories; no SFT; no dynamic evolution | success/score, convergence, context length, library size, policy/bank version | full pipeline potentially `paper_faithful`; updater-only is `source_variant` |
| [GRASP](../02_paper_analysis/algorithm_cards/grasp_gate.md) | failure grouping→best-of-K proposals→probe gate→versioning | benchmark, writer/executor model, ID/OOD, seed, probe size, `K`, regression budget, transfer direction | fresh same-probe baseline; proposal batch excluded from probe; validation/test frozen; capacity fixed | no grouping; no regression budget; fixes-only; append-only; no gate K4/K1; matched compute | fixes, regressions, accepted/rejected/no-op, library size, task score, calls/tokens/cost | strongest released native reference; exact first-batch source is `source_variant` until the probe is disjoint |
| [SkillOps](../02_paper_analysis/algorithm_cards/skillops.md) | library maintenance plug-in; optional planner separate | host×raw/maintained; library size; degradation density; gold/blind information; scale | downstream host/retriever unchanged; same library copy and task set; planner excluded in first maintenance cell | no task loop; no library loop; graph levels; no CGPD; individual actions; retrieval `k` | task/subgoal success, tokens/calls, maintenance action precision/cost, scale slope | primitives are `source_variant`; full paper loop `blocked` |

## 4. Matrix B — selected portability program

### 4.1 Priority cells

| Cell ID | Priority | Component and boundary | Host / comparison | Purpose | Entry status |
|---|---:|---|---|---|---|
| `B-GRASP-NATIVE-CONTROL` | P0-control | GRASP complete `Method.run()` | official task interface | establish native artifacts and proposer/gate reference; not the primary plug-in result | planned prerequisite |
| `B-A-GRASP-PROPOSER` | P0 | native GRASP proposer | fixed native GRASP gate/probe/evaluator | establish the `A`-slot reference under frozen `L` | planned after native control |
| `B-A-SKILLRL-UNDER-GRASP` | P0 | released SkillRL additive updater used as an ADD-only proposer | same fixed GRASP gate/probe/evaluator; compare with `B-A-GRASP-PROPOSER` | first cross-paper single-slot swap; expose unsupported MODIFY/REMOVE and evidence differences | planned; adapter specification required |
| `B-SKILLOPS-ROUNDTRIP` | P1 | released contracts and typed maintenance actions | copied `alfworld_static_v0`; no task execution | measure conversion loss, ID mapping and round-trip safety | planned source-component smoke |
| `B-L-SKILLOPS-AFTER-GRASP` | P1 | released SkillOps maintenance primitives | GRASP-produced library, then frozen SkillStack retriever + ReAct executor | test cross-paper sequential composition without changing downstream `D/C` | planned after round trip |
| `B-GRASP-SS-TASK` | P2-supporting | unchanged GRASP `Method.run()` | SkillStack ALFWorld Task adapter | auxiliary whole-method host-portability test | deferred until the slot-level P0 specification is frozen |
| `B-SKILLRERANKER-SS` | P2 | reconstructed full selector | frozen SkillStack ReAct host | test `D` portability and variable-size ordered output | blocked by source/library/parser reconstruction |
| `B-GraSP-SS` | P2 | reconstructed typed compiler/executor/repair | SkillStack ALFWorld environment adapter | test `C` portability | blocked by typed library, verifier, memory and source gaps |
| `B-SKILLCAT-AAE` | P2 | reconstructed replay admission gate | preserved candidate patches and source-task clones | compare admission semantics with GRASP gating | blocked by source/prompts/replay artifacts |

`GRASP` denotes the regression-aware skill proposer. `GraSP` denotes the typed
graph orchestration method. Cell IDs preserve this distinction.

### 4.2 Slot-level candidate map

| SkillStack responsibility | Native/current control | Paper-derived candidates | First swap rule |
|---|---|---|---|
| `R` contract | native Markdown payload + canonical-interface fields | SkillOps contracts; SkillRL hierarchy; typed GraSP schema | preserve native payload and emit a field-level loss log before any task run |
| `A` evidence/proposal | no current learning implementation | GRASP proposer; SkillCAT CCE; SkillRL distiller/updater | proposal and admission must remain separate ports |
| `D` discovery/route | lexical and task-semantic retrievers | SkillReranker; SkillRL hierarchical retriever; SkillCAT TTE router | same task/library/Top-k budget; retain order, scores and discard reasons |
| `C` composition/execution | flat/structured ReAct; deterministic plan executor | GraSP compiler/executor/repair | freeze retrieval and host action vocabulary; report graph and fallback states |
| `L` admission/maintenance | static library | GRASP gate; SkillCAT AAE; SkillOps maintenance | freeze evaluator and data split; retain rejections/no-op and version mapping |

## 5. Matched-control contract

Within every direct comparison, the following fields are immutable unless the
field itself is the declared experimental axis:

1. task IDs, order, split and task text source;
2. environment/backend version and action vocabulary;
3. initial library bytes/hash, ID namespace and starting version;
4. host model, system prompt, tool set and skill-injection location;
5. writer/teacher/evaluator model and prompt when applicable;
6. decoding, random seed, concurrency and cache policy;
7. step, token, call, wall-time, cost, retry and timeout budgets;
8. retrieval `k`, route/context budget and candidate capacity;
9. evaluator/verifier implementation and success definition;
10. failure retention, exception handling and stopping rules;
11. dev/probe/validation/test membership and access permissions; and
12. neighboring components, their configurations and source revisions.

If a paper method requires additional information unavailable to its
comparison, do not silently provide it. Run separate declared
`information_axis` cells such as `blind`, `adapter_inferred`, `structured`, or
`gold`, following SkillOps' matched-information controls.

Learning/evolution methods must never read held-out test outcomes. GRASP probe
examples must be earlier/out-of-sample relative to the proposal batch;
SkillCAT admission uses source-task replay; SkillRL evolution follows its
declared training/validation source variant. These are distinct split
contracts and cannot be normalized into a generic `validation` label.

## 6. Outcome hierarchy

Results are interpreted in this order. A later layer cannot erase a failure in
an earlier one.

### Layer 1 — execution status

| Status | Meaning |
|---|---|
| `completed` | Required raw outputs and terminal state were written. |
| `partial` | Some outputs exist, but the declared boundary did not finish. |
| `failed` | Execution started and terminated with a retained error/failure. |
| `blocked` | Execution was not started because a prerequisite was absent or unsafe. |
| `not_run` | Planned but not yet attempted. |

### Layer 2 — compatibility class

| Class | Meaning |
|---|---|
| `native` | Component runs inside its released/native boundary. |
| `plug_and_play` | Only a generic declared adapter/configuration is added; neighbors are unchanged. |
| `adapter_compatible` | A method-specific adapter transforms data, but no neighboring algorithm is rewritten. |
| `adjacent_rewrite_required` | Running requires changing another responsibility's logic or hidden method-specific branches there. |
| `semantically_incompatible` | Required meaning/authority cannot be preserved even if schemas can be made to parse. |
| `undetermined` | Evidence is insufficient; never coerce this to compatible. |

Compatibility is not inferred from task success. A successful task with an
adjacent rewrite remains `adjacent_rewrite_required`.

### Layer 3 — fidelity

Use the Matrix-A fidelity vocabulary. Fidelity describes relation to the paper;
compatibility describes relation to the host. They are independent fields.

### Layer 4 — performance portability

Report the swapped cell and its paired reference side by side:

- absolute task metric and paired difference;
- environment actions/steps;
- prompt, completion and total tokens;
- model/teacher/writer/evaluator call counts;
- latency and estimated cost;
- component-specific outcomes; and
- failure distribution.

Do not create a single weighted “portability score.” Success, cost and adapter
friction expose different trade-offs and remain separate.

## 7. Metrics

### 7.1 Cross-component required metrics

| Family | Required fields |
|---|---|
| boundary execution | attempted/completed count; schema-valid outputs; explicit no-op/reject count; missing raw-output count |
| integration surface | adapters added; adjacent components changed; method-specific branches; configuration-only versus code change |
| information friction | fields read/generated/dropped/approximated/defaulted; native payload retained; round-trip equality; warning count |
| task performance | task success/reward/subgoal as applicable; paired delta against the declared reference |
| efficiency | environment steps, tokens, calls, latency, cost; maintenance/training cost separate from task-time cost |
| reliability | failures by primary/secondary code; retries; fallbacks; invalid actions; indeterminate count |
| provenance | component/source commit; adapter version; task/library/checkpoint/evaluator IDs; seed/model/decoding |

Information friction is reported as a ledger, not only a count. Each lossy
event receives one severity:

- `lossless`: copied or renamed without semantic change;
- `reversible`: transformed and exactly recoverable;
- `lossy_nonrequired`: native information lost but not required by this cell;
- `lossy_required`: information needed by the method/host was guessed or lost.

Every generated field also records `transform_kind ∈ {copy, rename, construct,
synthesize}`. `generated` alone is not evidence of semantic invention; the
Week-3.2 adapter, for example, reversibly constructed execution context from
retained native candidates.

Any `lossy_required` event prevents `plug_and_play`; it usually yields
`adapter_compatible`, `adjacent_rewrite_required`, or
`semantically_incompatible` depending on scope and behavior.

### 7.2 Component-specific metrics inherited from papers

| Component family | Metrics |
|---|---|
| selector/router | candidate count, selected count/order, discarded count/reasons, context tokens, task metric, steps |
| compiler/executor | compile/graph validity, bound arguments, node verification, repair/replan/fallback rate, recovery by failure type |
| proposer/admission | candidates, valid proposals, fixes, regressions, accepted/rejected/no-op, admission rate, probe errors |
| evolution/training | policy checkpoint × bank version, category success, convergence step, library growth, context length |
| maintenance | action counts/precision, merge/retire/repair/validator/adapter counts, ID mapping, health/risk if implemented, maintenance cost |

## 8. Failure taxonomy

Every incomplete, failed, blocked, rejected and no-op cell remains in the raw
record. Store one `primary_failure_code` and zero or more secondary codes.

| Code family | Meaning and examples |
|---|---|
| `DATA.*` | missing paper assets, task/library mismatch, corrupted artifact |
| `SPLIT.*` | proposal/probe overlap, held-out leakage, unavailable clone/replay authority |
| `R.*` | schema, artifact-kind, version, ID, provenance or round-trip failure |
| `A.*` | missing evidence, distillation/proposal parse failure, unsupported action algebra |
| `D.*` | recall/parse/rank/route failure, empty candidates, invalid ordering/cardinality |
| `C.*` | compile/bind/graph/execute/verify/repair/replan/fallback failure |
| `L.*` | assess/gate/admit/commit/version/retire/rollback failure |
| `ADAPTER.*` | dropped/defaulted/approximated required field, semantic conversion loss, hidden branch |
| `HOST.*` | adjacent host contract mismatch, invalid action vocabulary, unsupported state/tool |
| `EVAL.*` | evaluator disagreement, unavailable metric, wrong authority or inconsistent baseline |
| `INFRA.*` | API, timeout, quota, dependency, hardware or source revision failure |
| `BUDGET.*` | call/token/step/cost/time budget exhausted |

Examples of terminal labels include `D.EMPTY_CANDIDATES`,
`C.GRAPH_INVALID`, `C.VERIFIER_REJECTED`, `L.REGRESSION_REJECTED`,
`L.NOOP_NO_FAILURES`, `ADAPTER.LOSSY_REQUIRED`, `SPLIT.PROBE_LEAKAGE`, and
`BUDGET.MAX_STEPS`. Rejection and no-op are not infrastructure failures; they
are valid method outputs with explicit codes.

## 9. Raw-record and aggregation rules

### Required run artifacts

Each run directory must retain:

1. immutable run manifest;
2. append-only cell/episode JSONL;
3. unmodified component raw inputs and outputs or stable content-addressed
   references to them;
4. adapter events and field-level loss ledger;
5. component state before/after, including library and policy versions;
6. summary generated only from raw records; and
7. source/config/environment hashes or exact revisions.

Existing SkillStack traces already provide task IDs, retriever/executor names,
selected native payloads, adapter events, actions, observations, rewards,
success, stop reason, seed and LLM cost records. Day 5 will test which new
fields can be derived and which require future instrumentation.

### Aggregation

- The unit of analysis is the task/episode unless the paper's native unit is a
  proposal batch, library sweep or policy checkpoint.
- Compare the same task IDs pairwise. Never compare means from different task
  populations as a direct swap effect.
- Report raw numerator/denominator for binary outcomes and Wilson 95% intervals
  when sample size permits.
- Report paired task-level differences with bootstrap 95% intervals for the
  confirmatory matrix; retain per-seed values and mean±SD for stochastic runs.
- Use each paper's stated seeds for Matrix A. For Matrix B, use at least three
  independent seeds for stochastic components; use GRASP's five-seed open-model
  setting when reproducing that condition. A deterministic schema smoke may use
  one run but cannot support a performance claim.
- Report negative, zero, failed and blocked cells separately. Do not average
  them away or impute missing performance.
- No-skill, random and oracle conditions may calibrate the host, but they are
  diagnostic controls rather than the primary research question.

## 10. Stop conditions and decision gates

A cell stops and is retained as `blocked`, `partial` or `failed` when:

1. a required native artifact/source revision cannot be identified;
2. required semantics would have to be silently guessed;
3. test/evaluation leakage is detected;
4. the evaluator or success definition differs from the matched reference;
5. running requires an undeclared adjacent-component rewrite;
6. raw component output or adapter-loss evidence cannot be retained;
7. the declared resource budget is exceeded; or
8. continuing would overwrite the starting library/checkpoint rather than use
   an isolated copy.

### Advancement gates

- **M0 Native reference:** native/source-variant cell finishes with raw
  artifacts, or is explicitly blocked with evidence.
- **M1 Boundary conformance:** input/output/state and failure/no-op validate.
- **M2 Adapter audit:** every conversion is classified; no hidden required
  inference exists.
- **M3 Matched comparison:** frozen-neighbor and split checks pass.
- **M4 Portability report:** compatibility, fidelity, performance, efficiency
  and failure evidence are all reported.

Only cells passing M0–M3 may contribute a performance-portability comparison.
Earlier-gate failures remain compatibility evidence.

## 11. Day-5 dry-run input

Day 5 will not begin with a new benchmark run. It will map retained Week-3.2
factorial traces into the Matrix-B record shape to verify:

- comparison-cell linkage and frozen-control fields;
- adapter-event coverage and information-loss severity;
- task-paired metrics and raw numerator/denominator;
- failure-code assignment from `stop_reason`, warnings and trace state;
- fields that are unavailable in historical traces; and
- whether the schema can represent completed, failed, no-op and blocked cells.

After that dry-run, Day 5 will specify—but not silently broaden—the first
paper-derived component integration: `B-A-SKILLRL-UNDER-GRASP`. The GRASP
gate, probe, evaluator, failure evidence, task/library start and budgets remain
fixed. The adapter may translate only the SkillRL updater's ADD output into a
GRASP candidate edit; it must report that MODIFY/REMOVE, per-candidate
validation evidence and refinement semantics are unavailable rather than
invent them.

The completed dry-run and resulting integration specification are:
[`matrix_dryrun.md`](../04_matrices/matrix_dryrun.md) and
[`integration_spec_grasp_skillrl_proposer_swap.md`](integration_spec_grasp_skillrl_proposer_swap.md).

## 12. Day-4 completion criteria

- [x] Matrix A separates paper-native fidelity from observed SkillStack data.
- [x] Matrix B defines selected single-slot component swaps without a full
  Cartesian product; whole-method host transfer is auxiliary.
- [x] Every adopted experiment axis points to a paper card/source family.
- [x] Matched controls, information-axis exceptions and split rules are frozen.
- [x] Execution, compatibility and fidelity labels are independent.
- [x] Adapter loss, performance, efficiency and failures remain separate
  measurements.
- [x] Negative, rejected, no-op, partial and blocked cells are retained.
- [x] Day-5 trace dry-run and first-integration entry gates are specified.

No implementation or experiment result is changed by this protocol.
