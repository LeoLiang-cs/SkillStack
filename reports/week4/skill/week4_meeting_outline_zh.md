# SkillStack Week 4 组会汇报提纲

## 本次希望优先确认

1. 当前结果是否统一表述为 **adapter-compatible component portability**，不使用过强的 plug-and-play？
2. 下周先解除 13/13 task-performance 环境阻塞，还是先扩展 SkillOps maintenance？
3. Source-faithful SkillRL/o3 是否必须补跑？
4. GRASP gate 的 baseline-error 行为是否需要修正版 gate 对照？

## 1. 本周核心进展

- 研究问题从“skill 有没有用”修正为“不同论文组件能否在固定框架内单槽位替换”。
- 固定 GRASP repository 和 admission gate，只替换 A-slot：GRASP proposer 对比 SkillRL additive updater。
- 两个组件都通过显式 adapter 到达同一个未改写的 repository/gate。
- 当前结论等级是 **adapter-compatible**；兼容性已完成，任务性能仍被环境阻塞。

## 2. 论文阅读带来的关键启发

- 深读六篇论文：SkillReranker、GraSP、SkillCAT、SkillRL、GRASP、SkillOps。
- 统一提取伪代码、输入输出、中间状态、实验轴和关键消融。
- 得到八个共同 primitive：Observe、Represent、Generate、Structure、Assess、Gate、Act、Persist。
- R-A-D-C-L 判断：五类责任保留；内部 primitive 细化；R 改为跨槽位 contract；L 区分 admission 与 maintenance。
- 共同 primitive 是分析语言，不等于统一实现或统一 Skill Schema。

## 3. 实验结果与变化

### 做了什么改动

```text
A0：GRASP classify → diagnose → group → propose ─┐
                                                 ├─→ fixed GRASP gate
A1：SkillRL analyze failures → propose ADDs ─────┘
```

- 两个 cell 使用相同历史 failure、空 learned library、DeepSeek writer、三条 ADD 上限和固定 gate。
- Adapter 保留 native payload、provenance、转换类型、信息损失和不支持语义。

### 结果如何变化

| 指标 | GRASP | SkillRL |
|---|---:|---:|
| 合法 candidates | 1 | 3 |
| 到达 repository/gate | 1/1 | 3/3 |
| 模型调用 | 3 | 1 |
| Prompt tokens | 3,297 | 532 |
| 延迟 | 12.127 s | 3.311 s |
| 估算成本 | $0.00327 | $0.00060 |

- I0 source、I1 13/13 split、I2 gate parity、I4/I5/I6 compatibility 已通过。
- Source-faithful SkillRL/o3：`blocked_credentials`。
- 严格 13/13 task performance：`blocked_environment`。
- Provider-substituted flow 后续选 DeepSeek：单次匹配运行 3.144 秒，对比 GLM 105.965 秒。

### 当前最可信的解释

- 两种 A-slot 算法在工程边界上都能接入同一个 L-slot，无需重写相邻 gate。
- SkillRL 的转换更多，因此是 adapter-compatible，不是零转换 plug-and-play。
- 调用、token、延迟和成本差异说明流程结构不同，不能说明候选质量或任务效果高低。
- No-change gate 的 no-op 只说明 gate reachability，不能当作真实 ALFWorld 无收益。

## 4. 当前主要问题

1. AgentBench 服务和 Docker 不可用，任务性能比较没有完成。
2. Azure o3 凭证缺失，SkillRL 原生 updater 无法 source-faithful 执行。
3. GRASP gate 的 baseline-error 记账可能让 0-fix 候选得到正 adjusted score。
4. 当前只有一个槽位、两个组件，接口的普适性仍待验证。

## 5. 下周计划

1. 恢复 AgentBench/Docker，完成严格 13/13 A0/A1 配对性能实验。
2. 增加 `actual_fixes > 0` sensitivity，并与 released admission 并列报告。
3. 决定是否补跑 Azure o3 的 source-faithful SkillRL control。
4. A-slot 闭环后，开始 SkillOps library round trip 和 maintenance 边界实验。

## 6. 希望组会讨论的点

- “可插拔”的主张边界：adapter-compatible 是否足够构成当前贡献？
- 实验优先级：补性能证据还是扩大组件/槽位覆盖？
- Fidelity 标准：原始模型 provider 是否必须保持一致？
- Gate 处理：保留原生行为并做 sensitivity，还是同时实现修正版 gate？

## 一分钟口头版

“这一周我把问题从 skill 有没有用，修正成跨论文组件能不能单槽位替换。我固定 GRASP 的 repository 和 regression-aware gate，只替换前面的 proposer：GRASP 自己的 proposer 对比 SkillRL updater。两个组件都通过显式 adapter 到达了同一个未改写的 gate，所以第一个 A-slot 实验已经达到 adapter-compatible。

两边的流程成本差异很明显：GRASP 三次调用，SkillRL 一次；但现在只能说工作流不同，不能说 SkillRL 效果更好，因为严格 13/13 ALFWorld 性能实验仍被 AgentBench 和 Docker 环境阻塞。论文阅读方面，我把六篇方法抽象成八个 primitive，并确认 R-A-D-C-L 可以保留，但 R 要作为跨槽位 contract，L 要区分 admission 和 maintenance。

下周我建议先恢复环境完成 A0/A1 性能配对，同时给 GRASP gate 增加 actual-fixes sensitivity。之后再进入 SkillOps，验证第二种跨论文边界。希望组会确认的是：论文主张是否采用 adapter-compatible portability，以及下周先补性能还是先扩组件。”
