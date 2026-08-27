# SkillStack Week 4——第六次导师简报（中文版）

- **当前状态：** 第一个跨论文单槽位实验已完成到兼容性层；严格任务性能实验因 AgentBench/Docker 环境不可用而按协议阻塞。
- **一句话结论：** GRASP proposer 与 SkillRL additive updater 可以通过显式 adapter 接入同一个、未改写的 GRASP repository 和 admission gate；这证明了 **A-slot 的 adapter-compatible 可替换性**，但还不能比较两者的任务效果。

## 1. 与上周相比，研究问题发生了什么变化

Week 3_2 研究的是 SkillStack 内部的 Retriever × Executor 组合，以及 skill 内容是否影响执行。Week 4 根据会议结论把主问题收窄为：

> 不评价某种 skill 方法“有没有用”，而是固定 task、evidence、library、gate 和 evaluator，只替换一个论文组件，检查不同论文算法能否真正拼接，以及转换代价在哪里。

因此，本周没有把整套论文 agent 搬进 SkillStack，而是选择两篇公开实现中边界最清楚的 acquisition/evolution 组件：

```text
A0: GRASP classify → diagnose → group → propose ─┐
                                                 ├─→ fixed GRASP repository + gate
A1: SkillRL analyze failures → propose ADDs ─────┘
```

这个设计只改变 A-slot proposer，Lifecycle admission、起始 library、failure evidence、candidate cap 和记录链路保持一致。

## 2. 本周完成了什么

1. 深读六篇论文，分别提取伪代码、输入输出、中间状态、实验轴和关键消融，形成六张 Algorithm Card。
2. 把六种方法抽象为八个共同 primitive：Observe、Represent、Generate、Structure、Assess、Gate、Act、Persist。
3. 重新检查 R-A-D-C-L：五类责任可以保留，但 R 应视为跨槽位 artifact contract，L 应区分 admission 与 maintenance。
4. 冻结两套矩阵：Matrix A 保存论文原生实验设计；Matrix B 专门记录单槽位可插拔性、adapter friction、成本和失败。
5. 建立最小 proposal envelope，并实现 GRASP→proposal、SkillRL→GRASP 等显式 adapter；原始模型输出、转换方式、信息损失和不支持语义均被保留。
6. 接通 GRASP 原生 `validate → fork → apply → cleanup` repository 路径，并完成 released gate parity。
7. 在相同历史 failure、空 learned library、DeepSeek writer、三条 ADD 上限和固定 gate 下完成 A0/A1 配对兼容性实验。

## 3. 配对兼容性结果

| 指标 | A0：GRASP proposer | A1：SkillRL updater |
|---|---:|---:|
| 合法 ADD candidates | 1 | 3 |
| 到达原生 repository | 1/1 | 3/3 |
| 到达固定 gate | 1/1 | 3/3 |
| Gate 结果 | 1 no-op | 3 no-op |
| 模型调用 | 3 | 1 |
| Prompt tokens | 3,297 | 532 |
| Completion tokens | 1,380 | 279 |
| 延迟 | 12.127 s | 3.311 s |
| 估算成本 | $0.00327228 | $0.00060236 |

A0 的工作流更长，需要分类、诊断、分组和生成；A1 把失败分析与候选生成压在一次 writer 调用里。本次 A0 使用 3 倍调用、6.20 倍 prompt tokens、3.66 倍延迟和 5.43 倍估算成本。

这些数据说明的是**工作流结构和运行开销差异**，不能解释为 SkillRL 质量更高。当前 gate 使用确定性的 no-change fixture，只验证候选是否能到达相同边界并留下完整决策记录。

## 4. Gates 与阻塞状态

| Gate | 状态 | 解释 |
|---|---|---|
| I0 Source | 通过 | 两个源仓库 commit 和使用文件已固定 |
| I1 Split | 通过 | GRASP 的 26 个 dev 任务按 epoch-0 规则分成严格、无重叠的 13/13 |
| I2 Native gate | 通过 | 五类候选情形与 released GRASP gate 逐字段一致 |
| I3 SkillRL source-faithful | `blocked_credentials` | 原实现需要 Azure o3 key/endpoint；prompt、parser 和 recorder 已完成，没有伪造输出 |
| I3 provider-substituted | 通过 | GLM 和 DeepSeek 的真实输出都经过 released parser、adapter、repository 和 gate |
| I4 A0 compatibility | 通过 | GRASP 产生 1 个合法 ADD 并到达固定 gate |
| I5 A1 compatibility | 通过 | SkillRL-shaped 路径产生 3 个合法 ADD 并到达固定 gate |
| I6 paired compatibility | 通过 | 两个 cell 使用相同 evidence、library、cap 和 gate |
| I6 task performance | `blocked_environment` | AgentBench 5060/5061 服务和 Docker daemon 不可用 |

## 5. 最重要的发现

