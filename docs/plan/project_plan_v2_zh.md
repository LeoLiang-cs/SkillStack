# SkillStack 项目计划 v2：开源收尾、BLM 可行性与定向扩展

## Material Passport

- Origin Skill: ars-codex:academic-research-suite / experiment-agent
- Origin Mode: plan
- Origin Date: 2026-09-15
- Verification Status: UNVERIFIED — 以下实验尚未执行；仓库与来源检查见第 2 节。
- Version Label: project_plan_v2
- 状态：供采用的具体计划；不代表已经冻结实验配置、发布版本或运行 BLM。
- 发布范围：本地研究规划，暂不纳入 public alpha。与 [framework v2](../original/skillstack_draft_framework_2.md) 配套使用。

## 1. 优先级决策

建议顺序：**短期完成开源技术收尾 → BLM Phase 0 → 按诊断缺口接入论文组件 → 冻结正式实验 → 论文与研究制品发布。**

开源收尾设工时上限，不再增加 alpha 功能。正式 tag 的发布决定可以与研究进展解耦；如果发布范围尚未确定，就冻结已验证 commit 作为研究基线，继续 Phase 0。

BLM 是下一阶段主线。外部组件的可用性核查在 Phase 0 早期进行：本地实验负责检验测量工具；真实来源案例决定是否值得继续投入。避免把所有本地工具做完后才发现没有合适的自然案例。

暂缓无具体假设的大量模块接入。只有某个组件能补上一个明确的边界差异、真实消费路径或独立验证案例时，才进入实现队列。

## 2. 当前证据与决策依据

