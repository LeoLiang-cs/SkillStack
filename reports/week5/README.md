# Week 5 报告索引

Week 5 完成了 Week 4 被环境阻塞的严格 13/13 A-slot 性能实验，并据此把
下一步扩展到 SkillOps maintenance 的第二种跨论文组件边界。

## 目录

- [`skill/week5_weekly_report_zh.md`](skill/week5_weekly_report_zh.md)：
  面向导师的 Week 5 中文科研周报，整合 A-slot 与 SkillOps M1–M5 周期。
- [`skill/week5_meeting_outline_zh.md`](skill/week5_meeting_outline_zh.md)：
  精简组会提纲与一分钟口头版。
- [`00_overview/w5_advisor_brief_zh.md`](00_overview/w5_advisor_brief_zh.md)：
  面向导师的主报告，包含实验目标、设计、结果、成本、限制和下一步。
- [`05_experiments/w5_performance_evidence_audit.md`](05_experiments/w5_performance_evidence_audit.md)：
  原始 JSON 到报告结论的数字核对与解释边界。
- [`05_experiments/skillops_m1_m3_summary_zh.md`](05_experiments/skillops_m1_m3_summary_zh.md)：
  SkillOps adapter、受控 duplicate maintenance 与 unchanged-host recorder 的
  零模型验收结果。
- [`02_paper_analysis/skillops_refresh_zh.md`](02_paper_analysis/skillops_refresh_zh.md)：
  对 SkillOps v1 论文、官方 commit 和 Week4 分析的刷新核查。
- [`01_planning/skillops_maintenance_experiment_plan_zh.md`](01_planning/skillops_maintenance_experiment_plan_zh.md)：
  SkillOps maintenance 可插拔实验计划；只给计划和命令，不启动长耗时实验。

## 本周证据状态

| 层次 | 状态 | 能支持的结论 |
|---|---|---|
| Adapter compatibility | 已完成 | A0/A1 都能进入同一 repository 与 gate |
| Native gate admission | 已完成 | 原生 GRASP gate 对四个候选分别给出 accept/no-op |
| Effectiveness sensitivity | 已完成 | 额外要求 `native_admitted AND fixes > 0` |
| ALFWorld task performance | 单 seed 完成 | 报告 13-task 原始计数；不能推断一般优劣 |
| SkillRL source fidelity | 未完成 | 本次是 DeepSeek Flash substituted writer，不是 Azure O3 |
| SkillOps maintenance M1–M3 | 已完成 | 往返安全、受控 merge correctness、host recorder parity |
| SkillOps task performance M4–M5 | 已完成 | 144 episodes、0 error；三次 val 重复无可分辨方向差异 |
| SkillOps held-out M6 | 未开始 | test split 尚未消耗 |

## 真实结果根目录

`runs/week5/w5_a_slot_seed2_deepseek_flash/`

报告不复制或改写原始运行结果；所有数字均可从该目录中的
`evidence_summary.json`、`paired_summary.json`、两个 cell summary、proposal
output 和候选 `result.json` 复核。
