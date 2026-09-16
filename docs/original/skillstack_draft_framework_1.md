# SkillStack 与 Boundary Load Mapping：面向 Skill 组件边界完整性的实验框架

> **Version 1 / Week 6 revision**
> 本版依据 `reports/week6/week6_report_script_zh.md` 更新。原始框架保存在 `skillstack_draft_framework_0.md`。
> **证据快照：** SkillStack alpha release candidate 已实现并完成零模型发布检查；Boundary Load Mapping（BLM）仍是待实现、待实验验证的研究 proposal。

## Abstract

现有 Skill Agent 研究分别关注技能表示、生成、检索、编排、执行、演化与维护，但通常以端到端系统为评估单位。不同系统采用不同的 skill representation、state abstraction、applicability condition、failure signal 与 update semantics。即使两个组件在形式上通过同一个 schema 交换数据，也不能由此判断接收方是否获得了所有真正影响行为的信息。

**SkillStack** 是一个面向 Skill 组件实验的可安装、可追踪、可复现 harness。它用 Representation、Acquisition/Evolution、Discovery/Selection、Composition/Execution 和 Lifecycle Management（R–A–D–C–L）描述五类稳定职责，并通过显式 Adapter、冻结配置和 append-only trace 支持 controlled component swap。SkillStack 的基础设施贡献与论文方法贡献需要分开：当前 alpha release candidate 证明的是实验路径能够被安装、检查和追踪，而不是所有组件都能 plug-and-play，也不是 SkillStack 优于其他 Agent。

本文进一步提出 **Boundary Load Mapping（BLM，边界负载映射）** 作为待验证的 measurement method。BLM 不只观察组件交换后性能是否变化，而是在接收组件真正读取输入的位置记录 boundary atoms，从同一保存状态出发，逐项恢复原生信息，并使用环境 oracle 判断哪一项恢复会改变任务结果。其目标是识别声明接口没有表达、但对下游行为具有可观察影响的 **load-bearing information**。Phase 0 计划冻结 ALFWorld 中的 Discovery/Selection → Composition/Execution（D→C）边界；Acquisition/Evolution → Lifecycle Management（A→L）作为后续扩展。

BLM 最终只给出范围受限的三类结论：`falsified`、`not falsified` 或 `abstained`。因此，本项目的研究主张不是提出首个模块化 Skill Agent 架构，也不是证明一个普适完整接口，而是建立一种可证伪的实验方法，检验声明的 Skill interface 是否遗漏了行为上承重的依赖。

## 1. Introduction

Large Language Model agents increasingly externalize reusable procedural knowledge as skills. A skill may be natural-language guidance, executable code, a workflow graph, or a structured package containing instructions, tools and validation logic. Recent work has shown that skills can support long-horizon planning, repeated-task reuse, experience transfer and continual agent improvement.

然而，当前研究通常围绕一个完整 pipeline 展开。一个系统同时规定 skill 的表示方式、检索方法、执行器和更新规则，然后报告整个系统相对于 baseline 的结果。这种评估无法直接回答：改进来自哪个组件、一个组件能否离开原系统工作，以及两个单独有效的组件组合后是否仍然有效。

组件交换还可能通过形式检查但在语义上失败。Producer 可能只通过声明接口发送 skill ID、description 和 retrieval score，而原生 Consumer 实际还依赖 prompt 中的动作顺序、内部对象中的前置状态或没有显式记录的 evidence。更换 Consumer 后，程序没有报错，schema validation 也通过，但任务结果发生变化。此时，普通 swap experiment 只能显示差异，不能定位差异由哪一条遗漏信息造成。

Week 6 的 prior-art review 进一步收缩了论文空间。**Harnessing Agent Skills** 已从 37 个系统和 51 篇论文中归纳 architectural patterns，并提出覆盖 Supply Chain、Mediation、Execution Control、Evidence and Feedback 的 reference architecture。它与 SkillStack 原先的“模块化 Skill Agent reference architecture”表述高度重叠。因此，本项目不再把宽泛的 reference architecture 或“首个可组合 Skill Agent 框架”作为主要 novelty。

更新后的论文问题是：

> **当一个 Skill 组件被移入非原生系统时，声明接口是否遗漏了接收方真正消费、并会改变任务结果的信息？如果遗漏，能否通过逐项恢复把该依赖定位出来？**

