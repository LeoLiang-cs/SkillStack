# Week 4 Day 5 — Historical-Trace Matrix Dry-Run

**Date:** 2026-08-26  
**Status:** complete  
**Input:** five immutable Week-3.2 runs, 45 ALFWorld episodes  
**New model/environment calls:** none  
**Purpose:** test whether the corrected single-slot matrix can represent real
SkillStack traces before implementing a paper-derived component.

## 1. Input runs

| Historical cell | Retriever (`D`) | Executor condition (`C`) | Run ID | Episodes |
|---|---|---|---|---:|
| `H-B00` | lexical | flat ReAct | `20260818T154917764174Z_w3_2_b00` | 9 |
| `H-B10` | task-semantic | flat ReAct | `20260818T155258922797Z_w3_2_b10` | 9 |
| `H-B01` | lexical | structured ReAct | `20260818T155625913852Z_w3_2_b01` | 9 |
| `H-B11` | task-semantic | structured ReAct | `20260818T155938729458Z_w3_2_b11` | 9 |
| `H-CONTROL` | no skill | flat ReAct | `20260818T161157142962Z_w3_2_control` | 9 |

All five runs contain the same nine unique task IDs. All 45 traces include the
21 checked runtime fields: run/episode/task identity, task text/family,
retriever/executor, retrieval response, selected IDs/native payloads, adapter
events, executor report, actions/observations/rewards, success/stop reason,
seed, step budget, library version and environment version.

## 2. Cell-level reconstruction

| Cell | Success | Terminal outcomes | Actions | LLM calls | Prompt / completion tokens | Cost estimate |
|---|---:|---|---:|---:|---:|---:|
| `H-B00` | 5/9 | 5 done; 4 max-steps | 148 | 157 | 466,155 / 4,964 | $0.033403 |
| `H-B10` | 5/9 | 5 done; 4 max-steps | 144 | 152 | 450,492 / 4,836 | $0.029290 |
| `H-B01` | 5/9 | 5 done; 4 max-steps | 140 | 146 | 438,484 / 4,481 | $0.031876 |
| `H-B11` | 5/9 | 5 done; 4 max-steps | 139 | 145 | 433,894 / 4,487 | $0.027801 |
| `H-CONTROL` | 3/9 | 3 done; 6 max-steps | 164 | 177 | 496,267 / 5,740 | $0.032576 |
| **Total** | **23/45** | **23 done; 22 max-steps** | **735** | **777** | **2,285,292 / 24,508** | **$0.154946** |

`max_steps_exhausted` is a task failure code (`BUDGET.MAX_STEPS`) but not a
matrix execution failure: those traces reached a terminal state and retained
all required raw outputs. Therefore execution status is `completed` for 45/45,
while task outcome is successful for 23/45.

## 3. Paired comparison dry-run

The historical aggregate success is equal across B00/B10/B01/B11, but paired
task transitions are not always equal. This confirms that Matrix B must retain
task-paired transitions instead of only cell means.

| Comparison | Slot changed | Both success | A-only success | B-only success | Both fail | Success-rate delta |
|---|---|---:|---:|---:|---:|---:|
| `H-D-E0` (`B00→B10`) | `D`: lexical→task-semantic; flat executor fixed | 4 | 1 | 1 | 3 | 0.0000 |
| `H-D-E1` (`B01→B11`) | `D`: lexical→task-semantic; structured executor fixed | 5 | 0 | 0 | 4 | 0.0000 |
| `H-C-R0` (`B00→B01`) | `C`: flat→structured; lexical retriever fixed | 4 | 1 | 1 | 3 | 0.0000 |
| `H-C-R1` (`B10→B11`) | `C`: flat→structured; task-semantic retriever fixed | 3 | 2 | 2 | 2 | 0.0000 |

The complete numeric edges are stored in
[`matrix_dryrun_comparisons.csv`](matrix_dryrun_comparisons.csv).

