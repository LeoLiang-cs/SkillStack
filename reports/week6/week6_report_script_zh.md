# SkillStack Week 6 汇报稿

> 建议汇报时长：8–10 分钟
> 汇报主线：Scoop Check → 研究方向收窄 → SkillStack 开源进展 → BLM Phase 0

## 第一部分：本周工作的整体变化

老师好，我这周的工作主要可以分成三部分。

第一部分是做了更系统的 scoop check，也就是检查我们的研究想法有没有被已有工作覆盖。这里我重点对比了最近的 **Harnessing Agent Skills**。

第二部分是通过 Idea-Spark 进一步收窄论文问题。我们不再把论文贡献笼统地表述为“提出一个模块化 Skill Agent 框架”，而是聚焦到一个更具体、也更容易证伪的问题：**当我们把一个 Skill 组件从原来的系统换到另一个系统时，接口里是不是遗漏了某些真正影响执行结果的信息？**

围绕这个问题，目前形成的研究 idea 叫做 **Boundary Load Mapping，简称 BLM，中文可以叫边界负载映射**。

第三部分是继续完善 SkillStack 开源仓库。现在我们的整体路线变成了两条相互支持、但需要区分的主线：

第一条是把 SkillStack 做成一个开源、可复现、可替换组件的实验框架；第二条是使用 SkillStack 实现和验证 BLM，争取形成面向 12 月会议的论文。

---

## 第二部分：Scoop Check 与 Harnessing Agent Skills

这周重点比较的工作是：

**Harnessing Agent Skills: Architectural Patterns and a Reference Architecture for Skill-Mediated LLM Agents。**

这篇工作调研了 37 个系统和 51 篇论文，总结了 10 种 architectural patterns，并提出了四层参考架构，包括：

- Supply Chain
- Mediation
- Execution Control
- Evidence and Feedback

它的核心观点是：一个 Skill 的实际作用，不只由 Skill 文件本身决定，还取决于外围 harness 如何选择它、绑定上下文、解释它、执行它，以及记录什么证据。

这个观点与 SkillStack 确实有较高重叠。具体来说，二者有三个明显的相同点。

第一，研究对象相同。两者都研究 Skill-mediated LLM Agents，而不是单纯研究 prompt 或某一个 Agent 的性能。

第二，核心观察相同。两者都认为 Skill 本身不是一个完全独立的单元，它的效果依赖周围系统怎样处理它。

第三，两者都关心 Skill 生命周期中的不同职责，以及这些职责之间的接口。

但是，两者的研究方法和要回答的问题不一样。

Harnessing Agent Skills 主要是一个综述和参考架构工作。它回答的是：

> 一个完整的 Skill harness 应该包含哪些职责？现有系统可以怎样分类？

SkillStack 更偏向可执行的实验框架。它回答的是：

> 来自不同论文的 Skill 组件，在保留各自原生表示的情况下，能不能实际组合和替换？替换以后是格式不兼容、语义不兼容，还是任务性能发生了变化？

BLM 又比 SkillStack 的一般组件替换多走了一步。它回答的是：

> 如果替换以后失败，到底是哪一条没有写进接口的信息造成了失败？

所以我目前认为，Harnessing Agent Skills 对我们原来比较宽泛的“Skill 参考架构”贡献构成了比较强的覆盖。我们不应该再声称自己是第一个模块化 Skill Agent 架构。

但是，我们仍然可以把论文贡献收窄到：**通过实际组件交换和逐项干预，测量声明接口中遗漏的行为依赖。**

这里还有一个证据限制：目前对 Harnessing Agent Skills 的分析主要基于可获得的摘要和元数据，SSRN 全文暂时无法获取。因此现在的结论是 abstract-only confidence。比较安全的说法是：当前摘要没有报告 SkillStack 式的跨论文组件替换实验，也没有报告 BLM 式的逐项恢复干预。

---

## 第三部分：SkillStack 中的 R–A–D–C–L

为了说明我们具体在交换什么组件，我先简单解释 SkillStack 的 R–A–D–C–L。

它们代表 Skill 生命周期中的五类职责。

**R 是 Representation。**

它负责 Skill 怎么表示和存储。例如，一个 Skill 是自然语言步骤、结构化 JSON，还是一个带有前置条件和效果的图。

**A 是 Acquisition and Evolution。**

它负责 Skill 怎么产生和变化。例如从成功轨迹中生成新 Skill，或者修改、合并已有 Skill。

**D 是 Discovery and Selection。**

它负责面对一个任务时，从 Skill library 里选择哪个 Skill。

**C 是 Composition and Execution。**

它负责怎样组织并执行选中的 Skill，把 Skill 变成 Agent 的实际动作。

**L 是 Lifecycle Management。**

它负责审核、接纳、版本化、回滚和淘汰 Skill。

这五个字母不是说 Agent 一定要严格按照 R、A、D、C、L 的顺序运行，而是为了区分系统里的不同职责。我们真正研究的是这些职责之间的交接边界。