本项目形成两条相互支持但证据边界不同的主线：

1. **SkillStack：实验基础设施。** 提供组件接入、controlled swap、trace、provenance、fidelity 和可复现运行路径。
2. **BLM：研究方法 proposal。** 通过 receiver-side observation、saved-state replay 和 differentiated atom restoration，检验接口边界的行为完整性。

### 1.1 Revised Contributions

当前版本将预期贡献限定为：

1. **A reproducible Skill component harness（已实现到 alpha release candidate）。** SkillStack 提供可安装 package、命令行入口、显式 Adapter、Retriever–Executor trace path、零模型 demo、发布前检查与 provenance/fidelity 记录。
2. **Boundary Load Mapping（待实现与验证）。** 在 Consumer read point 记录 boundary atoms，并从相同保存状态逐项恢复原生值，以环境 oracle 测量其结果影响。
3. **A bounded interface verdict（待实验产生）。** 对冻结边界输出 `falsified`、`not falsified` 或 `abstained`，而不是声称证明接口普遍完整。
4. **An evidence-derived interface revision（条件性产物）。** 只有经干预显示为 load-bearing 的信息，才成为下一版 shared interface 的候选字段；method-specific 信息继续保留在 native payload 中。

### 1.2 Claim Boundary

本版本不提出以下主张：

- SkillStack 是首个模块化、可组合或具有完整 lifecycle 的 Skill Agent architecture；
- 所有 Skill 组件都可以 plug-and-play；
- SkillStack 的任务性能优于其他 Agent；
- GRASP、SkillRL 或 SkillOps 已被完整复现；
- BLM 已经实现、已经发现普遍 hidden dependency，或已经取得正式实验结果；
- `not falsified` 等价于证明接口完整。

## 2. Related Work and Novelty Boundary

### 2.1 Harnessing Agent Skills

**Harnessing Agent Skills: Architectural Patterns and a Reference Architecture for Skill-Mediated LLM Agents** 是当前最直接的 reference-architecture collision。该工作总结 Skill harness 如何供应、选择、绑定、执行 Skill，并记录 evidence 与 feedback。它说明 Skill 的作用取决于外围 harness，而不是只由 Skill 文件本身决定。

这与 SkillStack 共享研究对象和核心观察，但二者拟回答的问题不同：

| 维度 | Harnessing Agent Skills | SkillStack / BLM |
|---|---|---|
| 主要对象 | Skill-mediated Agent 的 architectural patterns 与 reference architecture | 来自不同实现的 Skill 组件边界 |
| 主要问题 | 一个完整 Skill harness 包含哪些职责 | 组件交换后，声明接口是否遗漏行为依赖 |
| 主要方法 | 跨系统综合与架构归纳 | controlled swap、receiver-side tracing、saved-state intervention |
| 主要产物 | patterns 与 reference architecture | 范围受限的 Boundary Load Map 与 interface verdict |

当前比较主要基于可获得的摘要和元数据，SSRN 全文尚未纳入本项目的直接核查。因此，只能说现有摘要没有报告 SkillStack 式跨论文组件交换或 BLM 式逐项恢复干预；不能据此断言全文一定没有相关内容。

### 2.2 Discovery, Selection and Composition

Skill retrieval 从 embedding Top-k 发展到 task decomposition、state-aware reranking 和 dependency-aware structural retrieval。SkillReranker、Graph of Skills 与 SkillDAG 表明，选择结果不仅依赖文本相关性，还可能依赖当前状态、子任务与结构关系。

Composition/Execution 负责把 selected skills 转换为实际动作。GraSP 使用带 precondition/effect 的 typed DAG、node-level verification 与 local repair。此类方法通常要求上游提供比 skill ID 或 description 更丰富的语义。BLM 不预设这些字段一定属于通用 schema，而是把 Consumer 实际读取的内容作为待测对象。

### 2.3 Acquisition, Evolution and Lifecycle Management

SkillRL、SkillCAT 与 GRASP 研究如何从交互经验中生成或修改 skills；SkillOps 与 MUSE-Autoskill 研究 skill library 的长期评估、准入、维护和演化。这些系统对 evidence source、patch format、validation rule 和 target environment 的要求并不相同。

因此，Acquisition/Evolution 与 Lifecycle Management 不能被默认视为无条件可交换。A→L 可作为 BLM 的第二条边界：一个新的 proposer 把 candidate 交给既有 governance mechanism 时，后者是否缺少做出可靠 admission decision 所需的原生证据。

