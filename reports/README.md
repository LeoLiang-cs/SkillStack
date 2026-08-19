# SkillStack Reports

Reports are organized by research week. Each week directory is append-mostly:
plans are committed before runs, summaries refuse to overwrite, and raw
evidence stays immutable under `runs/`.

| Directory | Content | Status |
|---|---|---|
| `week1/` | P0.0 vertical slice (Phases 0–7): environment smoke, frozen tasks, static library, C0/C1 interchangeability pilot, friction ledger, advisor brief | Complete |
| `week2/` | Phase 2A: skill-conditioned execution — deterministic multi-step executor × four skill-input conditions | Complete |
| `week3/` | Phase 2C+2D: LLM ReAct executor swap, ceiling finding, tight-budget skill signal, GLM few-shot attribution | Complete |
| `week3_2/` | Phase 3: RQ3 retrieval × composition 2×2 factorial + Canonical Interface v1 induction | In progress |

## Week 1 (P0.0)

- `phase0_manifest.json` — preflight skeleton check
- `phase1_alfworld_smoke.json` — deterministic ALFWorld reset + one action
- `phase2_task_validation.json` — five frozen tasks, real environment resets
- `phase5_pilot_summary.json` — C0/C1 pilot binding from immutable runs
- `phase6_pilot_audit.md` — results audit + adapter-friction ledger v0
- `phase7_advisor_brief.md` / `phase7_advisor_brief_zh.md` — first advisor update

## Week 2 (Phase 2A)

- `plan_phase2a.md` — committed plan: objective, conditions, H1 gate, metrics, non-goals
- `w2_pilot_summary.json` — four-condition pilot bound from immutable runs
- `w2_friction_ledger.md` — friction ledger v1 additions (F-06 … F-14)
- `w2_advisor_brief.md` / `w2_advisor_brief_zh.md` — second advisor update

## Week 3 (Phase 2C + 2D)

- `plan_phase2c.md` — committed plan: ReAct executor swap, backends, gates, probe addendum
- `plan_phase2d.md` — committed plan: harder task set + GLM few-shot attribution
- `w3_hard_tasks_validation.json` — 8-task harder set, real-reset validation
- `w3_pilot_summary_deepseek_v4_flash.json` — 5-task DeepSeek pilot summary (2C)
- `w3d_picktwo_tightbudget_summary.json` — pick_two × 20-step summary (2D)
- `w3_glm_2shot_probe.json` — GLM few-shot validity attribution (2D-D3)
- `w3_friction_ledger.md` — friction ledger additions (F-15 … F-21)
- `w3_advisor_brief.md` / `_zh.md` — third update (2C executor swap)
- `w3_advisor_brief_4.md` / `_4_zh.md` — fourth update (2C/2D findings)

## Week 3_2 (Phase 3)

- `plan_phase3.md` — committed plan: 2×2 factorial + interface induction
- `picktwo9_validation.json` — 9 pick_two tasks, real-reset validation
- `w3_2_factorial_summary.json` — 2×2 factorial + interaction I
- `w3_2_friction_ledger.md` — ledger additions (F-22 … F-25)
- `w3_2_rq1_assessment.md` — RQ1 reference-architecture assessment
- `w3_2_advisor_brief.md` / `_zh.md` — fifth advisor update
- `docs/canonical_interface_v1.md` — interface induction draft