### D→C 是什么

D→C 是从 **Discovery/Selection 到 Composition/Execution**。

用大白话说，D 是“负责找技能的人”，C 是“负责使用技能的人”。

例如，Agent 接到一个任务：“把苹果加热，然后放到桌子上。”

D 从 Skill library 中选择了一个叫 `heat_then_place` 的 Skill，然后把这个 Skill 交给 C。C 再根据 Skill 生成具体动作，例如找到苹果、打开微波炉、放入苹果、加热、取出并放到桌子上。

这里的研究问题是：

> D 交给 C 的信息够不够？如果把 C 换成另一个执行器，这个 Skill 还能不能正确执行？

### A→L 是什么

A→L 是从 **Acquisition/Evolution 到 Lifecycle Management**。

用大白话说，A 是“写技能或者改技能的人”，L 是“技能仓库的审核员”。

例如，GRASP 或 SkillRL 生成了一个新的 Skill proposal。L 层需要检查这个候选 Skill 有没有足够证据、是否与已有 Skill 重复、会不会导致回归，然后决定接受、拒绝、合并或者建立新版本。

这里的研究问题是：

> A 提交给 L 的信息够不够？换一个 Skill 生成器以后，原来的审核机制还能不能做出可靠决定？

BLM 理论上可以研究这两个边界。最初的 Idea-Spark 卡片更接近 A→L 场景，但从第一阶段实验的可执行性考虑，我建议先选择 **D→C 作为主边界**，因为它有比较直接的任务成功率、环境 oracle 和执行状态。A→L 可以作为第二个边界，用来证明 BLM 不只适用于 Retriever 和 Executor。

---

## 第四部分：BLM 到底是什么

BLM 的方法全称是：

**Boundary Load Mapping。**

它产生的结果叫做：

**Boundary Load Map，也就是边界负载图。**

这里的“负载”可以理解成建筑里的“承重”。

一个接口中有很多信息。有些信息只是普通信息，删掉以后系统没有变化；但有些信息是真正的承重信息，虽然没有被正式写进接口，但删掉以后任务就会失败。

所以 BLM 最简单的解释是：

> 两个组件交接失败以后，把可能遗漏的信息一条一条补回去，看补回哪一条以后任务恢复成功。那条信息就是这个边界上的承重信息。

还是用刚才加热苹果的任务举例。

D 选择了 `heat_then_place` Skill，并通过正式接口告诉 C：

- Skill ID 是 `heat_then_place`
- 目标是加热苹果并放到桌子上
- 这个 Skill 的检索分数是 0.9

从格式上看，这些字段都是合法的，因此 schema validation 可以通过。

但是，原来的执行器可能还隐含地依赖三个信息：

- 应该使用的设备是 microwave；
- 执行前必须先拿到苹果；
- 动作顺序必须是打开微波炉、放入苹果、加热、再取出。

这些信息可能藏在原生系统的 prompt、上下文或者内部对象里，没有被写进正式的 D→C 接口。

当我们把这个 Skill 交给另一个 Executor 时，程序不会报错，接口检查也可以通过，但 Agent 最终无法完成任务。

普通的组件交换实验只能告诉我们：

> 换了 Executor 以后，成功率下降了。

但是它不能告诉我们为什么下降。

BLM 的做法是从同一个保存状态开始重新执行，然后一次只补回一条信息。

例如：

- 补回 Skill 作者名称，任务仍然失败；
- 补回一个无关标签，任务仍然失败；
- 补回 `required_appliance = microwave`，任务恢复成功；
- 补回完整的原生 payload，任务也恢复成功。

那么我们就获得了一条比较具体的结论：

> 对当前任务和 Executor 来说，`required_appliance` 是一条有因果证据支持的承重信息，但它没有出现在当前声明接口中。

这就是 BLM 相对于一般兼容性测试增加的价值。它不是只判断“能不能换”，而是定位“为什么不能换”。

---

## 第五部分：BLM 实验准备怎么做

Phase 0 准备先冻结 D→C 边界。

具体来说，我计划固定：

- Retriever 和 Executor 的具体版本；
- ALFWorld 任务清单；
- 模型、prompt、budget 和随机种子；
- 当前正式声明的 D→C 接口；
- 任务成功的环境 oracle；
- 可以保存和恢复的执行状态。

正式实验大致分为五步。

第一步，运行原生组合和交换组合，确认交换后是否存在稳定的结果差异。

第二步，在 Executor 真正读取输入的位置记录它消费了哪些信息。这里每一条最小信息称为一个 boundary atom，也就是边界原子。

第三步，从同一个保存状态重新运行，并一次只恢复一个原生 atom。

第四步，观察恢复这个 atom 后，ALFWorld 的任务结果是否发生变化。

第五步，加入对照实验。恢复无关信息作为 negative control；恢复完整原生 payload 作为 positive control，检查恢复机制本身是否可靠。

