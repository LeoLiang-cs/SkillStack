# Week 4 — GRASP Native Repository Source Smoke

**Local date:** 2026-08-26  
**Run ID:** `20260827T043304706348Z_w4_grasp_repository_source_smoke`  
**Result:** passed  
**Model calls:** 0  
**ALFWorld episode calls:** 0

## What was connected

This smoke used the existing SkillStack proposal envelope, adapter and
`JsonlTraceWriter`, then crossed into the pinned released GRASP repository code.
It did not create a separate result-storage pipeline.

The executed path was:

```text
handcrafted SkillRL native output
  → SkillRL-to-GRASP envelope adapter
  → native GRASP ADD shape
  → released SkillUpdater.validate
  → released SkillRepository.fork
  → released SkillUpdater.apply
  → released SkillRepository.cleanup
  → SkillStack run manifest / episodes.jsonl / summary
```

## Verified source evidence

- GRASP commit:
  `9d7d125a3e9b46ed591692475eb07aff4ae67d34`.
- Released split counts: dev 26, validation 24, test 20.
- Dev, validation and test task-ID sets are mutually disjoint.
- Component split inherited the GRASP epoch-0 shuffle seed
  `2:shuffle:0` rather than using an unrelated local shuffle.
- History/probe source: 13 records.
- Proposal source: 13 records.
- History/probe and proposal task-ID overlap: none.
- Validation/test access in the component split: none.

Frozen history/probe task IDs:

```text
26, 9, 23, 34, 3, 25, 49, 14, 8, 4, 11, 43, 6
```

Frozen proposal task IDs:

```text
27, 46, 45, 37, 40, 20, 19, 38, 16, 32, 31, 15, 7
```

## Repository-boundary result

- Native validator accepted exactly one ADD candidate.
- Native applied name: `systematic_container_search`.
- Fork snapshot contained exactly one learned skill after apply.
- SkillStack provenance was written into the native Markdown frontmatter.
- Starting learned repository was identical before and after the smoke.
- Temporary native GRASP fork was cleaned up.
- Run artifacts were written through the existing SkillStack JSONL writer.

The source check also exposed and corrected one adapter mismatch: the first
fixture used hyphenated names, while released GRASP normalizes names with
lowercase underscores. The adapter now emits the native convention directly
and records the rename transform.

## Verification state

- Whole SkillStack suite after I2: 66 tests passed, one pre-existing conditional test
  skipped.
- I1 split gate: passed for the released source snapshot.
- I2 fixture/native gate: passed after the five-scenario parity run documented
  below.
- I3 adapter gate: partial pass; native shape and repository acceptance passed,
  released SkillRL updater call has not run.
- I4–I6: not started.

## Evidence artifacts

- `runs/20260827T043304706348Z_w4_grasp_repository_source_smoke/run_manifest.json`
- `runs/20260827T043304706348Z_w4_grasp_repository_source_smoke/episodes.jsonl`
- `runs/20260827T043304706348Z_w4_grasp_repository_source_smoke/summary.json`

## I2 update

I2 is now complete. Run `20260827T074403832376Z_w4_grasp_gate_parity`
matched the released GRASP baseline/candidate scoring and admission decision in
all five deterministic scenarios. See `grasp_gate_parity_summary.md`.

The next target is I3: one released SkillRL updater compatibility smoke with
raw input/output and adapter evidence retained.
