# Week 4 — GRASP Gate Contract Parity

**Date:** 2026-08-27  
**Successful run:** `20260827T074403832376Z_w4_grasp_gate_parity`  
**Result:** five of five scenarios matched released GRASP  
**Model calls:** 0  
**ALFWorld episode calls:** 0

## Completed

SkillStack now has a deterministic implementation of the released GRASP gate
contract. The parity smoke called GRASP's native baseline and candidate methods
with deterministic task-client outputs and compared these fields:

- baseline fixes and regressions;
- baseline error IDs;
- candidate fixes and regressions;
- invalid-action regressions and penalty;
- raw and adjusted scores; and
- final accept/no-op decision.

All compared fields matched in all five cases:

| Scenario | Native parity | Decision |
|---|---:|---|
| positive fix without regression | match | accept |
| ordinary regression | match | no-op |
| invalid-action regression | match | no-op |
| pre-existing baseline error repeated by candidate | match | accept |
| no change | match | no-op |

The first parity attempt,
`20260827T070104527999Z_w4_grasp_gate_parity`, stopped because the deterministic
harness lacked GRASP's `_id_to_index` field. It made no model/environment calls
and is retained as an incomplete integration attempt. The corrected run added
the minimum source-required mapping and deterministic task client.

## Important source behavior

The pre-existing-error scenario exposes a GRASP gate edge case:

1. a task was previously passing;
2. the fresh baseline returns `status=error`, producing one baseline regression;
3. the candidate returns the same error;
4. candidate regression counting excludes it as a pre-existing error;
5. adjusted score becomes `0 - (0 - 1) = +1`;
6. the candidate is admitted despite producing zero fixes and repeating the
   same error.

The source parity test confirms this is released GRASP behavior, not a
SkillStack approximation error. Primary A0/A1 reporting must therefore retain:

- raw fixes and regressions;
- baseline errors and candidate errors;
- adjusted score; and
- a stricter sensitivity result requiring at least one actual fix.

The released rule remains the source-fidelity result. The stricter
`actual_fixes > 0` result must be labeled as a SkillStack sensitivity analysis,
not silently substituted for GRASP.

## Gate status

- I0 Source: passed.
- I1 Split: passed.
- I2 Fixture/native gate: passed.
- I3 Adapter: source-shape boundary passed; released SkillRL updater call still
  pending.
- I4 Native A0: not started.
- I5 Swapped A1: not started.
- I6 Comparison: not started.

## Next target

Complete I3 by running the released SkillRL updater once on a small frozen
failure fixture, retaining its raw request/output, parse/no-op status, model
configuration, usage and adapter events. The resulting candidates may enter the
already frozen GRASP gate, but the run is only a compatibility smoke and cannot
support a performance claim.

## I3 update

Run `20260827T074953255512Z_w4_skillrl_i3_source_smoke` completed the frozen
fixture, released prompt construction and raw-call instrumentation, but stopped
before the API call because the required Azure key and endpoint are absent. I3
therefore remains `blocked_credentials`, not passed. See
`skillrl_i3_source_smoke_summary.md`.
