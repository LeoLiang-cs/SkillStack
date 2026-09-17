# 当前计划入口

当前执行规划采用科研主线 v4，更新于 2026-09-16。

1. [SkillStack / BLM 科研主线计划 v4](skillstack_research_master_plan_v4_zh.md)：当前唯一主计划；G0+G1 合并为已完成的 F0，下一阶段直接进入 BLM。
2. [R1-00 BLM 测量可行性与实验协议审计清单](r1_00_blm_calibration_preparation_plan_list_zh.md)：已完成；primary calibration boundary、negative control 与 R1-01 handoff 已冻结。
3. [R1-01 BLM 首次边界捕获与干预机制实现清单](r1_01_blm_boundary_instrumentation_plan_list_zh.md)：已完成；默认关闭的 first-handoff capture/intervention 与 validity guard。
4. [R1-02 首次 handoff replay 清单](r1_02_blm_first_handoff_replay_plan_list_zh.md)：首次 envelope 与 exact replay。
5. [R1-03 boundary-atom census 清单](r1_03_blm_boundary_atom_census_plan_list_zh.md)：runtime read tracking 与 atom 冻结。
6. [R1-04 restoration controls 清单](r1_04_blm_restoration_controls_plan_list_zh.md)：合法 restoration、matched carrier 与 unread controls。
7. [R1-05 bounded verdict 清单](r1_05_blm_bounded_verdict_calibration_plan_list_zh.md)：有限范围 verdict 与 R1 exit audit。
8. [R2 自然案例筛选与增量验证清单](r2_blm_natural_case_increment_plan_list_zh.md)：Structured ReAct 首次 handoff、候选筛选、固定 arms 与 dry-run；live provider 需人工启动。
9. [研究 framework v2](../original/skillstack_draft_framework_2.md)：BLM 当前方法定义与研究主张边界。
10. [G0 发布隔离清单](g0_release_isolation_plan_list_zh.md)与 [G1 核心 Alpha 清单](g1_core_alpha_plan_list_zh.md)：仅作为 F0 的历史工程记录。
11. [v3 总计划](skillstack_blm_master_plan_v3_zh.md)与 [v3 执行清单](skillstack_blm_execution_backlog_v3_zh.md)：保留用于理解旧编号，不再决定执行优先级。

F0 工程完成证据：[Week 7 G1 完成执行报告](../../report/week7/g1_completion_execution_report_zh.md)。

[项目计划 v2](project_plan_v2_zh.md) 保留作历史。

当前状态：F0（历史 G0+G1）、R1-00～R1-05 已完成；R1 状态为 `complete_calibration_only`，R2 实现已进入 `implementation_complete_live_not_run`，当前 dry-run 没有可验证的 live case（optional ALFWorld runtime 未安装）。正式开源整理延期到研究实验与论文完成之后。这些全局规划文件不自动属于公开发布内容。