最后，对一个接口可能得到三种结论：

第一种是 **falsified**。也就是发现了没有写进接口、但确实影响结果的承重信息。

第二种是 **not falsified**。在当前有限的任务和干预范围内，没有发现遗漏的承重信息。

第三种是 **abstained**。由于状态无法恢复、缺少可替代值或者覆盖不足，我们没有足够证据做判断。

这里使用 not falsified，而不是直接说接口被证明完整，是为了避免过度声明。我们的结论只对冻结的任务、组件和干预范围成立。

---

## 第六部分：SkillStack 开源仓库进展

除了论文 idea，这周也基本完成了 SkillStack 开源 alpha 的准备。

当前代码已经推送到 GitHub 的 main 分支，采用 MIT License。现在仓库提供：

- 可安装的 Python package；
- `skillstack` 命令行入口；
- 不需要调用模型的 deterministic demo；
- Retriever、Adapter、Executor 和 trace 的完整执行路径；
- 仓库安全扫描和发布前检查；
- GRASP、SkillRL 和 SkillOps 组件的 provenance 与 fidelity 记录；
- Python 3.9 和 3.10 的 CI 配置。

独立 fresh-clone 验证中，公开文件扫描为零问题，108 项单元测试通过，package build 和 zero-model demo 也通过。

不过目前还没有创建正式的 `v0.1.0-alpha` tag，所以更准确的说法是：**alpha release candidate 已经完成并推送，但正式 tag 尚未创建。**

这里需要特别区分开源成果和论文成果。

当前开源版本证明的是：SkillStack 已经是一个可安装、可追踪、可以进行组件实验的 harness。

它还不能证明：

- 所有 Skill 组件都可以 plug-and-play；
- SkillStack 的任务性能优于其他 Agent；
- GRASP、SkillRL 和 SkillOps 已经被完整复现；
- BLM 已经实现或者取得了正式实验结果。

---

## 第七部分：当前阶段性结论和局限

目前最重要的阶段性结论有三个。

第一，SkillStack 作为开源实验框架的方向仍然成立，但论文不能再使用宽泛的“首个模块化 Skill Agent 架构”作为主要 novelty。

第二，论文问题已经收窄为 BLM。我们不只是测试组件能不能交换，而是尝试测量声明接口遗漏了哪些真正影响结果的信息。

第三，SkillStack 和 BLM 应该被明确区分。SkillStack 是实验基础设施，BLM 是建立在这个基础设施上的研究方法。

当前最大的局限是：BLM 仍然是一个研究 proposal，还没有完成正式实现和实验。因此现在只能说方法设计具有可行性，不能说已经证明存在某种普遍的隐藏接口问题。

---

## 第八部分：下一步计划和希望讨论的问题

下一步我准备先完成 BLM Phase 0 的范围冻结，暂时不直接扩大实验规模。

具体包括：

第一，确定是否正式采用 D→C 作为主边界，并把 A→L 保留为扩展实验。

第二，冻结 Retriever、Executor、任务、随机种子和声明接口。

第三，明确哪些信息算一个 boundary atom，以及应该在哪个 consumer read point 记录。

第四，验证 ALFWorld 是否能够支持可靠的 saved-state replay。

第五，提前写清 positive control、negative control、停止条件和失败判定，避免实验跑完以后再修改定义。

我希望和老师重点讨论三个问题：

第一，论文是否应该明确以 BLM 这个 measurement method 作为核心贡献，而把 SkillStack 定位为实验基础设施？

第二，Phase 0 先研究 D→C、之后再扩展到 A→L，这个范围是否合适？

第三，我们目前的 novelty claim 是否应该限定为：**通过 receiver-side observation 和 differentiated atom restoration，实证检验声明的 Skill interface 是否遗漏了承重依赖？**

最后总结一下：这周最大的变化不是增加了更多模块，而是把论文问题收窄了。SkillStack 解决的是如何可复现地交换和比较 Skill 组件；BLM 解决的是交换失败以后，如何定位真正影响结果的隐藏接口依赖。下一步的关键不是马上跑大规模实验，而是先把 D→C 的测量边界和可证伪条件冻结下来。

---

## 一分钟压缩版

这周主要完成了三件事。第一，scoop check 发现 Harnessing Agent Skills 已经系统总结了 Skill harness 的架构职责，所以我们不能再把“模块化 Skill Agent 架构”作为主要 novelty；但它目前没有报告跨论文组件交换和逐项恢复干预。第二，我们把论文方向收窄成 Boundary Load Mapping，也就是当组件交换失败时，从同一个状态开始，把遗漏的信息逐条补回，找出真正决定结果的承重接口信息。第三，SkillStack 的开源 alpha release candidate 已经完成并推送，提供可安装 package、命令行、零模型 demo、追踪和测试。下一步准备先冻结 D→C 边界，在 ALFWorld 上验证 saved-state replay 和 boundary atom intervention，再决定是否扩展到 A→L。