## 4. Adapter audit

- Adapter event coverage is 45/45.
- Every event contains `component`, `read`, `generated`, `dropped`,
  `approximated`, `defaulted`, and `warnings`.
- All cells read candidate ID, score and native payload, then construct selected
  IDs, scores, native skill list and flat skill context.
- Non-control cells have no recorded drop, approximation, default or adapter
  warning.
- The nine no-skill control events retain the expected warning: the executor
  receives an empty skill context. This is a declared control outcome, not an
  adapter failure.
- Historical `generated` conflates reversible packaging with new semantic
  synthesis. For the new matrix, each generated field also needs a severity /
  transform kind; these 45 events are classified as `reversible` construction,
  not new inferred skill semantics.

## 5. Failure-code dry-run

| Evidence | Proposed code | Count | Interpretation |
|---|---|---:|---|
| `environment_done` + success | none | 23 | completed execution and successful task |
| `max_steps_exhausted` | `BUDGET.MAX_STEPS` | 22 | completed trace, unsuccessful task |
| invalid-action retry warning | `HOST.ACTION_NOT_ADMISSIBLE` (secondary) | 42 warnings | recovered/nonterminal warning; retain attempts and cost |
| no-skill empty context | `D.NO_SKILL_CONTROL` | 9 episodes | expected diagnostic control, not failure |
| `runner_exception` | `INFRA.RUNNER_EXCEPTION` | 0 | not observed |

Historical codes are derived in this report only. The append-only raw traces
are not rewritten.

## 6. Schema coverage

### Directly available

- stable run/episode/task IDs and matched task population;
- component names and selected native artifacts;
- component raw retrieval output;
- action/observation/reward and task outcome;
- adapter transformation arrays and warnings;
- model-call usage, latency records and cost estimate;
- seed, step budget, library/environment version.

### Safely derivable

- cell aggregates and paired task transitions;
- calls, tokens, cost and invalid-action warning counts;
- `BUDGET.MAX_STEPS` and other stop-reason-based outcome codes;
- reversible severity for the exact historical adapter operations after
  inspecting their recorded read/generated fields.

### Missing and not backfilled

- explicit `comparison_id`, varied slot and frozen-neighbor declaration;
- component, host, prompt, library and adapter source hashes/versions;
- evaluator identity/version and split-access authority;
- temperature, retry, timeout, concurrency and cache policy in the immutable
  manifest, even though some are recoverable from source/plans;
- standalone raw component request and exact starting library hash;
- adapter transform kind/severity and native round-trip check;
- adjacent-component change record and compatibility decision evidence;
- explicit primary/secondary failure codes;
- paper-fidelity status, which is not applicable to these local methods.

These omissions prevent a retrospective claim that Week-3.2 already proved
paper-derived plug-and-play behavior. They do not prevent using the traces to
validate the record shape and paired-analysis logic.

## 7. Schema decisions produced by the dry-run

1. Add `not_applicable_local` to the fidelity vocabulary for SkillStack-native
   controls; never label them `paper_inspired` merely because they are local.
2. Separate immutable **cell records** from **comparison edges**. One run such
   as B11 participates in both a `D` comparison and a `C` comparison and should
   not be duplicated.
3. Store `task_outcome` separately from `execution_status`.
4. Store paired transitions: both-success, A-only, B-only and both-fail.
5. Add adapter `transform_kind` (`copy`, `rename`, `construct`, `synthesize`)
   plus loss severity.
6. Put all new failure classification in a sidecar/event field; never mutate
   historical raw traces.

## 8. Dry-run verdict

The current trace foundation is sufficient for a future single-slot matrix:
it already preserves component output, native payload, adapter events, task
outcomes and costs. It is not sufficient for a paper-portability claim without
new manifest provenance, evaluator/split authority, comparison-edge records and
typed failure/adapter metadata.

Day 5 can proceed to an integration specification. No new run or result is
authorized by this dry-run.
