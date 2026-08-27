# Day 5 Integration Specification — GRASP Proposer vs SkillRL Updater

**Date:** 2026-08-26  
**Status:** specification frozen; local contract and native repository source smoke complete  
**Primary slot:** `A — Diagnose/Distill → Propose/Transform`  
**Frozen downstream responsibility:** `L — GRASP regression-aware admission`  
**Environment:** released GRASP AgentBench ALFWorld condition  
**Claim boundary:** cross-paper component compatibility experiment, not a
reproduction of SkillRL or a head-to-head claim about complete systems.

## 1. Question and hypothesis

Can the released SkillRL additive updater replace the native GRASP proposal
pipeline while the GRASP repository, probe, evaluator and admission rule remain
unchanged?

- **Compatibility hypothesis:** SkillRL's ADD output can be converted into a
  valid GRASP ADD candidate through one explicit output adapter.
- **No performance-direction hypothesis:** the experiment does not assume that
  either proposer will produce more fixes or better task scores.
- **Expected friction:** SkillRL lacks MODIFY/REMOVE, failure grouping,
  candidate-level evidence and contrastive revision semantics. Those gaps must
  remain visible.

## 2. Verified source boundaries

### GRASP

- Repository commit: `9d7d125a3e9b46ed591692475eb07aff4ae67d34`.
- AgentBench ALFWorld config: 26 dev, 24 validation and 20 held-out test records
  in the inspected snapshot; 10 epochs, `K=4`, probe budget 20, seed 2.
- Native proposal unit:
  `classify_failures → diagnose → group → propose → validate`.
- Native gate behavior: fresh current-library baseline and candidate runs on
  the same probe; adjusted fixes/regressions; hard regression budget; forked
  repository; commit at most one candidate or no-op.

### SkillRL

- Repository commit: `8e66726ed866a4e0a7f053586a41022798192e6c`.
- Released `SkillUpdater.analyze_failures(failed_trajectories,
  current_skills)` reads at most five displayed failures and their last five
  steps, calls o3, emits at most three new skills, reassigns collision-free
  `dyn_NNN` IDs and returns `[]` on API/parse failure.
- Output is additive only: `skill_id`, `title`, `principle`, and normally
  `when_to_apply`. It does not implement paper-described refinement, admission
  or rollback.

## 3. Important source/paper variant

The inspected GRASP source uses current-batch entries as the probe at epoch 0,
batch 0 when no earlier data exist, although its documentation and the paper
describe an out-of-sample probe. The released ALFWorld config uses one 26-item
dev batch, so this fallback is reachable.

The component comparison therefore freezes a stricter split:

1. deterministically order the 26 released dev records using the recorded seed;
2. run the first 13 as `history_probe_source` without proposing an edit;
3. run the next 13 as `proposal_source`;
4. build the probe only from the first 13;
5. fail preflight on any task-ID overlap;
6. never use validation or test outcomes for proposal/gating.

This is a SkillStack component-test protocol, not the exact released full-cycle
configuration. Exact-source behavior and strict-disjoint behavior require
separate fidelity labels.

## 4. Experimental cells

| Cell | `A` proposal implementation | Fixed `L` | Role |
|---|---|---|---|
| `A0-GRASP` | GRASP classify/diagnose/group/propose | strict-disjoint GRASP gate | native component reference |
| `A1-SKILLRL` | SkillRL `analyze_failures` + output adapter | identical strict-disjoint GRASP gate | first cross-paper swap |

The complete GRASP run remains a separate Matrix-A/source control. It is not
mixed into the paired A0/A1 result.

## 5. Frozen evidence universe

Both cells receive the same immutable evidence snapshot:

- `proposal_source` task IDs and failure outcomes;
- action/observation trajectories and evaluator results;
- `history_probe_source` task IDs and baseline outcomes;
- starting base/learned library bytes, capacity and version;
- ALFWorld task/evaluator implementation;
- random seed, task order and resource limits.

Each proposer may read only the fields its native mechanism uses. GRASP may use
passing examples, failure labels, diagnoses and current library statistics;
SkillRL may ignore them and read only failed trajectories/current skills. The
adapter ledger records these read-set differences rather than pretending the
algorithms consume identical evidence.

## 6. Common proposal envelope

Every raw candidate is wrapped without replacing its native payload:

```text
proposal_id
producer_method + source_commit
native_action
native_payload
normalized_action
normalized_name / description / content / tags
triggering_evidence_ids
adapter_events
unsupported_semantics
writer_model / decoding / call_usage
parse_status
```