### 2.4 Taxonomy, Architecture and Executable Measurement

Dynamic Agent Skills 等 survey 为 skill lifecycle 提供共同词汇，Harnessing Agent Skills 进一步提供 reference architecture。它们回答“领域中有哪些职责与模式”。SkillStack 保留 R–A–D–C–L 作为实验坐标系，但不再把该分类本身当作核心 novelty。

更新后的区分是：

> **Prior work organizes declared responsibilities; SkillStack executes controlled crossings; BLM tests whether the declared boundary captures the information that actually carries behavior.**

## 3. Problem Formulation

### 3.1 R–A–D–C–L as Responsibility Coordinates

SkillStack 将 Skill Agent 中与 skill 直接相关的职责表示为：

\[
\mathcal{A}=(R,A,D,C,L)
\]

其中：

- \(R\)：**Representation**，定义 skill 的内容、形式和可观察属性；
- \(A\)：**Acquisition/Evolution**，生成、修改、合并或拆分 skill；
- \(D\)：**Discovery/Selection**，根据 task 与 state 选择候选 skill；
- \(C\)：**Composition/Execution**，组织、执行并验证 selected skills；
- \(L\)：**Lifecycle Management**，评估、准入、版本化、回滚与退役 skill。

R–A–D–C–L 不是强制执行顺序，也不要求每项职责对应一个代码模块。它的作用是标记 producer–consumer handoff，并帮助冻结实验中被替换与被保持不变的部分。

### 3.2 Declared Boundary and Native Dependency

对一个 producer \(P\) 与 consumer \(C\)，定义：

- \(I_{declared}\)：文档、schema 或 Adapter 明确声明会传递的信息；
- \(I_{native}\)：原生组合中可能到达 Consumer 的完整可观察信息；
- \(a\)：一个 boundary atom，即 Consumer 在具体 read point 读取、默认、丢弃或回退的一项最小可干预信息；
- \(Y\)：环境 oracle 给出的任务结果。

若 \(a \in I_{native}\) 但 \(a \notin I_{declared}\)，并且从同一保存状态恢复 \(a\) 会改变 \(Y\)，则该 atom 在冻结实验范围内是 undeclared load-bearing information 的候选证据。

这里的“load-bearing”是操作性定义，不表示该字段在所有任务、模型和 Consumer 中都重要。BLM 只对冻结的组件、任务、状态、prompt、budget、seed 和 intervention domain 做结论。

### 3.3 Research Questions

**RQ1 — Swap gap。** 在冻结邻接组件与运行条件后，native pairing 与 crossed pairing 是否出现稳定、可重放的任务结果差异？

**RQ2 — Boundary load。** 哪些由 Consumer 实际读取的 atoms 会在逐项恢复时改变环境 oracle 结果？其中哪些没有出现在声明接口中？

**RQ3 — Bounded completeness。** 在预注册的任务、组件与干预覆盖下，当前声明接口应被判为 `falsified`、`not falsified` 还是 `abstained`？

**RQ4 — Boundary transfer。** D→C 上形成的测量协议能否迁移到 A→L，而不把 task execution evidence 与 lifecycle admission evidence 混为一谈？

## 4. SkillStack as Experimental Infrastructure

### 4.1 Infrastructure Role

SkillStack 固定实验外围条件，并允许研究者替换一个被测组件而不重写其他部分。核心能力包括：

- explicit Retriever、Adapter、Executor 与 trace path；
- frozen task manifest、component version、prompt、budget 与 seed；
- append-only JSONL evidence；
- component provenance 与 fidelity label；
- regression checks 和 deterministic zero-model path；
- native payload preservation 与 adapter-friction logging。

SkillStack 的角色是让组件交换和因果干预可以被复现与审计。它不是 BLM 结论本身。

### 4.2 Week 6 Release-Candidate Snapshot

截至 Week 6 报告所记录的 release-candidate 快照，仓库已经提供：

- 可安装的 Python package；
- `skillstack` 命令行入口；
- 不调用模型的 deterministic demo；
- Retriever、Adapter、Executor 和 trace 的完整零模型执行路径；
- repository preflight、安全扫描和发布前检查；
- GRASP、SkillRL 与 SkillOps 的 provenance/fidelity 记录；
- Python 3.9 与 3.10 CI 配置。

