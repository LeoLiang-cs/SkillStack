# Week 4 报告导航

Week 4 的研究重点是**跨论文组件的单槽位可插拔性**：固定 task、evidence、library、repository、gate 和 evaluator，只替换 Acquisition/Evolution 的 proposer，检查 GRASP 与 SkillRL 是否能通过明确 adapter 接到同一个 Lifecycle 边界。

## 建议阅读顺序

1. [`00_overview/w4_advisor_brief_zh.md`](00_overview/w4_advisor_brief_zh.md) — 可直接用于导师汇报的精简版本。
2. [`00_overview/week4_final_summary_zh.md`](00_overview/week4_final_summary_zh.md) — 内部最终技术总结，保留完整 gate、结果与限制。
3. [`01_planning/decisions/week4_research_goal_corrected_zh.md`](01_planning/decisions/week4_research_goal_corrected_zh.md) — 会议后研究目标为什么从整套 agent 迁移修正为单槽位替换。
4. [`02_paper_analysis/architecture_crosswalk.md`](02_paper_analysis/architecture_crosswalk.md) — 六篇论文的共同 primitive、R-A-D-C-L 判断和接口抽象。
5. [`03_protocols/integration_spec_grasp_skillrl_proposer_swap.md`](03_protocols/integration_spec_grasp_skillrl_proposer_swap.md) — A0/A1 实验的冻结条件、adapter、gate 和停止规则。
6. [`04_matrices/matrix_b_plugin_portability.csv`](04_matrices/matrix_b_plugin_portability.csv) — 当前所有可插拔实验单元及其通过、未运行或阻塞状态。

## 目录职责

| 目录 | 内容 | 使用场景 |
|---|---|---|
| `00_overview/` | 导师简报和内部最终总结 | 快速了解本周成果 |
| `01_planning/` | 范围、抽取模板和研究决策 | 追溯为什么这样设计 |
| `02_paper_analysis/` | 六张 Algorithm Card 和跨论文架构分析 | 查看论文依据与结构抽象 |
| `03_protocols/` | Performance Matrix 协议和 A-slot 集成规范 | 复现实验设计 |
| `04_matrices/` | 原生实验矩阵、可插拔矩阵和历史 dry-run | 查结构化结果与实验状态 |
| `05_experiments/` | Source smoke、gate parity、provider flow 和 A0/A1 配对结果 | 查看具体执行证据 |
| `90_archive/` | 已被正式文档覆盖但仍有过程价值的旧计划和 Day2/Day3 总结 | 仅用于历史追溯 |

## 当前结论边界

- **已完成：** I0 source、I1 13/13 split、I2 gate parity、provider-substituted I3、I4/I5/I6 compatibility。
- **凭证阻塞：** Source-faithful SkillRL/o3，状态为 `blocked_credentials`。
- **环境阻塞：** 严格 13/13 task performance，状态为 `blocked_environment`。
- **可以主张：** 两个跨论文 A-slot 组件达到 adapter-compatible，且未要求重写相邻 Lifecycle gate。
- **不能主张：** SkillRL 比 GRASP 效果更好、完整复现论文、或 no-change gate 等同于真实任务无收益。

## 文件保留策略

本目录保留正式结论、实验协议、原始论文分析和不可替代的实验记录。`day4_summary.md`、`day5_summary.md`、`implementation_step1_summary.md` 已被正式协议和最终结果完全覆盖，因此删除；Day2、Day3 与原始 Phase 4 计划仍能解释研究方向变化，因此移入 `90_archive/`。

