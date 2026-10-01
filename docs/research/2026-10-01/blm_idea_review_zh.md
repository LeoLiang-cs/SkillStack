# BLM idea 评估：大方向问题与会议档次

日期：2026-10-01 ｜ 依据：`docs/final_cards/idea.std.en.md`、`docs/plan/skillstack_research_master_plan_v4_zh.md`、`report/week8/r2_completion_record_zh.md`，以及 scoop-check（paper-search 检索 4 组查询，arXiv/Crossref 共 57 篇；Semantic Scholar/OpenAlex/OpenReview/DBLP 本次被限流或拒绝，覆盖不完整）。

## 一句话结论

方向成立，但现在只够 **workshop**。要冲 NeurIPS/ICLR/ICML/ACL 主会，需要补三样东西：**更大的实验面、处理非确定性的统计、以及"知道隐藏依赖后能做什么"的下游收益**。

## 1. 撞车检查（scoop-check）

**Verdict：Level 3 — Medium Overlap（中度重叠）**

最接近的工作（都是 2025–2026 新文）：

| 论文 | 做了什么 | 和 BLM 重合在哪 | 不同在哪 |
|---|---|---|---|
| Causal Agent Replay (CAR, arXiv 2606.08275) | 把 agent 运行建成 SCM，对某一步做 do-干预后重跑，测结果分布变化，含 Shapley 分摊交互 | 机制几乎一样：干预 + 从保存状态重放 + 结果打分 + 联合效应 | 干预单位是"步骤"，目的是失败归因；不涉及组件替换和接口声明 |
| CausalFlow (arXiv 2605.25338) | 步级反事实干预算 Causal Responsibility Score，再生成最小修复 | 机制重合 | 目标是修复/训练数据，不是接口 |
| A2P (arXiv 2509.10401)、Who&When (2505.00212) | 多智能体失败归因 | 问题邻近 | 主要靠 LLM 推理，不是真实重放 |
| The Replay Gap (arXiv 2608.08239) | 证明"换模型后拼接日志重放"会评错世界；temperature 0 并不确定 | 同样批评"静态替换评测" | 对象是模型路由，不是组件接口 |
| Skill Runtime Intelligence (arXiv 2608.08793) | 跨 harness 重建 skill 生命周期，结论"事件存在 ≠ 边界保真" | 同样关心 skill 边界保真 | 被动观测，无干预 |
| 经典：interchange intervention / causal abstraction（Geiger 等）、activation patching | 把内部变量换成另一次运行的值，看输出变化 | BLM 的"恢复原值"在概念上就是对模块 I/O 做 interchange intervention | 它们作用在神经网络内部，不在 agent 组件边界 |

**Delta（可写进论文的那句话）**：
> 不同于 CAR/CausalFlow 以"轨迹步骤"为干预单位做失败归因，BLM 以"接收方在组件边界实际读取的字段"为干预单位，在跨系统移植时检验声明接口是否完整，输出可证伪的接口证书。

这个 delta 站得住，但很窄：审稿人很可能说"这就是把 activation patching / CAR 用在模块接口上"。所以**方法本身不能当主要卖点**，卖点必须落在"发现了什么"上。

## 2. 大方向上的问题（按严重度）

1. **确定性假设站不住。** 方法写的是 temperature 0 + 8 次重放"精确比较、不做统计检验"。但 R2 用的是 DeepSeek API，Replay Gap 一文刚实测：同样 temperature 0，FP8 部署下 >90% 的分叉会发散。
   *例子*：同一个 atom 恢复前后，8 次重放里 5/8 vs 4/8 成功，你会把它判成 load-bearing，其实可能只是噪声。
   → 改法：保留 no-op 对照估噪声地板，所有 Δ 报置信区间；或用本地开源模型 + 固定推理配置。

2. **没有"所以呢"。** 现在 BLM 是审计工具：告诉你哪些未声明字段在承重。主会审稿人会问：知道了以后，移植成功率能提升吗？能预测哪些替换会失败吗？
   *例子*：把 BLM 找出的字段加进 `canonical_interface_v1.md` 后，crossed cell 的成功率从 40% 回到 70%，这才是一个能上主会的结果。
   → 至少补一个下游实验："schema-later 接口"修补后的移植收益，对比 schema-first。

3. **实验面太窄。** 一个边界、一个环境（ALFWorld）、两个适配器（GRASP、SkillRL）、少量任务。主会通常要求 ≥2 个环境（如加 WebShop 或 ScienceWorld，GraSP 本身就用了 4 个）和多对组件。

4. **对 GraSP/AgentSquare 的批评有稻草人风险。** 它们没声称"接口完整"，只是用接口做组合。批评要改写成"它们的结论隐含依赖接口完整，而我们实测它不完整，且影响 X% 的结论"。

5. **证据还是零。** R1 只是校准，R2 live 没跑，自然案例 eligible = 0。如果 R2 结果是"没有未声明承重字段"，主线论点就塌了，需要提前准备阴性结果的写法（例如作为"接口其实够用"的证据 + 方法论贡献）。