独立 fresh-clone 验证中，公开文件扫描为零问题，108 项单元测试、package build 和 zero-model demo 通过。当前仓库仍未创建 `v0.1.0-alpha` tag，因此准确状态是 **alpha release candidate**，不是正式 tagged release。

### 4.3 Native-First Boundary Handling

BLM 延续 implementation-first, schema-later 原则：

1. 保留 producer 与 consumer 的 native artifact；
2. 用最小、显式 Adapter 连接组件；
3. 记录 Adapter 与 Consumer read point 上实际读取、生成、默认、丢弃或猜测的信息；
4. 不因现有 schema 没有某字段就提前删除 native value；
5. 只有干预证据显示某类信息影响结果时，才把它列为 interface revision candidate。

这使 Canonical Interface 从实验结果中产生，而不是成为过滤实验现象的前提。

## 5. Boundary Load Mapping

### 5.1 Core Idea

普通 component swap 估计“换组件后是否变化”。BLM 增加第二层测量：从交换后的同一失败或差异状态开始，一次只恢复一项原生信息，观察结果是否随之改变。

```text
Native pairing ───────────────→ reference outcome
      │
      └─ component swap ──────→ crossed outcome
                                  │
                                  ├─ restore atom a1 ─→ outcome a1
                                  ├─ restore atom a2 ─→ outcome a2
                                  ├─ negative control ─→ control outcome
                                  └─ full native payload ─→ upper-bound outcome
```

如果恢复 `required_appliance = microwave` 能使 ALFWorld 的加热任务从失败恢复为成功，而恢复 author label 或无关 tag 不改变结果，那么前者在该冻结状态下具有 load-bearing evidence，后者不具有。

### 5.2 Boundary Atom Census

Phase 0 在 Consumer 真正读取输入的位置记录 boundary atom。每条记录至少包含：

- channel 或来源；
- key / semantic role；
- Consumer 读取到的 native value；
- read locus；
- event class，例如 read、default、drop、reject 或 fallback；
- declared / undeclared 状态；
- 对应 task、component、state 与 trace identifier。

该 census 只覆盖显式可观察 read points。Prompt 内部或模型隐状态中无法可靠定位的依赖必须标为 censored，不能被当作已覆盖。

### 5.3 Saved-State Restoration

对可重放的 crossed state，BLM 比较：

\[
\Delta_a = Y(\text{restore } a) - Y(\text{unrestored})
\]

其中两条 arm 从同一 pre-consumption saved state 开始，保持 Retriever、Executor、task、prompt、budget、seed 与其他输入不变。\(\Delta_a\) 是冻结范围内的 paired outcome difference，不自动具有跨任务或跨系统的普适含义。

如果 saved-state replay 不能保持必要环境状态，或 restoration 绕过了 Consumer 的正常解析与准入路径，则该 atom 不能产生有效因果判断。

### 5.4 Controls

Phase 0 至少需要两类 controls：

1. **Negative control。** 恢复与当前执行无关的信息；如果它也系统改变结果，说明 restoration carrier 或 replay 过程本身引入了干扰。
2. **Positive control / full-payload restoration。** 恢复完整 native payload；如果完整恢复仍无法回到 native reference 附近，则逐项 atom probe 不足以解释 swap gap，结果应降级为 `abstained` 或未覆盖，而不是强行归因。

逐项干预还可能漏掉只有联合恢复才起作用的 dependencies。Phase 0 应保存该风险，并在单 atom 结果与 full-payload control 不一致时测试有限的 joint restoration，或明确 abstain。

### 5.5 Verdicts

每个冻结边界输出以下三类 verdict 之一：

- **`falsified`：** 至少一个声明接口之外的 atom 或 atom group 通过有效 replay 与 controls 显示会改变任务结果。
- **`not falsified`：** 在预先限定且覆盖充分的任务、read points 与 intervention domain 中，没有发现 undeclared load-bearing information。
- **`abstained`：** saved-state 无法可靠恢复、Consumer reads 覆盖不足、缺少可接受替代值、controls 失败，或 full-payload restoration 无法解释差异。

`not falsified` 不是“接口已被证明完整”。它只表示当前有限实验没有推翻声明接口。

## 6. Phase 0 Experimental Design

### 6.1 Primary Boundary: D→C

