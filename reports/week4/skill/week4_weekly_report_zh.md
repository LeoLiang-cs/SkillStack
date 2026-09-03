# SkillStack Week 4 科研周报

**主题：** 跨论文 A-slot 组件可插拔性验证

**时间：** 2026-08-25 至 2026-08-27

**当前阶段：** 兼容性实验完成；严格任务性能实验因环境问题阻塞

## 本周进展

### 本周最重要的变化

本周根据组会结论修正了研究重点：不再把“skill 到底有没有用”作为当前主问题，也不优先迁移整套论文 Agent，而是研究**不同论文中的单个算法组件能否在固定框架中替换**。

第一轮实验固定 task、failure evidence、library、repository、gate 和 evaluator，只替换 Acquisition/Evolution 中的 proposer：

```text
A0：GRASP proposer ──┐
                    ├──→ fixed GRASP repository + admission gate
A1：SkillRL updater ─┘
```

这一修正把研究问题从“某个方法是否有效”转为三个更具体的问题：组件能否接入、是否需要修改相邻模块，以及 adapter 转换了或损失了什么信息。

### 当前阶段性结论

GRASP proposer 和 SkillRL additive updater 都能通过显式 adapter 到达同一个、未改写的 GRASP repository 和 admission gate。因此，第一个跨论文 A-slot 实验已经达到 **adapter-compatible**。

目前还不能称为完全 plug-and-play，也不能比较两者的任务效果：SkillRL 输出需要显式生成 action、规范名称、构造 content/tags；严格 13/13 ALFWorld task-performance 实验则被 AgentBench/Docker 环境阻塞。

## 论文阅读总结

### 阅读主题

本周围绕“skill agent 的算法结构、组件边界和原生实验设计”深读了六篇论文，并统一提取：伪代码、输入输出、中间状态、实验轴、关键消融和可插拔边界。

### 重点论文与组件角色

| 方法 | 主要机制 | 对当前实验的作用 |
|---|---|---|
| SkillReranker | recall、task/skill parsing、graph、adaptive reranking | Discovery/Selection 参考 |
| GraSP | typed DAG compilation、verification、local repair | Discovery + Composition 参考 |
| SkillCAT | causal extraction、assessment gate、topology execution | Acquisition/Lifecycle 复合参考 |
| SkillRL | trajectory distillation、hierarchical SkillBank、additive evolution | A1 updater 来源 |
| GRASP | failure diagnosis、proposal、regression-aware admission | A0 proposer 与固定 gate 来源 |
| SkillOps | typed contract、health diagnosis、library maintenance | 后续 Lifecycle/maintenance 候选 |

### 主要收获

六种方法虽然实现差异很大，但可以用八个共同 primitive 描述：

```text
Observe → Represent → Generate → Structure → Assess → Gate → Act → Persist
```

这些 primitive 是分析和接口定位工具，不是要求所有论文使用同一套实现或统一 Skill Schema。相同术语在不同论文中也可能具有不同语义，例如 graph、repair、verify 和 update 都不能直接连接到无类型端口。

对 R-A-D-C-L 的当前判断是：
（“一个 Agent 如何使用和维护技能”的五类核心职责划分，Representation，Acquisition / Evolution，Discovery / Selection，Composition / Execution，Lifecycle Managemen）

- **Keep：** 保留五类粗粒度责任。
- **Refine：** 为 A、D、C、L 声明内部 primitive 顺序。
- **Revise：** 把 R 视为跨槽位 artifact contract；把 L 区分为 admission 和 maintenance。

### 对当前研究的影响

1. 第一轮实验应测试单槽位替换，而不是完整 Agent 移植。
2. 论文原生性能与跨框架可插拔性不能混在同一张表中，因此拆分为 Matrix A（paper-native）和 Matrix B（plugin portability）。
3. 公共 proposal envelope 只保留本次交换真正需要的字段，并记录 native payload、provenance、转换、默认、近似、丢失和不支持语义。
4. 完整 GRASP 方法只作为 native fidelity reference；它不是本周主要的可插拔结果。

## 实验结果总结

### 本周完成的实验链路

| Gate | 状态 | 结果 |
|---|---|---|
| I0 Source | 通过 | GRASP 与 SkillRL 的 source commit 和使用文件已固定 |
| I1 Split | 通过 | GRASP 的 26 个 dev 任务按 epoch-0 规则划分为无重叠 13/13 |
| I2 Native gate | 通过 | 五类候选场景与 released GRASP gate 逐字段一致 |
| I3 SkillRL source | 通过 | GLM 和 DeepSeek 输出均通过 released parser、adapter、repository 和 gate |
| I4 A0 compatibility | 通过 | GRASP 生成 1 个合法 ADD 并到达固定 gate |
| I5 A1 compatibility | 通过 | SkillRL-shaped 路径生成 3 个合法 ADD 并到达固定 gate |
| I6 paired compatibility | 通过 | 两个 cell 使用相同 evidence、library、candidate cap 和 gate |
| I6 task performance | `blocked_environment` | AgentBench 5060/5061 服务与 Docker daemon 不可用 |

