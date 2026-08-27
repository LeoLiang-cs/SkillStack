# Week 4 — SkillRL Flow Backend Comparison

**Date:** 2026-08-27  
**Decision:** use `deepseek_v4_flash` for subsequent provider-substituted runs  
**Decision rule:** switch only if latency decreases by at least 30%

## Matched comparison

Both calls used the same historical failure fixture, released SkillRL prompt,
maximum token setting, temperature, parser, adapter, native GRASP repository
boundary and deterministic no-change gate. Only the writer backend changed.

| Metric | GLM FlashX | DeepSeek V4 Flash |
|---|---:|---:|
| Run ID | `20260827T075641886319Z_w4_skillrl_zhipu_glm_flashx_flow_smoke` | `20260827T075940000842Z_w4_skillrl_deepseek_v4_flash_flow_smoke` |
| Model latency | 105.965 s | 3.144 s |
| Latency reduction | — | 97.03% |
| Speedup | 1.00× | 33.70× |
| Prompt tokens | 531 | 545 |
| Completion tokens | 220 | 282 |
| Estimated cost | $0.00012505 | $0.00061204 |
| Native candidates | 3 | 3 |
| Adapter-valid | 3 | 3 |
| Reached native repository | 3/3 | 3/3 |
| Gate result | 3 no-op | 3 no-op |

DeepSeek exceeded the pre-registered 30% reduction threshold by a wide margin,
so it becomes the default substituted backend. Its estimated cost was 4.89×
higher, but the absolute difference for this call was approximately $0.000487.

This is one call per backend, so it is an operational choice rather than a
stable latency benchmark. Candidate quality was not compared: the gate used a
fixed no-change runnability fixture, and both runs were provider-substituted
rather than source-faithful SkillRL/o3 results.

DeepSeek normalized candidates:

1. `confirm_object_identity_before_pickup`
2. `check_drawer_contents_before_closing`
3. `scan_all_surfaces_for_targets`
