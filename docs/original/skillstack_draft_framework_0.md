# SkillStack：面向可组合 Skill Agent 的参考架构与实验框架

## Abstract

现有 Skill Agent 研究分别关注技能生成、检索、编排、执行、演化与维护，但大多以端到端系统呈现。不同系统采用不同的 skill representation、state abstraction、failure signal 与 update semantics，使得研究者难以回答两个基础问题：一个模块能否脱离原系统被其他实现替换，以及多个单独有效的模块组合后是否仍然有效。本文提出 **SkillStack**，一个面向 Skill Agent 的 reference architecture 与 modular experimental harness。SkillStack 将 Skill Agent 概括为五类稳定职责：Representation、Acquisition/Evolution、Discovery/Selection、Composition/Execution 和 Lifecycle Management；同时在实验层面定义四个可替换槽位，并要求每个槽位至少包含两个机制上真正不同的实现。

与先设计统一 schema 再适配现有方法的路线不同，SkillStack 采用 **implementation-first, schema-later** 的开发方法：首先保留各方法的原生数据结构，使用可追踪的 hard-coded adapters 在 ALFWorld 上跑通真实组合实验；随后根据实际接口摩擦、信息丢失和失败案例，逐步归纳最小 Canonical Skill Interface。实验将测量 implementation interchangeability、performance portability 和 cross-module interaction，并将 applicability mismatch 作为 interface leakage 与 hidden coupling 的案例研究。SkillStack 的目标不是提出另一套 skill taxonomy，也不是简单整合多个 SOTA 模块，而是提供一种可执行的方法，研究 Skill Agent 组件是否能够真正替换、组合和共同演化。

## 1. Introduction

Large Language Model agents increasingly externalize reusable procedural knowledge as skills. A skill may be natural-language guidance, executable code, a workflow graph, or a structured package containing instructions, tools and validation logic. Recent work has demonstrated that skills can improve long-horizon planning, reduce repeated exploration, transfer experience across tasks, and support continual agent improvement.

然而，当前研究通常围绕某一个完整 pipeline 展开。例如，一个系统同时规定 skill 的表示方式、检索方法、执行器和更新规则，然后只报告整个系统相对于 baseline 的提升。这种评估方式无法说明改进究竟来自哪个组件，也无法判断某个模块能否离开原系统继续工作。一个 retriever 在自己的 planner 上有效，不代表它能够与另一个 graph executor 组合；一个 evolution method 能生成高质量 skill，也不代表这些 skill 能被其他 retrieval 或 maintenance system 正确理解。

现有系统之间还可能存在大量 **hidden coupling**。组件表面上交换的是 skill ID、description 或 execution trace，实际上却隐含依赖特定的 state representation、precondition semantics、failure label 或 evidence format。当第二个实现接入时，这些隐藏假设才会暴露。此时，一个形式上正确的接口仍可能在语义上失效。

本文提出 SkillStack，将研究重点从“整合更多模块”转向以下问题：

> **Skill Agent 的组件能否在统一实验框架中被替换和组合？如果不能，失败暴露了哪些必须进入接口的语义？**

本文预期贡献如下：

1. **Skill Agent Reference Architecture。** 将 Skill Agent 定义为五类稳定职责，而不是绑定某几篇论文或固定八个模块。
2. **Modular SkillStack Harness。** 为四个实验槽位提供至少两个机制上不同的实现，支持 controlled swap 与 interaction experiments。
3. **Empirically Derived Canonical Interface。** 不预先设计大而全的 schema，而是从真实方法接入、转换损失和失败案例中归纳最小接口。
4. **Composability Analysis。** 系统测量 implementation interchangeability、performance portability、cross-module interaction 与 hidden coupling，并以 applicability mismatch 作为具体案例。

## 2. Related Work

### 2.1 Skill Discovery and Retrieval

