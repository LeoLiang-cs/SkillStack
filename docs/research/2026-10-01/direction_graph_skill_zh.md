# 方向梳理：Graph Skill Agent 模块化

日期：2026-10-01 ｜ 使用 skill：research-ideation（claude-scholar）、paper-search
依据：EvoSkillGraph.pdf（2 页提案）、本次检索的 2025–2026 论文摘要（只读了摘要，标为 abstract-only 证据）

## 1. 现有工作其实各自只"图化"了 agent 的一块

| 模块 | 扁平（non-graph）代表 | 图化代表 | 它们的对比方式 |
|---|---|---|---|
| 表示/存储 | SkillRL 的 SkillBank（层级列表） | SkillNet（本体 + 关系，60 万技能）、EvoSkillGraph 的多重图 schema | 整机 vs 整机 |
| 检索 | SkillRL 语义检索 | Graph-of-Skills（arXiv 2604.05333，依赖感知 + 反向 PPR） | 只在检索层内部做消融 |
| 组合/规划/执行 | ReAct、flat skill | GraSP（arXiv 2604.17870，DAG 编译 + 节点验证 + 局部修复） | 整机 vs 整机，+19 分里混着图、验证、修复三样 |
| 进化/更新 | SkillRL 递归进化、Library Drift（arXiv 2605.19576）的治理 | EvoSkillGraph 的 Corrects 边 / 分化 | 基本没有图 vs 扁平的对照 |

还有一篇综述 *Self-Evolving Agents as Dynamic Graph Transformation*（arXiv 2608.18104）把这些统一成"动态图变换"，并点名 **cross-component co-evolution（跨组件协同进化）** 研究不足。它是概念框架，没有受控实验。

**空白**：没有人在同一个流水线里，逐模块地把"扁平"换成"图"，回答"图结构到底在哪一块起作用、几块之间会不会互相依赖"。

## 2. 对 EvoSkillGraph 原方案的判断

作为"新方法"，它的每一块都已经有人做了：schema 对应 SkillNet/GraSP，反向链式规划对应 GraSP，依赖检索对应 Graph-of-Skills，失败分化修复对应 GraSP 的局部修复加 SkillRL 的进化。直接做会被审稿人说成"拼装"。你观察到"大家各做一块"是对的，这正是转向的理由。

## 3. 两个选项的看法

### 选项 A：Benchmark（我推荐，但要做"强版本"）

- **弱版本**：把几个 graph agent 和几个 non-graph agent 放一起跑分。这只是排行榜，主会不收，因为差异来源说不清。
- **强版本**：做一个**模块化、受控的对照平台**。统一流水线分 4 个槽位：存储、检索、组合、进化。每个槽位有 flat 和 graph 两种实现，都取自已发表系统。然后做（部分）析因实验。
  - 例子：`flat 存储 + GoS 检索 + GraSP 组合 + SkillRL 进化` 对比全 flat。算出每个槽位"图化"的主效应和交互效应，比如"图检索只有在组合层也是图的时候才有用"。
- **BLM 在这里的位置**：把模块塞进统一接口，恰好就是 BLM 批评的 schema-first。所以每次跨系统替换掉分时，用 BLM 解释原因，例如 GraSP 执行器读了 flat 检索器不提供的 precondition 字段。BLM 从"主方法"变成"诊断工具"，前面说的"所以呢"和"范围窄"两个问题同时解决。
- **和项目目标对齐**：这个平台本身就是"开源 graph skill agent"，SkillStack 现有的 registry、adapter、tracing、replay 都能直接复用。

### 选项 B：新方法

现在提新方法风险高，因为每一块都有人占了。更好的顺序是**先由 A 得到发现，再针对发现提一个轻量方法**。
- 例子：如果实验发现"图进化（加 Corrects 边）会悄悄破坏组合层依赖的前置条件字段"，就提出"契约感知的图进化"：进化时用 BLM 的 load map 约束哪些字段不能改。这也正好打在综述点名的"跨组件协同进化"空白上。

## 4. 推荐的论文形态

**"图结构在 skill agent 的哪一块起作用？受控模块化研究 + 开源平台 + 一个由发现驱动的轻量方法"**

### Research Question Card

- Question：在 skill agent 的存储、检索、组合、进化四个模块中，图结构各自贡献多少收益？模块之间是否存在必须同时图化才生效的依赖？
- Type：confirmatory + exploratory
- Hypothesis：图结构的收益集中在 1–2 个模块（例如检索和组合），且存在显著交互；跨系统移植的大部分损失来自未声明的边界字段。
- Why it matters：现有论文都是整机对比，归因不清；社区不知道该投入在哪一块。
- Current evidence：GoS、GraSP、SkillNet 的整机增益（abstract-only）；Library Drift 显示进化可能有害；R1 校准已完成。
- Missing evidence：任何受控的逐模块对照；跨系统移植的实测损失。
- What would support it：主效应和交互效应的置信区间不跨 0，且在 ≥2 个环境、≥2 个 backbone 上一致。
- What would falsify it：图化收益在受控后消失（全部来自验证/修复等非图机制），这本身也是可发表的阴性发现。
- Minimal next action：选定 4 个槽位各 1 个 flat 和 1 个 graph 实现，确认代码可得性和保真度（faithful/adapted）。
- Decision：read more → run experiment

## 5. 风险

1. **工程量**：要复现 4–5 个系统的模块。先做 3 槽位 × 2 变体（8 个配置），进化槽位放第二阶段。
2. **撞车**：SkillNet-Gym 已经在测检索、使用、组合；综述作者也可能接着做 benchmark。定方向前要对"受控模块化对照"这个 claim 跑一次 scoop-check。
3. **成本**：8–16 个配置 × 2 个环境 × 2 个 backbone × 多个 seed，需要先估 API 预算。