1. **A-slot 可以跨论文替换，但当前准确等级是 adapter-compatible。** 两边都不需要修改 GRASP 的 repository 或 Lifecycle gate；SkillRL 端仍需显式合成 action、重命名 title、构造 Markdown content 和 tags，因此不能称为零转换的 plug-and-play。
2. **公共接口应保持小。** 当前真正共同需要的只有 action、name、description、content、tags、evidence IDs 和 provenance。proposal envelope 是实验边界，不应提前升级为所有论文都必须服从的统一 Skill Schema。
3. **Adapter 不对称本身就是研究结果。** GRASP 基本是字段复制加 provenance；SkillRL 需要更多可见转换，但没有要求相邻 L-slot 重写，也没有伪造其不支持的 MODIFY/REMOVE 能力。
4. **失败和阻塞被保留。** Source-faithful SkillRL、严格任务性能、reject/no-op、原始模型输出和转换记录都没有被“跑通流程”掩盖。
5. **发现一个 gate 解释风险。** Released GRASP gate 的 baseline-error 记账可能让没有真实修复的候选得到正 adjusted score。后续必须同时报告原生 admission、raw fixes/errors，以及要求 `actual_fixes > 0` 的 sensitivity 结果。
6. **DeepSeek 是后续替代 writer 的运行选择。** 同一 fixture 下，DeepSeek 为 3.144 秒，GLM 为 105.965 秒，单次延迟下降 97.03%；但这只是一次匹配运行的工程选择，不是稳定速度 benchmark，也不是质量比较。

## 6. 现在可以主张的结论

1. GRASP proposer 和 SkillRL additive updater 可以进入同一个未改写的 GRASP repository/gate 边界。
2. 第一个跨论文 A-slot swap 达到 adapter-compatible，且转换与信息损失可以审计。
3. 两种算法的调用结构、token、延迟、成本和 adapter friction 明显不同。
4. R-A-D-C-L 作为粗粒度责任划分基本合理，但内部 primitive、artifact contract 和 admission/maintenance 区分必须显式化。

## 7. 仍然不能主张的结论

1. SkillRL 比 GRASP 更有效，或生成的 skill 质量更高。
2. 当前结果复现了完整 SkillRL 或完整 GRASP 论文性能。
3. DeepSeek 比 GLM 的候选质量更好。
4. No-change gate 的 no-op 等于真实 ALFWorld 上没有收益。
5. 该接口已经适用于所有 skill agent；当前只有一个跨论文槽位和两个组件的证据。

## 8. 建议的下一步

1. **优先解除严格性能阻塞：** 恢复 AgentBench/Docker 服务，完成相同 13/13 split 下的 A0/A1 task-performance 配对。
2. **增加 gate sensitivity：** 除 released admission 外，额外报告 `actual_fixes > 0` 的结果，避免 baseline-error 记账造成误判。
3. **决定 source-faithful SkillRL 的必要性：** 若能获得 Azure o3 凭证，再跑原生 I3；否则继续把 DeepSeek 路径明确标成 provider-substituted，而不是论文复现。
4. **完成第二种边界验证：** 在 A-slot 性能闭环后，再推进 SkillOps maintenance，使一个跨论文产生的 library 经维护后继续被不变的 D/C host 消费。

## 9. 希望与导师讨论的决策

1. 论文主张是否使用“adapter-compatible component portability”，而不使用过强的“plug-and-play”？
2. 下周是否应先集中解决 13/13 task-performance 环境，还是直接扩展到 SkillOps 的第二种边界？
3. Source-faithful SkillRL/o3 是否是必须完成的 fidelity control，还是保留为凭证阻塞即可？
4. GRASP gate 的 baseline-error 边界应作为实现发现报告，还是进一步设计修正版 gate 对照？

## 10. 四页汇报结构

1. **问题变化与设计：** 从“skill 有没有用”转向“跨论文组件能不能插”；固定 gate，只换 A-slot。
2. **架构与接口：** 六篇论文、八个 primitives、R-A-D-C-L 修正、最小 proposal envelope。
3. **配对证据：** A0/A1 repository/gate reachability、adapter friction、调用与成本；明确 compatibility 与 performance 的边界。
4. **阻塞与决策：** 13/13 performance、source-faithful SkillRL、gate sensitivity、下一种 SkillOps 边界。

## 11. 口头汇报稿

“这一周我们把研究问题修正了。重点不再是证明某种 skill 到底有没有用，而是看不同论文里的组件能不能在同一个框架里真正拼接。因此我没有迁移整套 agent，而是固定 GRASP 的 repository 和 regression-aware gate，只替换前面的 A-slot：一边是 GRASP 自己的 proposer，一边是 SkillRL 的 additive updater。

结果是兼容性已经跑通。两边都能经过显式 adapter 到达同一个没有改写的 repository 和 gate。GRASP 产生一个合法 ADD，SkillRL 路径产生三个，全部留下原始输出、转换过程和 gate 记录。这个结果应该叫 adapter-compatible，而不是完全 plug-and-play，因为 SkillRL 需要显式构造 action、名称、content 和 tags，但没有要求我们重写后面的 Lifecycle gate。

两种算法的结构差异也很明显：GRASP 要做分类、诊断、分组和生成，一共三次模型调用；SkillRL 路径一次 writer 调用就完成。在这次配对里，GRASP 的 prompt tokens、延迟和成本都更高。不过这只能说明工作流开销不同，不能说明谁生成的 skill 更好。

现在最大的边界是任务性能还没跑完。严格 13/13 split 已经准备好，但 AgentBench 服务和 Docker 环境不可用，所以我们只证明了组件能接上，还没有证明替换后任务效果如何。下一步我建议先恢复这个环境，完成 A0/A1 的严格性能配对，并增加一个要求 actual fixes 大于零的 gate sensitivity，避免原生 gate 的 baseline-error 记账影响解释。之后再扩展到 SkillOps maintenance，验证第二种跨论文边界。”

