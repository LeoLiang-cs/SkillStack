# Week 4 — SkillRL Provider-Substituted Flow Smoke

**Date:** 2026-08-27  
**Run ID:** `20260827T075641886319Z_w4_skillrl_zhipu_glm_flashx_flow_smoke`  
**Result:** complete  
**Fidelity:** `provider_substituted_flow_smoke`  
**Future substituted backend:** `deepseek_v4_flash`

## Result

One GLM writer call successfully exercised the complete engineering path:

```text
historical failure fixture
  → released SkillRL prompt builder
  → substituted GLM writer
  → released SkillRL JSON parser and dyn_NNN reassignment
  → SkillRL-to-GRASP adapter
  → released GRASP validate/fork/apply/cleanup
  → deterministic fixed gate
  → SkillStack manifest/JSONL/summary
```

Observed results:

- native parsed candidates: 3;
- adapter-valid candidates: 3;
- candidates reaching the native GRASP repository: 3/3;
- native repository boundary success: 3/3;
- deterministic gate result: three no-ops under the explicitly labeled
  no-change runnability fixture;
- prompt tokens: 531;
- completion tokens: 220;
- cached prompt tokens: 2;
- latency: 105.965 seconds;
- estimated cost: USD 0.00012505.

Normalized candidate names:

1. `verify_object_location_first`
2. `scan_for_all_target_objects`
3. `check_inventory_before_placement`

The no-op decisions do not measure candidate quality. Candidate probe outcomes
were intentionally fixed to no change so this run could establish boundary
runnability without making a task-performance claim.

## Interpretation

This result proves that the full SkillRL-shaped output path can run through the
current SkillStack adapter and unchanged GRASP repository/gate boundary when a
different writer provider is substituted. It does not close source-faithful I3:
released SkillRL specifies o3 through Azure, and those credentials remain
unavailable.

The source-faithful cell therefore remains `blocked_credentials`. This GLM run
is recorded as a separate portability/engineering cell and is not used as a
SkillRL paper reproduction.

## Backend decision

GLM was used only for this first successful flow smoke. Per the updated research
decision, subsequent provider-substituted calls should use
`deepseek_v4_flash`. Existing GLM evidence remains immutable and will not be
overwritten or relabeled.

A matched DeepSeek follow-up completed in run
`20260827T075940000842Z_w4_skillrl_deepseek_v4_flash_flow_smoke`. Its model
latency was 3.144 seconds versus GLM's 105.965 seconds, a 97.03% reduction and
33.70× speedup. DeepSeek therefore passed the pre-registered 30% threshold and
is the selected substituted backend. See
`skillrl_provider_backend_comparison.md`.