Skill retrieval 研究关注如何从不断扩大的 skill library 中选择与当前任务相关的技能。Embedding Top-k 是常见 baseline，但仅依赖任务与 skill 文本的语义相似度，往往无法判断 skill 是否适用于当前执行状态。SkillReranker 通过任务分解、状态描述与 reranking 改善技能选择，并在 ALFWorld 和 ScienceWorld 上进行实验。SkillRouter、Graph of Skills 和 SkillDAG 进一步研究 large-scale routing、dependency-aware retrieval 与 execution-backed graph evolution。

这些工作表明 retrieval 已经从简单相似度搜索发展为结构化选择问题，但其输出通常与特定 skill representation 和 downstream planner 紧密耦合。SkillStack 不提出新的通用 retriever，而是比较 retrieval 实现能否在不同 composition/execution 方法下保持收益。

### 2.2 Skill Composition and Execution

被选中的 skills 不一定能够直接执行。GraSP 将 flat skill set 编译为带有 precondition/effect 关系的 typed DAG，并结合 node-level verification 与 local repair，在 ALFWorld、ScienceWorld、WebShop 和 InterCode 上进行评估。这类工作说明，结构化编排可能比简单增加 skill 数量更重要。

然而，graph planner 往往需要上游提供显式 preconditions、effects 和 dependencies，而 flat retriever 可能只返回 description。SkillStack 将这种表示与执行之间的依赖视为需要实验验证的 interface assumption。

### 2.3 Skill Acquisition and Evolution

SkillRL 从交互经验中构建 hierarchical SkillBank，并使 skill library 与 agent policy 共同演化。SkillCAT 使用成功/失败轨迹对比、assessment-gated evolution 和 topology-aware execution，在 SpreadsheetBench、WikiTableQuestions 与 DocVQA 上评估。GRASP 则使用 held-out regression probes 控制 skill edits 的准入，避免修复一个失败时破坏已有成功行为。

这些方法的 evidence source、patch format、validation rule 和 target environment 并不相同。因此，skill evolution 不能被默认视为一个可以直接插入任意 agent 的独立模块。SkillStack 将 proposal generation 与 governance/admission 分开，以研究更新方法与准入策略之间的 interaction。

### 2.4 Skill Lifecycle and Maintenance

SkillOps 将 skill library 视为需要长期维护的软件生态，通过 typed skill contracts、hierarchical ecosystem graph 和 health indicators 管理 skill technical debt。MUSE-Autoskill 覆盖 creation、memory、management、evaluation 和 refinement，说明 unified skill lifecycle 已经是现有研究主题。

因此，本文不声称是第一个整合 skill lifecycle 的系统。SkillStack 的区别在于：将 lifecycle 中的职责实现为可替换实验槽位，并测试来自不同方法的组件能否实际组合。

### 2.5 Taxonomies and Reference Models

Dynamic Agent Skills survey 已提出 skill taxonomy、八阶段 lifecycle、skill-record schema 与 update-operator vocabulary，为比较动态 skill systems 提供了共同语言。Taxonomy 回答的是“领域中有哪些阶段与方法”；SkillStack 关注的是“这些阶段之间需要交换什么，以及不同实现是否真的能够互操作”。

简言之：

> **Existing surveys define vocabulary; SkillStack derives and evaluates executable interfaces.**

## 3. Problem Formulation

### 3.1 Five Core Responsibilities

SkillStack 将一个 Skill Agent 表示为：

\[
\mathcal{A}=(R,A,D,C,L)
\]

其中：

- \(R\)：**Representation**，定义 skill 的内容、形式和可观察属性；
- \(A\)：**Acquisition/Evolution**，负责生成、修改、合并或拆分 skill；
- \(D\)：**Discovery/Selection**，根据 task 和 state 选择候选 skill；
- \(C\)：**Composition/Execution**，组织、执行并验证 selected skills；
- \(L\)：**Lifecycle Management**，负责评估、准入、版本、回滚与退役。

这些是 conceptual responsibilities，而不是必须一一对应的代码模块。一个具体系统可以合并若干职责，但必须明确它们之间共享了哪些内部假设。