| 已有证据 | 本轮核查方式 | 对计划的影响 |
|---|---|---|
| main 为 `f7cc44f499a176bbf4621de3f55dc55ff7739664`，远端一致，无 tag | 本轮读取远端 heads/tags | alpha 剩余工作有限，不应成为长期前置工程 |
| Hosted CI 成功 | [CI run 34449640120](https://github.com/LeoLiang-cs/SkillStack/actions/runs/34449640120) | release notes 中“尚待 push / 首次 hosted CI”已过时，应在发布收尾时修正 |
| 上一轮现场检查：测试套件共 108 项，1 项 skip，其余通过；公开扫描 247 文件零发现，demo 通过 | 当前对话上一轮实际运行，本轮未重复运行 | 已有工程基线；不能把 108 项都称为无跳过通过 |
| 2×2 四个 cell 均为 5/9，control 为 3/9 | [Week 3.2 报告](../../reports/week3_2/w3_2_advisor_brief_zh.md) | 聚合成功率无差异，不代表逐任务行为相同；先审查逐任务、消费路径和测量灵敏度 |
| A-slot 130 episodes 与 maintenance 144 episodes 已完成 | [Week 5 报告](../../reports/week5/skill/week5_weekly_report_zh.md) | 已有跨论文边界基础，但不等于已有 D→C BLM native/crossed 配对 |
| adapter 传递完整 native text；SkillPlanExecutor 有 skill-id → plan 映射 | 当前源文件读取，见下方路径 | 不能把未结构化字段自动称为未传递信息；硬编码是候选耦合，不是已证实契约遗漏 |
| 当前环境包装提供 reset；没有已验证的中途 checkpoint/replay 接口 | 当前环境包装与 framework v1 | 首轮固定首次消费前的 handoff，优先验证 reset 重建相同状态 |
| BLM 仍是 proposal | [framework v1](../original/skillstack_draft_framework_1.md) | 先做测量可行性和真实案例；不直接扩大正式实验 |

源文件：[adapter](../../src/skillstack/adapters/retrieval_to_execution.py)、[SkillPlanExecutor](../../src/skillstack/execution/skillplan.py)、[ALFWorld wrapper](../../src/skillstack/environments/alfworld_text.py)。

上一轮给出的“alpha 90% / 论文 50%”只是主观估计，不作为后续管理指标。本计划用可验收的里程碑代替百分比。

## 3. 里程碑与退出条件

下列工时是单人专注工作的规划估计，不是已经测得的耗时或交付承诺；正式模型实验耗时需在小样本测量后单列。

| 阶段 | 建议投入 | 交付物 | 通过条件 / 未通过时的处理 |
|---|---|---|---|
| M0 开源技术收尾 | 0.5–1 工作日 | 最终公开文件清单、更新后的 release 状态、冻结基线 | 所选发布 commit 的 fresh-clone 检查通过；如 tag 决策待定，使用冻结 commit 进入 M1 |
| M1 问题与案例可行性 | 2–3 工作日 | 契约声明表、消费点清单、首个外部案例可行性卡、初始 replay 检查 | 明确测什么、从何处读取、干预什么、参考值来自哪里；无可用自然案例则限时重选一次 |
| M2 测量工具校准 | 3–5 工作日 | 本地已知依赖/无关信息/已声明丢失的 calibration cases、恢复实验记录 | 在固定 Consumer 上识别已知效应，no-op 控制有效；人工缺失只作为校准证据 |
| M3 首个自然边界案例 | 1–2 工作周 | 来源固定的 handoff、crossed run、restoration map、逐案例结论 | 可归因的恢复效应或完整记录的阴性/不可测结果；只在人工案例有效则停止扩大论文主张 |
| M4 定向扩展与正式实验冻结 | M3 后重新估工 | 第二独立案例、原生参考与交叉组合矩阵、正式 manifest、统计方案 | 新案例能检验迁移性；任务/重复数由试验方差和目标精度决定，不沿用任意固定数 |
| M5 论文与研究制品 | 正式证据后重新估工 | 结果表、边界图、失败案例、可复现包与稿件 | 结论与已执行总体对应；novelty 与基线增量有证据；按目标 venue 决定发布范围 |

M0 完成后，建议工作精力约 70% 用于 BLM 实现和小试验、20% 用于案例来源与直接相关文献、10% 用于工程维护。这是排期建议，不是额外算力预算。

### M0 的具体清单

1. 修正 release notes 中已过时的 hosted-CI/push 状态。
2. 审阅拟公开的精确文件清单；Week 6、BLM、idea-spark 中间产物及论文全文不自动加入 alpha。
3. 在拟发布 commit 上复核安装、demo、tests 和 build；新的研究文件不能改变这个基线。
4. 记录 release SHA、依赖版本、通过的 CI；正式创建/push tag 属于后续发布动作，本轮未执行。
5. 从此 alpha 只处理阻止复现的问题；大规模 plugin registry、dashboard、更多 benchmark 不进入 M0。

## 4. M1–M3 的实验计划

### 4.1 研究问题与假设

主问题：在固定的 Skill handoff 中，保持接收方、任务状态和执行预算不变时，哪些交接信息的恢复会改变任务结果？这些信息属于契约已声明但实现丢失、经 opaque payload 传输但语义未明确、契约范围内未声明，还是契约范围之外的执行器知识？

待检验假设：对于至少一类自然组件移植案例，普通 schema/adapter 检查不足以描述结果相关的边界依赖；接收方观测和受控恢复可以提供额外的、可复算的定位证据。这个假设允许被否定。

### 4.2 两层证据

- **Calibration 层：** 使用已有 SkillStack 消费路径验证工具。优先考察已报告的 skill-id/plan 耦合；只有 native read path 和允许的干预位置清楚时才使用。必要的故障注入必须显式标为人工构造，不代表自然接口漏洞。
- **Natural-case 层：** 在固定来源版本、可追踪 native 行为的组件之间进行真实移植。不能为了制造正结果事后删除字段或改变契约。没有观察到遗漏也是结果。

第一层可以先用确定性 Executor；LLM Executor 的结果另行验证。手写执行器中的已知映射只能用于校准和局部案例，不能代表现代 Skill Agent 的一般行为。

### 4.3 首轮范围

- 主边界：D→C，即 Skill 选择结果交给组织/执行组件。
- 首个干预位置：episode 初始化后的首次消费前；暂不承诺任意执行点的完整状态快照。
- 开发任务：优先从已使用任务中按预定语义规则选择 3 个涉及不同操作的案例；这只是调试规模，无统计功效含义。
- 不使用 SkillOps 的未开启 held-out test 20。未来正式 BLM 数据另建开发/确认划分，并记录与历史任务的重叠。
- 不把 GRASP proposer 与 SkillRL updater 当成 D→C 两端：它们现有实验属于 A→L。
- 完整 2×2 保留为后续组合设计；现有本地 2×2 没有两个外部原生系统，不能事后给对角线补上 native 标签。

### 4.4 变量与比较

实验单元为 `(task, fixed consumer, handoff state, candidate atom/group, replicate)`。

自变量是 handoff 中指定信息的取值/可用性。主因变量为 ALFWorld goal success；动作序列、步数、解析/拒绝/fallback 与成本为辅助诊断。

保持 Consumer 源码、后续 prompt 模板、模型配置、环境版本、非干预输入、预算和停止规则固定。prompt 中由目标 atom 引起的局部变化是处理的一部分，额外载体变化必须被控制。

| Arm | 作用 |
|---|---|
| R：同一 Consumer 的可用原生/兼容参考输入 | 提供参考值来源与局部参考结果；不能用另一个 Consumer 的表现替代 |
| X：crossed 输入，不恢复 | 基线 |
| X-noop：相同插桩与写入路径，内容不变 | 检验工具本身是否改变行为 |
| X+a：恢复一个合法 atom | 测量单项局部恢复效应 |
| X+matched-control | 对照额外文本、长度、位置、序列化等载体效应；确定性路径可用已知无关字段 |
| X+F：恢复预定义、语义兼容的完整参考 payload | 检查可恢复范围与残余；不是性能上界 |
| X+group：预先允许的小组联合恢复 | 单项无效而完整恢复有效时，检查交互依赖 |

可补充 `R-a` 的删除检查，用于区分局部 sufficiency 与 necessity；成功恢复不自动证明该 atom 必要、唯一，或解释了全部 native/crossed 差异。

reference donor 必须与 task、skill 语义、状态和 Consumer 兼容，来源为实际 native artifact 或可审计的原生读取。来自测试答案、future trajectory、人工额外解题提示的信息不得作为“遗漏信息恢复”。无法匹配 donor 的案例只报告不可归因。

### 4.5 契约与消费观测

冻结三份独立对象：文档声明、实际 transport payload、Consumer 可见的依赖。Canonical Interface v1 是历史草案，不能自动作为所有外部方法已经承诺遵守的接口。

每个 atom 记录来源、read locus、类型、原值、替代值来源、传输状态、语义声明状态、干预范围、oracle outcome 和 trace ID。按 read site + semantic role 定义粒度；序列位置、重复读取和跨字段约束需要被保留。

LLM 路径中的“进入 prompt”只代表模型可见，不等于证明模型内部读取了该语义。通过结果干预测量效应，并把内部不可观测性写入限制。

### 4.6 Replay、有效性与分析

首先验证 reset 后的初始环境、oracle 相关状态、Consumer 输入、局部内存、计数器与预算一致。只比较 observation 文本不足以证明环境状态一致。若内部状态不可观测，记录具体限制并收缩结论。

对确定性校准路径，首次使用 3 次重复作故障检查，要求声明范围内状态和无干预轨迹一致；这是调试检查，不是统计证明。扩展到中途干预时，可以评估 snapshot 或 reset + 固定动作前缀，必须重新通过状态与无干预重放检查。

对在线模型，temperature=0 不保证相同输出。不把任务顺序 seed 写成模型 seed。配对固定任务/起点，随机化或平衡执行顺序，独立收集重复；报告配对效应和区间，按 task 聚类，不能把同任务多个 atom/replay 当作独立任务样本。

可以重放干预前的固定前缀；输入变化后必须重新执行 Consumer。缓存原来的后续回答不能构成干预效果证据。oracle 只评分，不为干预提供答案。

开发阶段只输出逐案例计数和有效性诊断。正式阶段预先确定主指标、效应阈值/目标精度、重复数与多重比较控制；探索发现用未参与选择的任务确认。

### 4.7 比较基线与结果判定

必须比较：schema/静态契约检查、现有 adapter friction log、相同合法候选和预算下的逐字段 ablation/restoration，以及适用时的 delta debugging。BLM 的差异应体现在诊断的有效性、契约遗漏/实现丢失区分、独立案例迁移或调用效率；只有重新命名不足以构成方法贡献。

输出两个维度：`measurement_status`（valid / invalid / insufficient）和 `contract_verdict`（falsified / not_falsified_in_tested_domain / abstained）。

- 有效反例可以推翻该具体契约主张，即使其他 read sites 尚未覆盖；仍需标注覆盖限制。
- 没发现效应且预算/覆盖不足时，结论是 abstained；不能写接口完整。
- 已声明内容被 adapter 丢失，归为 implementation nonconformance；它不是声明本身的遗漏。
- full-payload 没有恢复成功时检查 donor、Consumer 差异、重放和覆盖；不能自动断言接口无问题。
- gap=0、atom 效应=0、控制失败均保留；禁止不断换任务直到出现正结果。

## 5. 新论文模块的接入门槛

每次只接入一个能回答明确问题的组件。选择前填写：

1. 改变的是哪种边界依赖，而不仅是模型或超参数？
2. 源码、版本、license、native artifact 和正常消费路径能否取得？
3. 原生参考是否可运行；任务与消费者是否能做有意义的配对？
4. 能否固定相邻组件；修改 adapter 时是否引入额外语义？
5. 需要什么实验才会支持或否定接入假设；预计工程/API成本多少？

优先审查已有来源资产中的 GRASP host 消费路径与 SkillRL released retrieval 路径，但这只是待核查候选，不把 updater 的成功接入当作 retriever 已完成。只有新组件能产生机制不同、可观测的 D→C handoff，才实施集成。

typed/DAG 类组件可作为后续异质性候选；既有 crosswalk 标注缺少官方源码的项目必须重新核查后再排期。禁止把论文启发的重建代码称为原论文复现。

A→L 扩展、SkillOps semantic maintenance、第二环境和大规模全组合矩阵推迟到 M3/M4 gate 之后。

## 6. 成本、运行与停止规则

本轮只修改研究文档，不启动模型实验、安装新模块或发布 tag。

首轮零模型 calibration 使用当前 Python/ALFWorld 环境，无 GPU/API需求。在线部分的预算需在预检后冻结：若有 T 个任务、R 次重复、K 个单项 atom、G 个联合 probe，上表所有 arm 的 continuation 上限为 `T × R × (5 + K + G)`，另计 native/crossed 筛查和可选删除检查。这个式子是工作量核算，不是独立样本数。

正式命令尚不存在，不能给出伪造的 BLM 运行命令。实现交付时必须附精确命令、输入manifest、预计耗时/API费用、续跑方式、超时和总预算上限、输出目录；由 Leo 启动长任务。

建议新增产物路径，均尚未创建：

| 产物 | 计划路径 | 验收要求 |
|---|---|---|
| 组件与契约冻结 | `configs/blm/phase0_manifest.json` | commit、契约、donor、task、control、预算与分析规则齐全 |
| 状态/消费记录 | `runs/blm/<run_id>/state_checks.json`、`census.jsonl` | 可定位到实际读点与状态，完整记录不可观测项 |
| 原始干预与结果 | `runs/blm/<run_id>/interventions.jsonl`、`outcomes.jsonl` | 每个arm可追踪；无效/超时不记作普通任务失败 |
| 判定与对照 | `runs/blm/<run_id>/verdicts.json`、`baseline_comparison.json` | 可由原始证据重建，覆盖与未决项可见 |

停止/转向规则：

- M1 中无法构建合法对照：先重选一次有来源的边界，保留失败记录。
- M2 中插桩/no-op/replay无效：停止效果实验，先修测量路径。
- M3 中仅人工构造案例有效、自然案例没有可审计效应：完成可行性/负结果报告，暂缓大规模扩展。
- 简单基线获得相同证据且成本相当：缩小为应用/系统贡献，不继续声称独立算法创新。
- 若 D→C 在限定试验后持续没有可测依赖，重新讨论已有 A→L 案例；更换边界必须新建协议，不能沿用旧 verdict。

## 7. 本次 idea 修订要点

保留 SkillStack、R–A–D–C–L、controlled swap、2×2组合逻辑、native payload与可审计恢复。将主张收敛到 **Skill handoff contract 的范围受限诊断**，并加入三项必要约束：

1. declaredness 与传输可用性分别判断；
2. 固定 Consumer 估计局部恢复效应；
3. 校准、自然案例、独立确认依次建立证据。

完整方法定义、反例条件与来源边界见 [framework v2](../original/skillstack_draft_framework_2.md)。旧框架与 idea-spark 原始卡片保留，v2 是本轮人工研究修订，不继承旧生成流程的校验标签。

## 8. 来源与文献核查范围

- [Delta Debugging — 作者教材](https://www.debuggingbook.org/html/DeltaDebugger.html)：已核查方法说明，支持将其纳入简单对照；不意味着 BLM novelty 已确定。
- [AgentDebug — 作者 arXiv 摘要](https://arxiv.org/abs/2509.25370)：本轮摘要级核查，说明 agent failure diagnosis/recovery 已有工作；方法级差异仍待全文核查。
- [ALFWorld 官方仓库](https://github.com/alfworld/alfworld)：环境来源；未据此推断 SkillStack 当前包装支持任意状态恢复。
- [Week 4 crosswalk](../../reports/week4/02_paper_analysis/architecture_crosswalk.md)：已有组件资产与旧来源状态，只用于候选筛选，不代表今日所有外部项目状态。

本轮是项目决策与方法修订，不是完整、穷尽的 novelty review。正式实验前应针对程序依赖追踪、delta debugging、counterfactual agent debugging 完成方法级比较。