Phase 0 优先冻结 **Discovery/Selection → Composition/Execution（D→C）**。D 是“选择 Skill 的组件”，C 是“组织并执行 Skill 的组件”。该边界优先于 A→L，原因是 ALFWorld 提供直接的状态变化、任务成功判定和执行 trace，更适合先验证 saved-state intervention 是否可行。

示例任务为“加热苹果并放到桌子上”。D 选择 `heat_then_place`，C 将其转换为找到苹果、拿取、使用 microwave、加热和放置等动作。BLM 测量 D 正式交给 C 的信息是否足以让非原生 C 完成同一任务。

### 6.2 Frozen Manifest

正式实验前冻结并记录：

- Retriever 与 Executor 的具体实现和版本；
- native pairing 与 crossed pairing；
- ALFWorld task IDs 与 environment version；
- model/backend、prompt、decoding settings、budget 与 retry policy；
- seeds 与停止条件；
- 当前声明的 D→C interface；
- native payload 的保存范围；
- environment oracle；
- saved-state capture 与 replay procedure；
- boundary atom granularity 与 Consumer read-point coverage。

没有冻结 manifest 的结果只能作为 feasibility observation，不能进入正式 BLM verdict。

### 6.3 Execution Procedure

1. 运行 native pairing，保存 reference outcome 与 pre-consumption state。
2. 在相同任务条件下运行 crossed pairing，确认 swap gap 是否存在且可重放。
3. 在 crossed Consumer read points 建立 boundary atom census。
4. 从同一 saved state 分别运行 un-restored arm 与 per-atom restoration arm。
5. 运行 negative control 与 full native-payload control。
6. 检查 replay determinism、control validity 与 coverage。
7. 生成按 declaredness 分层的 Boundary Load Map。
8. 根据预先定义的 gate 输出 `falsified`、`not falsified` 或 `abstained`。

### 6.4 Measurements

**Task outcome**

- ALFWorld goal success；
- normalized reward（若与冻结 oracle 一致）；
- environment steps 与 termination reason。

**Boundary evidence**

- observed Consumer read points；
- declared / undeclared atom count；
- per-atom paired outcome difference；
- control outcomes；
- unexplained residual between atom restoration and full-payload restoration；
- censored、unreadable 与 non-intervenable atoms。

**Execution integrity**

- state replay success；
- repeated replay consistency；
- parser/admission path preservation；
- model calls、tokens、latency 与 estimated cost；
- trace completeness 与 configuration hash。

### 6.5 Secondary Boundary: A→L

A→L 从 **Acquisition/Evolution** 向 **Lifecycle Management** 交接 candidate skill 与证据。扩展实验可交换 GRASP/SkillRL-style proposer，同时固定 governance/admission mechanism，检查后者是否依赖未声明的 native evidence、failure label 或 patch semantics。

A→L 不能直接复制 D→C 的 outcome 定义。D→C 使用环境 task oracle；A→L 至少要区分 native admission、regression evidence、maintenance correctness 和下游 task effect。只有 D→C 的 instrumentation、replay 与 verdict gate 可行后，才进入该扩展。

## 7. Current Evidence and Remaining Work

### 7.1 What Is Implemented

| 项目 | 当前状态 | 可支持的陈述 |
|---|---|---|
| Installable package and CLI | 已实现 | SkillStack 可作为 Python package 安装并提供命令行入口 |
| Deterministic zero-model demo | 已实现并通过 release check | Retriever–Adapter–Executor–trace 路径可在无模型调用下复现 |
| Repository preflight / public scan | 已实现；Week 6 快照零问题 | release-candidate 文件通过当时的公开扫描 |
| Unit tests and build | 108 tests、package build 通过 | alpha release-candidate 工程检查通过 |
| Provenance and fidelity records | 已实现 | 外部方法接入状态可按来源与忠实度区分 |
| Formal alpha tag | 未创建 | 只能称 alpha release candidate |
| BLM instrumentation and experiments | 未完成 | 只能描述 proposal、feasibility requirements 与 falsification plan |

### 7.2 Phase 0 Feasibility Gates

进入正式 BLM 实验前，至少需要通过：