### 3.2 Research Questions

**RQ1：Reference Architecture。** 五类职责是否足以描述代表性 Skill Agent，同时避免绑定固定实现？

**RQ2：Interchangeability。** 当某一槽位的实现被替换时，其他组件能否在不重写的情况下继续运行？

**RQ3：Composability。** 两个单独有效的实现组合后，是协同、独立、冗余还是相互干扰？

**RQ4：Interface Leakage。** 组合失败暴露了哪些隐藏语义，哪些信息必须进入共享接口？

## 4. SkillStack Framework

### 4.1 Conceptual Architecture and Experimental Slots

Reference architecture 保留五类职责，但 P0 不把 Representation 单独作为算法槽位。Representation 首先保留为各方法的 native artifact，随后根据跨组件实验逐步形成共享接口。

实验 harness 包含四个可替换槽位：

| 槽位 | 实现 A | 实现 B | 机制差异 |
|---|---|---|---|
| **S1 Acquire / Propose** | 单轨迹反思与 skill rewrite | 成功/失败多轨迹对比抽取与 patch proposal | 单样本反思 vs 对比证据驱动更新 |
| **S2 Retrieve** | embedding Top-k | state-aware task decomposition + reranking | 全局语义相似度 vs 状态与子任务感知选择 |
| **S3 Compose / Execute** | flat skill injection + ReAct | precondition/effect graph + node verification | 非结构化执行 vs 显式依赖图执行 |
| **S4 Govern / Admit** | usage/failure statistics + threshold maintenance | held-out regression gate + admission/rollback | 统计规则维护 vs 回归证据驱动准入 |

每个槽位必须包含两个机制上真正不同的实现。以下情况不计为两个实现：

- 同一算法使用不同 Top-k；
- 同一 prompt 使用不同 backbone；
- 同一实现仅改变阈值；
- `no-op` 与一个有效方法。

`no skill`、`no evolution` 和 `no governance` 可以作为 ablation/control，但不满足双实现要求。

### 4.2 Implementation-First, Schema-Later

SkillStack 不在项目开始时定义完整 Canonical Skill Schema。这样做容易产生一个形式完整但未经执行验证的接口，并导致大量时间消耗在反复修改字段，而不是研究组件是否真正兼容。

第一阶段采用以下流程：

```text
Native Implementation A ── hard-coded adapter ──┐
                                                ├── Minimal Harness ── ALFWorld
Native Implementation B ── hard-coded adapter ──┘
```

具体原则为：

1. 保留每个方法原生的数据结构和 prompt，不提前强制转换为统一 skill object；
2. 使用最小、显式、可检查的 adapter 连接第一批实现；
3. 记录 adapter 读取、生成、丢弃或猜测的所有信息；
4. 只有当一个字段被至少两个实现需要，或能解释可复现的接口失败时，才将其加入 shared interface；
5. 方法特有信息继续保存在 native payload 中，不为了形式统一而丢失语义；
6. 完成每个槽位的双实现和 swap experiments 后，再冻结 Canonical Interface v1。

因此 Canonical Skill Interface 是本文的 **empirical output**，而不是实验前提。

### 4.3 Minimal Runtime Harness

P0 只固定运行实验所必需的最小 envelope：task identifier、raw observation、native skill payload、component output、environment action、outcome 和 timestamp。它们可以先使用普通 dictionary 和 JSON logs，不需要提前实现复杂 typed schema。

每次 episode 至少保存：

- task instruction 与 raw observations；
- skill library 和实现版本；
- retrieved candidates、scores 与 selector 原始输出；
- planner/executor 原始输入输出；
- environment actions、observations 和 rewards；
- success/failure 与资源消耗；
- adapter transformations 和 warnings。

这些 trace 用于发现接口摩擦，并支持后续 replay、failure attribution 与 schema induction。

## 5. Experimental Design

### 5.1 Environment

