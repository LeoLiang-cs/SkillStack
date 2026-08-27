# Week 4 研究目标修正版

**修正日期：** 2026-08-26  
**状态：** 当前 Week 4 的控制目标

## 一句话目标

> 不是把一整套论文 Agent 搬进 SkillStack，而是固定其他模块，只替换一个
> 论文中的组件，检查它能不能通过明确 adapter 接上、是否需要偷改邻居，
> 以及原来的性能和失败特征还能保留多少。

## 为什么需要修正

Day 1–3 对论文机制和边界的分析是必要的，但 Day 4 把“完整 GRASP
`Method.run()` 接入另一个 host”放到了首要位置。这能测试整套方法的
host portability，却不是原始 SkillStack 最核心的 slot-level
interchangeability。如果继续沿这条路线，论文贡献容易变成“移植完整
agent”，而不是“研究不同论文组件能否真正拼接”。

因此，完整方法接入降为 **原生基线和辅助实验**；跨论文、单槽位替换恢复为
本周主实验。

## 修正后的研究问题

在 task、library、host、evaluator、budget 和其他组件全部固定时：

1. 论文 A 的某个组件能否替换同一槽位中的组件 B？
2. 是否只需要边界 adapter，而不需要修改其他槽位的算法？
3. adapter 读取、生成、近似、默认或丢弃了什么信息？
4. 替换后，任务表现、成本、拒绝、回归和失败类型如何变化？
5. 如果不能拼接，问题来自 schema、语义、evidence authority、host，还是
   组件本身？

## 本周的主次关系

### 主线：slot-level 跨论文组件实验

- `A` proposal：GRASP proposer 与 SkillRL released additive updater。
- `L` admission：固定使用 GRASP regression-aware gate。
- 其他部分全部固定：failure batch、probe、task、library、evaluator、budget
  和 repository behavior。

第一个主比较是：

```text
GRASP proposer ─┐
                ├─→ fixed GRASP gate ─→ accepted/rejected/no-op + library version
SkillRL updater ─┘
```

SkillRL updater 只支持 ADD，缺少 GRASP 的 MODIFY/REMOVE 语义。adapter 必须
把这种能力差异明确记录下来，不能补写成不存在的能力。即使最终不兼容，
也是有效的接口研究结果。

### 第二主线：跨论文顺序组合

```text
GRASP-updated library → SkillOps maintenance → unchanged SkillStack D/C host
```

该实验检查一个方法产生的 library 能否被另一个方法维护，并继续被不变的
retriever/executor 消费。

### 辅助线：完整方法基线

完整 GRASP `Method.run()` 仍然运行，但用途仅为：

- 确认官方实现和原生 artifacts；
- 建立 proposer/gate 的 native reference；
- 判断后续拆出的组件行为是否偏离原方法。

它不是主要的“可插拔成果”。完整方法通过 SkillStack Task adapter 的测试
降为后续 host-portability 实验。

## 之前成果如何处理

Week 2–3 的工作不作废：

- lexical/task-semantic retriever 是 `D` 槽位的本地基线；
- flat/structured ReAct 是 `C` 槽位的本地基线；
- Week-3.2 的 2×2 traces 用于验证 matrix schema、paired comparison 和
  failure taxonomy；
- canonical interface v1 是从本地摩擦归纳出的 empirical interface，
  不是六篇论文都必须遵守的预设 schema；
- 原来的 success/steps/tokens/cost 继续保留，但解释为 portability 结果，
  不再用于回答“skills 是否有用”。

## 本周完成标准

Week 4 完成时必须具备：

1. 六篇论文的算法卡和共同 primitives；
2. paper-native Matrix A；
3. 以槽位替换为主的 Matrix B；
4. 第一个 `A proposer` swap 的明确 I/O、adapter、固定邻居和停止条件；
5. 完整 GRASP native baseline 的角色说明；
6. blocked、rejected、no-op 和失败输出完整保留；
7. 在实施前完成 Week-3.2 historical-trace schema dry-run。

## 判断标准

- **真正 plug-and-play：** 只新增通用注册/config，不改邻居。
- **adapter-compatible：** 需要显式转换，但邻居算法不变。
- **需要邻居重写：** 能运行，但不能称为可插拔。
- **语义不兼容：** 格式能转换，真正需要的 evidence/authority/operation
  仍无法保留。

最终不以“谁分数最高”为唯一结论，而回答：哪里能插、哪里不能插、为什么，
以及代价是什么。
