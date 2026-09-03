# SkillOps 论文与代码刷新核查

## 输入覆盖范围

- **论文：** [SkillOps: Managing LLM Agent Skill Libraries as Self-Maintaining Software Ecosystems](https://arxiv.org/abs/2605.13716)，arXiv v1，2026-05-13。
- **官方代码：** [Hik289/SkillOps](https://github.com/Hik289/SkillOps)，commit
  `c80b05246369c0b9d82a293390ca5add675c516a`。
- **覆盖级别：** 论文全文、官方仓库全部 Python 源码/测试/示例/文档，以及
  Week4 algorithm card、architecture crosswalk 和 performance protocol。
- **本次核查日期：** 2026-09-02。
- **验证：** 官方仓库 13/13 tests 通过；无网络 demo 可运行。没有运行论文规模
  ALFWorld grid，也没有调用外部模型。

## 研究问题与方法

SkillOps 研究的不是“当前 episode 怎样临时修好”，而是长期增长的 skill
library 怎样处理冗余、过时实现、缺失 validator、接口不兼容和风险传播等
**library-time technical debt**。

论文把每个 skill 表示为五元组 `(P,O,A,V,F)`：Precondition、Operation、
Artifact、Validator、Failure modes；再用 dependency、compatibility、
redundancy、alternative 等关系组织 library。论文中的 Library-Time Loop 先做
health diagnosis / risk propagation，再执行 `merge`、`repair`、`retire`、
`add_validator`、`add_adapter`，输出可交给不变下游 agent 的 maintained
library。

论文同时包含一个 task-time Graph-of-Graphs planner，但它不是第一轮
maintenance plug-in 实验需要替换的组件。第一轮若同时更换 planner，就无法
判断结果来自 maintenance 还是 D/C host 改变。

## 论文实验边界

论文主实验使用 ALFWorld 的 offline `high_pddl` strict-order subgoal grader，
每个 seed 185 个任务，并使用 200–2000 规模的 skill library 和人工注入的六类
technical debt。论文还比较 raw 与 maintained library 在多个不变 downstream
host 上的差值。

这个 success 定义与 SkillStack Week5 的交互式 AgentBench episode success
不同，不能把论文的 79.5% 与 Week5 的 12/13 直接并排当成同一个指标。
论文报告的主要数字在当前公开仓库中也缺少对应的原始 runs、200–2000 skill
libraries、aggregation scripts 和完整 grid，因此当前不能做 exact result
reproduction。

## 官方代码实际提供了什么

commit `c80b052` 提供：

1. `SkillContract`、`Skill`、`SkillLibrary` 和五类 typed edges；
2. load/save、directory loading 和 edge rebuilding；
3. 五个可直接调用的 maintenance primitives；
4. `MaintenanceEngine.sweep()`；
5. 一个轻量 planner、12-skill demo library、CLI 和 13 个 smoke tests。

本次实测：

- 13/13 tests 通过；
- demo 从 12 个 skills 开始，sweep 报告 `merged=2`，最后为 10 个 skills；
- demo 中 `validators_added=0`，所以 README 所说 demo 会 exercise
  `add_validator` 并没有在这一运行顺序中发生：缺 validator 的 synthetic
  skill 先作为 redundancy 被 merge 掉了。

## 论文与源码之间的关键缺口

1. **自动 sweep 只覆盖部分动作。** `sweep()` 自动做 signature merge、可选
   usage retirement 和特定 synthetic tag 的 validator inheritance；`repair`
   与 `add_adapter` 要求调用者提供 domain-specific 内容。
2. **`failure_log` 当前不驱动 repair。** 构造器接收它，但 `sweep()` 没有使用
   它生成或记录 repair candidate。
3. **没有五维 health diagnosis / maintenance trigger / CGPD。** 源码没有论文
   Algorithm 4/5 的完整实现。
4. **报告缺少身份级审计。** `MaintenanceReport` 只有动作数量，没有 survivor、
   removed IDs、old→new mapping、拒绝/no-op 原因或回滚目标。
5. **repair 是原地覆盖。** `repair_skill()` 改 operation 并追加一条 metadata，
   但没有建立新版本对象、父版本快照或可执行 rollback。
6. **planner 不是论文完整 graph search。** released `_stage2_stitch()` 实际选择
   一个最接近的 domain candidate，而不是多 skill constrained graph stitching。
7. **公开 entry point 不是论文 grid。** `run_skillops.py` 是单任务 CLI，
   `examples/demo.py` 是 12-skill smoke；二者不能独立复现论文表格。

这些缺口不否定 released primitives 的工程价值，但决定了 fidelity 标签：

- 单个 released primitive：`paper_faithful_possible`；
- 当前 `MaintenanceEngine.sweep()`：`source_variant`；
- 完整论文 SkillOps / CGPD / paper-scale result：`blocked_missing_artifacts`。

## 对 Week4 分析的复核

Week4 的核心判断仍成立，而且官方 HEAD 仍是同一 commit：

- `R` 应是跨槽位 artifact contract；
- `L` 必须区分新候选 admission 与既有 library maintenance；
- 第一安全步骤是 copied-library round trip；
- 第一真实性能 cell 必须固定 downstream D/C host，并排除 SkillOps planner；
- 不能把 released partial sweep 写成完整论文复现。

本次新增的实现级约束是：第一轮 cross-paper adapter 不能把 GRASP 的 Markdown
行为建议凭空解释成完整语义 `(P,O,A,V,F)`。否则 signature merge 可能把不同
行为错误合并。安全起点应使用**opaque、可逆 fingerprint contract**，只允许
对字节等价的 controlled clones 做 merge；semantic contract 留到第二阶段。

## 对 SkillStack 的直接启发

- **可直接借鉴：** maintenance 作为 `library copy → maintained copy + action
  report + ID map` 的独立边界。
- **可对比验证：** 在不改 GRASP `SkillAwareAgent` 选择、注入和 evaluator 的
  条件下，对 raw/maintained library 做 paired task comparison。
- **可作为边界案例：** source 可以“API 跑通”，但缺少 full health loop、
  versioning 和 result artifacts；这正好检验 SkillStack 是否能把 compatibility、
  fidelity 和 performance 分开报告。

## 是否值得精读

- **标签：** 值得精读
- **理由：** 它直接对应 SkillStack 下一条 Lifecycle/Maintenance 组件边界，
  并提供清楚的 raw→maintained 插件主张；同时源码缺口足够具体，适合做
  source-grounded portability 实验，而不是复述论文数字。