P0 仅使用 **ALFWorld**。相关工作的 benchmark 并不完全重合，将所有方法同时迁移到 ALFWorld、ScienceWorld 和 WebShop 会引入额外 porting confound。ALFWorld 同时具有长程任务、明确状态变化和可观察执行失败，适合初步研究 retrieval、composition 与 applicability。

只有在 P0 pipeline 和接口归纳稳定后，才考虑扩展到 ScienceWorld 或 WebShop。

### 5.2 P0: Retrieval × Composition

第一阶段先研究最短可执行链路：

```text
Static Skill Library → Retrieval → Composition/Execution → Trace
```

Acquisition 使用固定静态库，Governance 只记录证据而不修改 library。它们在 P0 中是 placeholder，不计入最终的双实现要求。

P0 包含四个配置：

| 配置 | Retrieve | Compose / Execute |
|---|---|---|
| B00 | Embedding Top-k | Flat ReAct |
| B10 | State-aware Reranker | Flat ReAct |
| B01 | Embedding Top-k | Graph Planner |
| B11 | State-aware Reranker | Graph Planner |

这组实验首先回答：两个 selector 和两个 composer/executor 是否能通过最小 adapter 互换，以及它们之间是否存在 interaction。

### 5.3 Interchangeability Evaluation

当替换一个实现时，记录：

- 是否需要修改无关组件；
- adapter 中新增了多少 method-specific branches；
- 是否增加额外 LLM calls 或 context；
- 是否出现格式错误、信息缺失或无法执行的输出；
- 该方法在不同搭配中是否保持相对收益。

若一个方法仅在原生搭配中有效，它仍可能是优秀方法，但不能被视为通用 plug-and-play component。这种结果将被报告为 coupling，而不是简单归因于“集成失败”。

### 5.4 Cross-Module Interaction

对于两个二元实现 A 和 B，定义 interaction：

\[
I_{A,B}=Y_{11}-Y_{10}-Y_{01}+Y_{00}
\]

其中 \(Y\) 可以是 success rate、reward、steps 或 token cost。

- \(I_{A,B}>0\)：synergy；
- \(I_{A,B}\approx0\)：approximately independent；
- \(I_{A,B}<0\)：redundancy 或 negative interaction。

最终虽然每个槽位有两个实现，但不运行完整 \(2^4\) 或 \(2^5\) factorial。实验采用：

1. 固定 baseline configuration；
2. 每个槽位的 one-at-a-time swap；
3. 有明确假设的 pairwise interaction；
4. 只有在发现显著 interaction 后才扩展更多组合。

优先研究：

- Retrieval × Composition；
- Representation × Retrieval；
- Acquisition × Governance；
- Composition × Governance。

### 5.5 Applicability Mismatch as a Case Study

Applicability mismatch 被定义为 interface leakage 的候选案例，而不是预设成立的独立方法贡献。可能的失败链路为：

```text
Retriever 因语义相关而选择 skill
→ Planner 默认前置条件成立
→ Executor 在错误状态调用 skill
→ 执行失败
→ Governance 将失败归因于 skill implementation
```

实验将检查：

1. retrieval、planning、execution 和 governance 是否维护了不同的 applicability 假设；
2. applicability mismatch 占失败案例的比例；
3. mismatch 是否集中出现在特定组件组合；
4. 哪些状态或条件字段需要进入 Canonical Interface。

只有当信号足够强时，才进一步测试 Restrict、Split、Dependency insertion 和 failure re-attribution。若信号较弱，则将其报告为 negative finding，不强行扩展为 method contribution。

### 5.6 Metrics and Controls

**Task performance**

- success rate；
- normalized reward；
- ALFWorld task-type performance。

**Efficiency**

- environment steps；
- model calls；
- input/output tokens；
- latency 与估算成本。

**Interoperability**

- successful swap rate；
- unrelated component modifications；
- adapter-specific branches；
- missing or approximated information；
- performance portability across pairings。

**Failure analysis**