Only `normalized_action=ADD` is shared by A0 and A1 in the first comparison.
GRASP MODIFY/REMOVE candidates remain in its native raw output but are excluded
from the matched ADD-only comparison and counted explicitly.

## 7. SkillRL → GRASP adapter v0

| SkillRL field | GRASP candidate field | Transform | Required handling |
|---|---|---|---|
| constant | `action="ADD"` | synthesize from released updater capability | record as generated; never emit MODIFY/REMOVE |
| `skill_id` | provenance/native ID | copy | do not use as final GRASP repository name |
| `title` | `name` | deterministic slug | retain original title in native payload |
| `when_to_apply` | `description` | copy | reject if missing; do not guess |
| `principle` + `when_to_apply` | Markdown `content` with Trigger and Rule sections | reversible construction | record template/version |
| task type | `tags` | construct | record source and any normalization |

The adapter must preserve the complete SkillRL JSON. It may not invent:

- MODIFY/REMOVE or paired replacement actions;
- verification examples;
- probe score, fixes or regressions;
- refinement/rollback support;
- failure-group labels not produced by SkillRL; or
- compatibility with a full-capacity library.

At capacity, a SkillRL ADD that GRASP rejects is recorded as
`L.ADD_BLOCKED_CAPACITY`, not silently converted into REMOVE+ADD.

## 8. Fixed gate and isolation decisions

For every candidate in A0 and A1:

1. validate schema and capacity;
2. fork the identical starting repository;
3. run the same frozen probe with the unchanged library for a fresh baseline;
4. apply one candidate only to its fork;
5. rerun the same probe;
6. compute adjusted fixes/regressions using the GRASP rule;
7. admit only positive improvement with no increase in regression count;
8. retain rejection/no-op and all raw probe transitions.

Contrastive revision is **disabled in both A0 and A1 primary cells**. Otherwise
the native GRASP revision writer could rewrite a SkillRL candidate and hide the
effect of the proposer swap. The full native GRASP control retains its native
revision behavior.

## 9. Budget and model axes

- Matched primary candidate cap: at most three ADD candidates per cell because
  the released SkillRL updater caps output at three. Native GRASP `K=4` remains
  in Matrix A rather than being presented as the matched cell.
- Model calls are not forced equal because the mechanisms use different stages;
  actual classifier/diagnoser/writer calls, tokens, latency and cost are
  reported separately.
- **Source-native writer axis:** each component uses its released writer setup;
  this tests portability but confounds mechanism and writer model.
- **Matched-writer axis:** deferred until both components can use one writer
  through a declared wrapper; this is required before an algorithm-only
  performance comparison.

The first implemented smoke may establish runnability and schema behavior
without making a performance superiority claim.

## 10. Required outputs

Each cell must retain:

- immutable request/evidence manifest and task-ID sets;
- starting library snapshot/hash;
- raw proposer prompts/inputs and raw model outputs;
- all raw and normalized candidates, including invalid/excluded ones;
- adapter events with transform kind and loss severity;
- baseline and candidate probe traces;
- fixes, regressions, invalid-action regressions and adjusted score;
- accepted/rejected/no-op decision and reason;
- repository fork mapping and before/after version/hash;
- writer/evaluator/model configuration and usage/cost;
- primary/secondary failure codes.

## 11. Metrics

### Primary

- boundary execution and schema-valid candidate rate;
- compatibility class and adjacent-component changes;
- adapter generated/dropped/approximated/defaulted fields;
- candidate accepted/rejected/no-op counts;
- fixes, regressions and invalid-action regressions on the same probe.

### Secondary

- writer/classifier/diagnoser calls, tokens, latency and cost;
- candidate duplication and capacity rejection;
- library size/version changes;
- task performance only as a paired downstream outcome, not a general
  skill-utility conclusion.

## 12. Gates and stop conditions

- **I0 Source:** both commits and exact files/configs are recorded.
- **I1 Split:** proposal/probe IDs are disjoint; val/test access is absent.
- **I2 Fixture:** deterministic handcrafted ADD candidates pass GRASP
  validate/fork/gate logging before any proposer call.
- **I3 Adapter:** valid SkillRL output round-trips; missing
  `when_to_apply`, parse failure, duplicate and capacity cases remain explicit.
- **I4 Native A0:** native proposer produces retained raw/normalized candidates.
- **I5 Swapped A1:** SkillRL updater reaches the unchanged gate without an
  adjacent `L` rewrite.
- **I6 Comparison:** A0/A1 use identical starting state/probe/evaluator and
  report paired transitions/cost.

Stop and retain the cell when credentials/endpoints are unavailable, evidence
overlaps, raw output cannot be stored, the gate must be rewritten for one
proposer, or a required field would need to be silently inferred.