6. **方法过重。** 10 步流程、7 类事件、"恢复超过一半才算有效"这类阈值，ML 会议读者会觉得是工程规程而不是方法。论文里应压缩成一个核心估计量（式 1）+ 一个证书规则。

## 3. 能投什么档次

| 情况 | 现实档次 |
|---|---|
| 现状（只有校准） | 投不了 |
| R2 跑出 1–2 个真实案例，单环境 | 主会 agent 相关 workshop（NeurIPS/ICLR/ICML workshop），或 AAMAS 短文 |
| R2+R3 正结果 + 统计 + 2 个环境 | ACL/EMNLP Findings、AAMAS 主会、TMLR 有机会 |
| 再加下游收益（修接口后移植成功率显著提升）+ 多组件对 | NeurIPS/ICLR/ICML 主会有竞争力 |

另一条路：把卖点改成"评测方法论"，即"schema-first 移植评测会系统性误判，结论有 X% 被未声明依赖驱动"，投 NeurIPS Datasets & Benchmarks 一类 track，更契合 BLM 作为审计工具的性质。

## 4. 建议的下一步（按顺序）

1. 先跑 R2 live，但把 no-op 重复对照扩到能估噪声的量（例如每个 seed ≥16 次），先确认 DeepSeek 下能否稳定复现。
2. 若噪声大，换本地开源模型做主实验。
3. R3 设计里加入下游收益实验和第二个环境。
4. 论文定位先按 Findings/workshop 写，结果好再升级。

---

# 第二轮：假设结构做完备、实验做充分，竞争力够不够

使用 skill：idea-quality（ResearchStudio-Idea/evaluation，按 SKILL.md 执行；只评 idea 本身，不假设实验结果）。

## Idea Review — Boundary Load Maps

| 轴 | 分 (1–5) | 证据（引自 idea 卡片） | 理由 |
|---|---|---|---|
| A 问题定位 | 3 | "declares an interface before transplanting heterogeneous implementations risks absorbing the incompatibilities it set out to detect" | 问题是真的，表述也不显然；但受众窄（只关心跨系统移植 skill 组件的人），重要性要靠"多少已发表结论受影响"来证明，目前是断言 |
| B 方法质量 | 3 | "restoring atoms one at a time"；"the comparison is exact and no statistical test is involved" | depth 2–3：核心是对模块 I/O 做 interchange intervention，已知技术换场景；soundness 有缺口：依赖精确确定性，joint mask 只在"单个全为 0"的组上跑，漏掉"单个非零但联合不同"的交互，">1/2 恢复"阈值无依据；feasibility 高（R1 已建好重放和注入） |
| C 问题契合 | 4 | "censusing every atom the receiver consumes at its read points" | 方法直接测"接收方实际读了哪些未声明字段"，正中 gap；扣分在 motivation 想回答"可移植性的承重轴是不是接口覆盖"，但方法只给单边界证书 |

**Overall：58 / 100 · Verdict：borderline**（A/C 闸门未触发）

- 最强点：把"接口是否完整"从假设变成可证伪、有对照的测量，这个 framing 是对的。
- 最可修的弱点：方法深度。现在等于"逐个字段做 patching"，需要一个自己的方法贡献。

## 结论：做完整后的竞争力

照现有方法设计，即使实验充分，**上限是主会 borderline（NeurIPS/ICLR 分数在 5 分线附近），更稳的是 Findings / TMLR**。卡住的不是实验量，而是两点：
1. 方法深度：审稿人会说"这是 activation patching / CAR 用在组件边界"。
2. 问题范围：只服务 skill 组件移植这一小圈子。

## 方法还需要研究什么（能把 B 和 A 拉上去的方向）

1. **自适应 / 分组测试找承重集合**（提升 depth）。逐个恢复要 O(n) 次重放；把字段分组恢复、二分定位，在 k 个承重字段时只要 O(k log n) 次，并给出漏检概率界。
   例子：200 个 atom、3 个承重，逐个要 200×16 次重放，分组二分大约 30×16 次。
2. **随机性下的证书**（修 soundness）。把"精确相等"换成带噪声地板的序贯检验，证书写成"在 α 水平下不可证伪"。这也直接回应 Replay Gap 的批评。
3. **交互发现**（修 soundness）。不只在"单个全为 0"的组上做 joint mask，而是估计二阶交互（Shapley / Möbius 截断），解释"恢复 A 和 B 单独都有用，一起更有用"。
4. **闭环：从 load map 合成接口并验证**（提升 A 和 C）。schema-later 接口自动生成后，重新移植，看成功率恢复多少。这是"所以呢"。
5. **扩大问题**（提升 A）。把对象从"skill 组件"推广到任意 LLM pipeline 的交接点：tool/MCP 返回值、多智能体消息、RAG 的检索结果。审稿人更在乎这个面。

如果做了 1+2+4，B 可到 4，A 可到 4，估计 overall 75 左右，是"strong"，主会有竞争力。