- retrieval failure；
- applicability failure；
- planning failure；
- executor deviation；
- validator failure；
- skill implementation failure；
- adapter semantic loss；
- indeterminate。

所有比较固定 environment version、task split、skill library、backbone、decoding parameters、prompt budget 和 retry policy。方法必须增加的额外调用可以保留，但需要单独报告。

## 6. Execution Plan

### 6.1 P0：先获得真实实验（Week 1）

**Day 1：ALFWorld baseline**

- 跑通无 skill 或 ReAct baseline；
- 建立小型 static skill library；
- 固定 task IDs、model settings 和基础日志。

**Day 2：第一个真实 pipeline**

- 实现 Embedding Top-k + Flat ReAct；
- 直接使用 native skill format；
- 只写最小 hard-coded adapter；
- 完整运行若干 smoke-test episodes。

**Day 3：第二个 Retrieval 实现**

- 接入 state-aware reranker；
- 不修改 downstream executor；
- 记录为了接入它实际缺失的 state 信息。

**Day 4：第二个 Composition/Execution 实现**

- 接入 minimal graph planner；
- 不提前定义统一 precondition/effect schema；
- 用 adapter 从现有 skill 中提取或临时补充 planner 所需信息；
- 明确记录所有 heuristic 与 information loss。

**Day 5：2 × 2 pilot**

- 运行 B00、B10、B01、B11；
- 比较 success、steps、tokens 和运行错误；
- 检查组件 swap 是否需要无关代码修改。

**Weekend：failure audit**

- 运行约 20–50 个 episodes，视成本调整；
- 人工检查 5–10 个 failure traces；
- 建立第一版 adapter-friction ledger；
- 只列出实验实际需要的候选共享字段，不立即冻结 schema。

### 6.2 P1：补齐四个实验槽位（Weeks 2–4）

- 完成 Acquire/Propose 的两个实现；
- 完成 Govern/Admit 的两个实现；
- 对每个槽位运行 controlled swap；
- 区分 proposal generation 与 admission decision，避免将 SkillCAT 或 SkillOps 的内部子模块错误地当作独立 intervention；
- 维护 native-to-native adapter 与 friction ledger。

### 6.3 P2：归纳 Canonical Interface v1（Week 4）

只有在四个槽位均有双实现并完成初步 swap 后，才整理接口：

- 哪些字段被多个实现共同需要；
- 哪些字段用于解释已复现的失败；
- 哪些信息应保留在 native payload；
- 哪些转换无法无损完成；
- 哪些接口属于 required、optional 或 extension。

随后再实现类型检查、版本控制、conformance tests 和 adapter documentation。

### 6.4 P3：Interaction and Case Study（Week 5+）

- 完成有假设的 pairwise interaction experiments；
- 分析 synergy、redundancy 与 negative interaction；
- 定位 repeated hidden coupling；
- 根据证据决定是否扩展 applicability intervention；
- P0/P1 稳定后再加入第二个环境。

## 7. Expected Outcomes

项目可能得到三类同样有价值的结果：

1. **多数实现能够互换。** 说明归纳出的最小接口足以支持可组合 Skill Agent。
2. **只有部分组合有效。** 说明模块具有条件性的 performance portability，SkillStack 可以识别兼容边界。
3. **大量组合失败。** 若失败可由重复的 hidden assumptions 解释，则说明当前方法并不真正 modular，接口泄漏本身构成重要发现。

因此，SkillStack 的成功不要求证明所有组件都能 plug-and-play；它要求能够受控地说明哪些组件可以组合、哪些不能，以及为什么。

## 8. Risks and Mitigations

### 8.1 Novelty Collision

MUSE-Autoskill、SkillOps、Dynamic Agent Skills survey 及新的 interoperability work 可能覆盖 lifecycle、schema 或 reference model。

**Mitigation：** 不使用“first integrated skill system”；将核心贡献限定为 multi-implementation harness、empirically derived interface 和 composability analysis。