1. **Saved-state replay gate：** 从同一状态重放时，未施加干预的结果可重复。
2. **Consumer-read census gate：** 明确哪些显式 read points 被观测，哪些被 censored。
3. **Restoration-path gate：** atom 恢复通过正常 parser/Consumer path，而不是绕过被测边界。
4. **Oracle gate：** ALFWorld goal predicate 与被测组件独立，且可稳定评分。
5. **Control gate：** negative control 不应系统改变结果；full-payload control 能检验恢复机制的上限。
6. **Claim gate：** verdict 只覆盖冻结 manifest，不外推为普遍接口完整性。

任一关键 gate 失败时，Phase 0 结果应记录为 feasibility failure 或 `abstained`，而不是 BLM positive result。

### 7.3 Immediate Next Steps

1. 正式确认 D→C 为主边界，并把 A→L 保留为扩展。
2. 冻结 Retriever、Executor、ALFWorld tasks、seeds 与 declared interface。
3. 定义 boundary atom granularity 和 Consumer read-point instrumentation。
4. 完成 saved-state replay feasibility spike。
5. 实现 side-car restoration，不修改 producer 与邻接组件。
6. 预先写明 positive/negative controls、停止条件、失败判定与 abstention rule。
7. 先运行小规模、可人工审计的 ugly-but-real pilot，再决定是否扩大任务与 seed 覆盖。

## 8. Risks and Mitigations

### 8.1 Reference-Architecture Novelty Collision

Harnessing Agent Skills、Dynamic Agent Skills、SkillOps 和其他 modular-agent work 已覆盖 reference architecture、taxonomy、lifecycle 或 modular recombination 的重要部分。

**Mitigation：** 删除“first architecture”“first composable skill system”等宽泛表述；将论文核心限定为 receiver-side observation、saved-state atom restoration 与 bounded interface falsification。Harnessing Agent Skills 的全文仍需在投稿前直接核查。

### 8.2 Replay Is Not Faithful

环境状态、模型上下文或随机性可能无法完整恢复，使 restoration arm 与 control arm 不再可比较。

**Mitigation：** 在正式实验前单独验证 replay determinism；保存 capture coverage；无法恢复的状态直接触发 `abstained`。

### 8.3 Atom Definition Is Arbitrary

atom 太粗会混合多个机制，太细会造成大量无意义 probes；逐项零效应也可能掩盖 joint dependency。

**Mitigation：** 在运行前冻结 atom rule；以 Consumer read point 与可独立恢复性为边界；用 full-payload control 暴露未解释差异，并仅对有依据的 groups 做 joint restoration。

### 8.4 Instrumentation Changes Behavior

Tracing 或 side-car injection 本身可能改变 prompt、latency、ordering 或 Consumer behavior。

**Mitigation：** 运行 instrumented no-op 与 unrelated-atom negative controls；保持正常 parser/admission path；记录所有额外操作。

### 8.5 Porting Distorts Native Methods

不同论文使用不同环境、模型和 skill format，简化接入可能不再忠实于原方法。

**Mitigation：** 区分 source-native、source-variant、reconstructed 与 blocked fidelity；不把 provider-substituted 或 method-inspired cell 表述为论文复现。

### 8.6 Scope Does Not Generalize

ALFWorld 的 D→C 结论可能不适用于其他环境、模型或 A→L boundary。

**Mitigation：** 先报告 per-boundary、per-manifest verdict；只有 Phase 0 gate 通过后才扩展第二边界与第二环境。

## 9. Success Criteria

Phase 0 的成功不要求发现 hidden dependency。一个可接受结果必须满足：

- native 与 crossed cells 使用冻结、可审计的 manifest；
- saved-state replay 与 controls 通过预定义 gate；
- Consumer read-point coverage 和 censored scope 被明确记录；
- Boundary Load Map 可从 raw traces 重建；
- `falsified`、`not falsified` 或 `abstained` verdict 可由规则复算；
- 结论不越过所执行的任务、组件、seeds 与 intervention domain；
- 即使没有发现 undeclared load-bearing atom，也将其作为有效 negative finding 报告。

SkillStack 的成功标准同样不是证明所有组件都可交换，而是让研究者能够受控、可复现地说明：哪些组件在什么边界上可以组合，哪些不能，观察到的差异有多少能够被具体边界信息解释。

## 10. References

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
11. [Harnessing Agent Skills: Architectural Patterns and a Reference Architecture for Skill-Mediated LLM Agents](https://doi.org/10.2139/ssrn.6871959). SSRN, 2026. **Current project review is abstract/metadata-only; full-text verification remains pending.**