## 13. Fidelity and claim labels

- complete released GRASP cycle: `source_variant` until the first-batch probe
  difference is resolved;
- A0 extracted proposer under strict gate: `source_component_experiment`;
- A1 released SkillRL updater under GRASP gate: `source_variant` component in a
  `cross_paper_slot_experiment`;
- neither A0 nor A1 is a full SkillRL reproduction or a full GRASP result.

## 14. Implementation status

The first low-cost implementation step is complete:

- proposal envelopes preserve native payloads and provenance;
- SkillRL ADD output is converted through a loss-visible adapter;
- missing fields, parse failure, empty output, duplicate names and candidates
  beyond the matched cap remain explicit;
- a deterministic 13/13 splitter rejects duplicate or overlapping task IDs;
- an in-memory gate fixture isolates the starting library and retains decisions
  and paired probe transitions;
- the repository test suite passes 58 tests with one pre-existing conditional
  skip.

At the end of the first local fixture step, I1 and I2 had not yet been checked
against the released ALFWorld/GRASP source. The following source-smoke update
records the subsequent native check.

### Native source-smoke update

Run `20260827T043304706348Z_w4_grasp_repository_source_smoke` completed against
the pinned GRASP commit. It verified the real 26/24/20 dev/validation/test split
counts, disjoint partition IDs, the exact epoch-0 source shuffle seed, and the
fixed 13/13 component split. One handcrafted SkillRL-shaped ADD passed the
released GRASP `validate → fork → apply → cleanup` repository boundary. The
starting repository remained unchanged and the temporary fork was removed.

This closes the source-data portion of I1. I2 remains partial because the smoke
did not invoke the native probe evaluator or calculate the released GRASP
adjusted gate score. Model calls and ALFWorld episode calls were both zero.

### Native gate parity update

Run `20260827T074403832376Z_w4_grasp_gate_parity` subsequently completed I2.
SkillStack and the released GRASP baseline/candidate methods matched on all
compared fields across positive-fix, ordinary-regression, invalid-action,
pre-existing-error and no-change scenarios.

The parity run exposed a source edge case: when a previously passing probe task
errors in both the fresh baseline and candidate run, GRASP counts one baseline
regression, excludes the candidate error as pre-existing, and can admit the
candidate with adjusted score `+1` despite zero actual fixes. Source-fidelity
results retain this decision. Primary reporting must also show raw fixes/errors,
and a separately labeled sensitivity analysis should require at least one real
fix.

### I3 released-updater update

Run `20260827T074953255512Z_w4_skillrl_i3_source_smoke` verified the pinned
SkillRL source, froze a historical failure fixture, constructed and stored the
exact released prompt, and installed raw request/response instrumentation. The
released constructor then stopped because `AZURE_OPENAI_API_KEY` and
`AZURE_OPENAI_ENDPOINT` are absent. No API or ALFWorld call occurred, and no
candidate was fabricated. I3 remains `blocked_credentials` until the same run
can produce, or explicitly return an empty, native updater result with valid
credentials.

### Provider-substituted flow update

Run `20260827T075641886319Z_w4_skillrl_zhipu_glm_flashx_flow_smoke` used the
released SkillRL prompt builder/parser with a substituted GLM writer. It
produced three native candidates; all three passed the adapter and released
GRASP repository boundary, then reached a deterministic no-change gate. This
establishes engineering runnability only and does not change the source-faithful
I3 status from `blocked_credentials`. Subsequent provider-substituted calls use
`deepseek_v4_flash`; the GLM run remains an immutable supporting cell.

A matched DeepSeek run then completed in 3.144 seconds versus GLM's 105.965
seconds. The 97.03% latency reduction exceeded the pre-registered 30% switch
threshold, so future provider-substituted experiments use
`deepseek_v4_flash`. This operational selection does not change the
source-faithful SkillRL/o3 cell or establish candidate-quality superiority.

### A0/A1 paired compatibility update

Run `20260827T080540451714Z_w4_a_slot_paired_deepseek_smoke` held the historical
failure evidence, empty learned library, DeepSeek writer, three-ADD cap and
deterministic gate fixed. A0 GRASP produced one valid ADD through three calls;
A1 SkillRL produced three valid ADDs through one call. All four candidates
passed the released GRASP repository boundary and reached the unchanged gate.
I4, I5 and I6 compatibility therefore pass under the provider-substituted
label.

Strict 13/13 task performance remains `blocked_environment`: AgentBench ports
5060/5061 and the Docker daemon were unavailable, and no existing trace set
contains the released 26 numeric task IDs. The no-change fixture is not used as
a performance proxy.