### 8.2 Schema Work Replaces Experimental Work

项目可能再次陷入提前设计复杂 schema、反复改字段而没有运行结果。

**Mitigation：** Week 1 禁止冻结 canonical schema；所有新增共享字段必须关联具体实现需求或复现失败；P2 前只维护 friction ledger。

### 8.3 Porting Distorts Methods

不同论文使用不同环境、模型和 skill format，简化实现可能不再忠实于原方法。

**Mitigation：** 明确区分 faithful reproduction 与 method-inspired implementation；记录 adapter、额外调用和被省略机制；不直接与原论文绝对分数比较。

### 8.4 Combinatorial Explosion

四个双实现槽位已有 16 个组合，加入环境、模型和 seeds 后成本迅速扩大。

**Mitigation：** 采用 baseline swaps 和 hypothesis-driven pairwise interactions，不做全 factorial。

### 8.5 Shared Assumptions Break Causal Interpretation

同一论文中的多个子模块可能共享 representation、prompt 和 validation rule，不是独立 intervention。

**Mitigation：** 按机制和论文 lineage 报告实现；避免把 SkillCAT 或 SkillOps 内部组件简单拆成相互独立槽位。

### 8.6 Ambiguous Failure Attribution

一次失败可能同时涉及 retrieval、state、planner、executor 和 skill content。

**Mitigation：** 使用 raw trace、成功/失败配对、state separability 和可行的 counterfactual replay；允许 `indeterminate`，不强行归因。

## 9. P0 Success Criteria

第一周结束时必须满足：

- ALFWorld baseline 可稳定复现；
- 两个机制上不同的 retriever 可以在不重写 executor 的情况下替换；
- 两个机制上不同的 composer/executor 可以在不重写 retriever 的情况下替换；
- 四个 P0 组合均能生成可比较的 raw traces；
- 已记录具体 adapter friction、缺失信息与失败案例；
- 能基于实验说明下一版接口需要什么，而不是凭抽象想象设计 schema。

第一周不要求完成 Canonical Skill Interface，也不要求实现完整 SkillStack。

## References

1. Chen, Y. et al. [Task Decomposition-Guided Reranking for Adaptive Agent Skill Retrieval (SkillReranker)](https://arxiv.org/abs/2607.06283). 2026.
2. Xia, T. et al. [GraSP: Graph-Structured Skill Compositions for LLM Agents](https://arxiv.org/abs/2604.17870). 2026.
3. Chen, K. et al. [SkillCAT: Contrastive, Assessment-Augmented and Topology-Aware Skill Self-Evolution for LLM Agents](https://arxiv.org/abs/2606.13317). 2026.
4. Xia, P. et al. [SkillRL: Evolving Agents via Recursive Skill-Augmented Reinforcement Learning](https://arxiv.org/abs/2602.08234). 2026.
5. Moll, J. et al. [GRASP: Gated Regression-Aware Skill Proposer for Self-Improving LLM Agents](https://arxiv.org/abs/2605.29668). 2026.
6. Pu, H., Song, X., and Zhao, L. [SkillOps: Managing LLM Agent Skill Libraries as Self-Maintaining Software Ecosystems](https://arxiv.org/abs/2605.13716). 2026.
7. Lin, H. et al. [MUSE-Autoskill: Self-Evolving Agents via Skill Creation, Memory, Management, and Evaluation](https://arxiv.org/abs/2605.27366). 2026.
8. Li, Y. [Dynamic Agent Skills: A Lifecycle Survey and Taxonomy of Evolving Skill Libraries](https://arxiv.org/abs/2607.10113). 2026.
9. Bai, T. et al. [SkillDAG: Self-Evolving Typed Skill Graphs for LLM Skill Selection at Scale](https://arxiv.org/abs/2606.03056). 2026.
10. Li, D. et al. [Graph of Skills: Dependency-Aware Structural Retrieval for Massive Agent Skills](https://arxiv.org/abs/2604.05333). 2026.