### A0/A1 配对结果

| 指标 | A0：GRASP | A1：SkillRL |
|---|---:|---:|
| 合法 ADD candidates | 1 | 3 |
| 到达原生 repository | 1/1 | 3/3 |
| 到达固定 gate | 1/1 | 3/3 |
| Gate 结果 | 1 no-op | 3 no-op |
| 模型调用 | 3 | 1 |
| Prompt tokens | 3,297 | 532 |
| Completion tokens | 1,380 | 279 |
| 延迟 | 12.127 s | 3.311 s |

A0 需要分类、诊断、分组和 proposal 生成；A1 把失败分析与生成压缩在一次 writer 调用中。因此本次 A0 使用了 3 倍模型调用、6.20 倍 prompt tokens、3.66 倍延迟和 5.43 倍估算成本。

这些差异只反映**当前实现的工作流结构和运行开销**，不能解释为 SkillRL 生成的 skill 更多、更好或任务效果更强。当前 no-change fixture 只验证 repository/gate reachability 和记录完整性。


### 当前最有希望的方向

目前最有价值的结果不是“某个 proposer 得分更高”，而是已经找到一种可审计的跨论文组件比较方式：固定相邻模块，通过显式 adapter 交换单个组件，同时保存原始输出、转换记录、资源开销、拒绝、no-op 和阻塞状态。

这使可插拔性可以被进一步拆分为：直接兼容、adapter-compatible、需要邻居重写和语义不兼容，而不再只用“能不能运行”做二元判断。

## 当前问题

### 1. 严格任务性能尚未完成

13/13 split 已冻结，但当前 AgentBench 端口和 Docker daemon 不可用。因此现在只能证明 A0/A1 能接入同一个边界，不能判断哪种 proposer 对 ALFWorld task performance 更有效。



### 2. GRASP gate 存在解释风险

Gate parity 实验发现，released GRASP 的 baseline-error 记账可能让没有真实修复的候选获得正 `adjusted_score`。如果只报告最终 admission，可能把 0-fix 候选解释为有效改进。

后续需要同时报告：原生 admission、raw fixes/errors，以及要求 `actual_fixes > 0` 的 sensitivity 结果。

### 3. 当前证据范围仍然有限

目前只完成了一个槽位、两个论文组件的兼容性验证，还不能把 proposal envelope 宣称为适用于所有 skill agent 的统一 schema。SkillOps maintenance 等第二种边界尚未执行。

## 下周计划

1. **优先恢复严格性能环境：** 检查 AgentBench 服务与 Docker，完成相同 13/13 split 下的 A0/A1 task-performance 配对。
2. **增加 gate sensitivity：** 在不改变 released gate 结果的前提下，额外计算 `actual_fixes > 0` 条件，分离原生 admission 与更严格的有效改进判定。

3. **准备第二种边界：** A-slot 性能闭环后，推进 SkillOps isolated-library round trip，再测试 GRASP-updated library → SkillOps maintenance → unchanged SkillStack D/C host。
4. **控制接口扩张：** 只有新的跨论文交换确实需要某字段，或该字段能解释可复现失败时，才扩展公共 envelope。

## 希望讨论的问题

1. 论文中的核心表述是否统一使用 **adapter-compatible component portability**，避免使用过强的 plug-and-play？
2. 下周优先级应当是集中解除 13/13 task-performance 环境阻塞，还是先扩展到 SkillOps 的第二种组件边界？
3. Source-faithful SkillRL/o3 是否是必须完成的 fidelity control，还是可以保留为明确的凭证阻塞？
4. GRASP gate 的 baseline-error 行为应只作为 source finding 报告，还是需要增加一个修正版 gate 作为对照实验？
5. 在完成几个槽位、多少个跨论文组件后，才有足够证据把当前 proposal envelope 提升为更一般的接口主张？

## 证据索引

- [Week 4 内部最终总结](../00_overview/week4_final_summary_zh.md)
- [研究目标修正记录](../01_planning/decisions/week4_research_goal_corrected_zh.md)
- [六篇论文架构 crosswalk](../02_paper_analysis/architecture_crosswalk.md)
- [A-slot 集成规范](../03_protocols/integration_spec_grasp_skillrl_proposer_swap.md)
- [Plugin portability matrix](../04_matrices/matrix_b_plugin_portability.csv)
- [A0/A1 DeepSeek 配对结果](../05_experiments/a_slot_paired_deepseek_summary.md)
- [GRASP gate parity](../05_experiments/grasp_gate_parity_summary.md)
- [Provider 对比](../05_experiments/skillrl_provider_backend_comparison.md)
