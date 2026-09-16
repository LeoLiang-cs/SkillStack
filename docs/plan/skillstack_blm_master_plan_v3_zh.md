# SkillStack 开源工程与 BLM 完整执行计划 v3

## Material Passport

- Origin Skill: ars-codex:academic-research-suite / experiment-agent
- Origin Mode: plan
- Origin Date: 2026-09-15
- Verification Status: UNVERIFIED — 实施计划，非完成报告；现状证据另列。
- Version Label: skillstack_blm_master_plan_v3
- 依据：用户要求“开源项目辅助 BLM，但也要完全健全”。
- 状态：当前完整计划；取代 [计划 v2](project_plan_v2_zh.md) 的排期和工程完成标准，保留其研究约束。
- 方法定义沿用 [framework v2](../original/skillstack_draft_framework_2.md)；任务拆解见 [执行清单](skillstack_blm_execution_backlog_v3_zh.md)。
- 本地研究材料；尚未批准纳入任何公开发布清单。现有 collector 不会自动落实这个标记，必须先完成 O01。

## 1. 总目标与完成定义

交付一个第三方能够安装、理解、扩展、运行、恢复、审计和维护的 Skill 组件实验工具，并用它完成 BLM 的方法验证、真实案例、正式确认和研究制品。

开源工程的范围由 BLM 的可复现需求决定；工程质量独立验收。BLM 没有正结果也必须能交付可用的 SkillStack。BLM 出现正结果，也不能豁免安装、故障恢复、数据完整性与发布检查。

“完全健全”指下表所有承诺均有证据、无阻断性缺口，不意味着覆盖所有操作系统、论文、模型或成为生产SaaS。

| 维度 | 完成标准 |
|---|---|
| 安装与分发 | 源码安装和实际wheel安装分别验证；必需资源随包提供或由明确参数定位；不依赖开发者目录 |
| 用户路径 | 新用户按文档能运行零模型demo、解释输出、运行已支持实验；出错有可执行诊断 |
| 组件扩展 | 外部贡献者按一个最小示例接入组件，无需修改相邻组件的业务逻辑；支持范围明确 |
| 数据与运行可靠性 | manifest冻结、身份/hash校验、追加证据、恢复时拒绝配置漂移，失败和部分结果可审计 |
| 测试与持续集成 | 快速离线门禁、安装包验收、关键失败路径、可选集成层分开；跳过不冒充通过 |
| 依赖与平台 | 声明并测试支持矩阵；核心与历史环境依赖分离；有升级/回归策略 |
| 文档与维护 | quickstart、架构、实验协议、输出格式、接入教程、troubleshooting、贡献/安全/版本规则完整 |
| 发布与来源 | 从明确版本导出文件清单；license/provenance/fidelity可追踪；制品及hash与已验收版本对应 |
| BLM研究制品 | 不依赖作者私有上下文即可重算表格/判定；有小型公开案例、原始数据获取边界和复现说明 |

## 2. 现状与新发现

已有：可运行harness、零模型demo、CLI、基础CI、MIT及第三方记录、Week 1–5实验。旧的
108/127-test 结果保留为历史证据；2026-09-16 本地当前套件为 137 passed、1 conditional
skip，hosted CI 和最终 SHA 仍未完成。本轮不将旧检查冒充当前发布验收。

本轮直接检查得到：

1. **发布文件选择存在实际缺口。** `collect_release_files()` 递归读取工作区docs/reports，仅显式hold `docs/final_cards/`。只读调用实际选中了未提交framework v0/v1/v2、scoop-check和Week 6文件，合计255文件（本轮新文档写入前快照）。这不是已经外传；它说明“未tracked”和“文档标记private”不能防止进入本地发布快照。O01是发布阻断项。
2. **源码checkout通过不等于独立安装包可用。** demo读取repo中的examples/skills，模型配置也有repo-relative路径；现有发布检查在clone内安装和构建。独立wheel在其他目录使用的能力尚未验证，O02必须实测后修复或明确收缩承诺。
3. **支持版本需要更新。** 当前metadata限定Python 3.9/3.10。按[Python官方生命周期](https://devguide.python.org/versions/)，3.9已结束维护、3.10计划于2026-10结束维护。主核心应验证较新受维护版本，历史外部实验保留锁定环境，不能为升级改写旧实验结果。
4. **续跑与trace有基础但没有统一BLM契约。** 已有原子checkpoint和部分manifest检查；BLM仍需确保所有影响干预结果的字段参与身份校验，以及重复arm、截断写入、调用失败的明确行为。
5. **公开文档存在状态漂移。** release audit/notes仍有“等待push/hosted CI”的历史状态；测试总数与skip表述也需校正。

因此，v2中的0.5–1天只适用于文档/发布手续。完整工程加固先预留5–10个专注工作日，并与BLM场景核查交错推进；发现问题后依据验收重估。

现状证据：[release实现](../../src/skillstack/release.py)、[CLI](../../src/skillstack/cli.py)、[demo](../../src/skillstack/demo.py)、[项目metadata](../../pyproject.toml)、[CI](../../.github/workflows/ci.yml)、[trace writer](../../src/skillstack/tracing/jsonl.py)。

## 3. 工作线、依赖与交付版本

三条工作线共同推进：O=开源工程，B=BLM方法与工具，E=实验与论文。每条任务的依赖和验收见执行清单。

依赖顺序：O01/O02消除分发风险；B01/B02尽早确定契约与案例；O04/O05支撑B03–B06；校准通过后进入E01自然案例；自然案例与直接相关工作比较支持E02正式冻结；E03/E04完成确认与制品发布。

| 里程碑 | 包含内容 | 出口条件 |
|---|---|---|
| G0 基线和发布隔离 | O01；保存既有证据/版本；确定公开与研究范围 | 发布候选来自明确commit或显式清单；未知/held文件默认不进入；无未解释diff |
| G1 健全的核心alpha | O02–O07；最低支持矩阵、文档、维护、实际制品验证 | 下文工程验收全部通过；明确可选集成状态；可准备正式alpha发布 |
| G2 BLM测量校准 | B01–B06；同时完成B02来源可行性 | 确定性校准通过；状态、正常消费路径、控制、判定可复算 |
| G3 真实案例与研究价值 | E01、B07 | 自然案例有有效诊断/可靠阴性；与简单基线的增量有具体判断 |
| G4 正式实验冻结与执行 | E02、E03 | manifest/任务/重复数/预算/统计规则先冻结；完整保留结果，完成独立确认 |
| G5 研究制品和论文交付 | E04、O08 | 第三方复现通过；制品版本、表格、论文主张可逐一对应 |

版本采用三个里程碑而非现在宣布新tag：core alpha、BLM experimental release、paper artifact release。只有稳定承诺和迁移路径被验证后才考虑1.0；不以“完全健全”为由提前承诺稳定API。

正式tag和公开BLM材料是发布动作；本轮只制定计划。技术验收和公开范围决策分开，公开研究材料暂缓不会阻塞本地科学验证。

## 4. 开源工程完整工作包

### O01 发布隔离与基线

逐项实施顺序、回归用例和退出表见 [G0 发布隔离完成计划清单](g0_release_isolation_plan_list_zh.md)。

- 优先从指定Git commit构建公开快照；工作区候选只能通过显式清单进入，且必须有diff和hash。
- 建立公开/暂存研究/外部数据/生成结果四类清单，检查源码archive、wheel、sdist三种制品，不能只检查repo文档。
- 未提交文档、symlink指向repo外、路径穿越、私有研究文件均有防误入测试；秘密检查不打印命中值。
- 保留现有dirty工作区和原始实验；实施时按审阅范围单独提交，不用宽泛stage捕获所有文件。
- 验收：向fixture增加一个未tracked研究文件不会改变发布清单；held文件不会出现在任何拟发布制品。

### O02 安装与资源访问

O02–O07 的完整实施顺序和 G1 退出表见 [G1 健全核心 Alpha 完成计划清单](g1_core_alpha_plan_list_zh.md)。

- 明确两个入口：普通用户安装包运行demo/分析；贡献者checkout运行repo检查和开发。
- 将demo所需轻量资源纳入包资源，或实现文档明确的示例获取流程；核心默认配置不能依赖作者checkout。
- repo专用命令接受明确root并报告缺失；环境/provider配置使用显式来源和优先级，输出有效配置时去除secrets。
- 在新环境实际安装wheel和sdist，切换到非仓库目录测试import、version、demo、配置解析；检查license、metadata和内容。
- 交付GitHub release制品及校验和；PyPI为可选分发渠道，后续确认包名和发布方式，不作为BLM前置。

### O03 支持矩阵与依赖

- 建议核心先验证Python 3.11/3.12及Linux/macOS；这是目标矩阵，未测试前不宣称支持。Windows暂标未验证。
- ALFWorld/AgentBench/旧论文环境单独记录锁定版本；若现代Python不兼容，采用独立环境/既有服务边界，不强行升级复现实验。
- 保留历史Python 3.9/3.10复现说明；区分historical reproduction与maintained support。
- 核心安装不隐式加载外部数据/模型服务；optional extra、源码commit与依赖清单可定位。记录依赖升级影响和已知问题。

### O04 稳定的实验运行与输出契约

- 稳定最小公共面：组件调用契约、配置、manifest、trace、summary；内部实现允许演化。R–A–D–C–L维持责任词汇，不要求五个全功能插件系统。
- 外部组件用显式adapter接入；保留native payload与来源；拒绝不支持的语义而非静默补全。
- run manifest记录代码/组件/数据/库/配置hash、模型实际ID、prompt、解码、预算、seed作用域、oracle和schema版本。
- 区分task failure、运行错误、无效干预、超时、未完成和主动abstention；summary同时列计划/启动/完成/有效/失败/跳过计数。
- resume检查影响结果的全部字段；配置变化新建run。重复执行不重复统计完成arm；部分写入保留并可诊断。
- raw证据只追加；修订summary生成新版本或明确derived文件，不覆盖原始记录。工程使用单写入者/独立run目录等最简单可靠方案。

### O05 测试分层

| 层 | 触发 | 必需验收 |
|---|---|---|
| Core offline | 每次PR | 核心契约、demo、manifest/trace完整性、错误路径；不调用模型/下载数据 |
| Packaging | 发布候选和分发相关PR | wheel/sdist脱离checkout安装；受支持环境；资源和清单检查 |
| Integration offline | adapter相关PR | 小型来源允许的fixture、round-trip、unsupported语义、邻接不变 |
| ALFWorld local | 环境/runner变更和研究里程碑 | 已获取数据的真实reset/step/oracle测试；缺数据写skip原因 |
| Live provider | 明确启动的小规模预检 | 响应格式、timeout/retry、usage、后端标签；记录费用，不在普通CI隐式运行 |
| BLM calibration | BLM变更 | replay/no-op/恢复/错误donor/预算/判定分支与全部校准案例 |
| Formal evidence | 冻结协议运行 | 配对完整性、排除日志、分析重算；不以单元测试代替研究结果 |

测试依据风险覆盖，不追逐任意覆盖率百分比。G1不能靠跳过必需路径通过；不支持的可选环境可以明确标记，而非承诺全覆盖。

### O06 用户与贡献者文档

- README：定位、支持矩阵、最短安装路径、首个demo、输出解释、真实实验与研究状态。
- 用户手册：配置/CLI、ALFWorld数据准备、外部组件获取、运行/续跑、费用预检、结果解释、常见故障。
- 开发者手册：责任边界图、schema版本、最小Retriever/Executor接入示例、adapter规范、测试方法。
- 研究手册：fidelity标签、任务划分、随机性、trace、有效性/abstention、统计与主张边界。
- 发布资料：CHANGELOG、迁移说明、CITATION.cff、许可证/第三方清单、贡献规范、安全报告途径、维护者与支持范围。作者/邮箱仅使用已核实信息。
- 文档中的命令都要实际验证；未实现功能明确标记planned。旧实验保持日期与当时状态，增加当前索引说明。

### O07 安全、维护与发布

- 为实验代码、外部组件和模型文本明确执行边界；只运行明确配置的代码路径，日志不暴露凭证，输出路径不能逃逸目标目录。
- 配置请求timeout、有限重试、总预算、取消与恢复行为；验证API错误不会污染有效结果。
- PR/issue模板与现有CI衔接，检查工作流权限及依赖来源；记录更新和回滚策略。
- 从验收SHA构建发行制品，保存版本/hash/测试摘要/兼容矩阵；清晰说明回退到上一个tag/配置的方法，不改写原始数据。
- 每个里程碑和依赖升级后复核支持状态、已知问题、文档与fidelity；不承诺无维护能力支撑的响应SLA。

### O08 BLM研究制品产品化

- 保留零模型上手demo，并增加小型BLM诊断案例和“如何阅读边界图”教程。
- 从原始记录生成判定/图表/报告的路径可由第三方执行；统计结果与代码/manifest hash绑定。
- 输出公开最小trace或可合法取得的重建步骤；私有/不可再分发数据不混入release。
- 让未参与开发者在干净环境按文档复现；无人可参与时标记为自动化隔离复现，不能称独立人工验证。

## 5. BLM完整工作包

### B01 问题、契约与声明范围

保留主问题：固定Consumer与起始状态，哪些交接信息的合法恢复改变结果，这些信息是否构成被测契约的遗漏？

冻结boundary-specific契约；分别记录declared semantics、transport availability、observed access/exposure、outcome effect。历史Canonical Interface v1不自动成为外部方法的规范。

区分契约遗漏、已声明但实现丢失、已传输但未使用、执行器知识/能力差异。LLM prompt可见不等于已观察内部语义读取；完整参考恢复不是性能上界。

### B02 首个场景与论文组件筛选

- 从现有代码读点开始，用SkillPlanExecutor等确定性路径做校准；硬编码依赖标为本地已知机制。
- 同期检查已有GRASP host与SkillRL retrieval相关来源资产。当前proposer/updater属于A→L，不能拿来充当D→C native对角线。
- 每个外部候选记录source commit、license、native artifact、Consumer读点、原生参考可运行性、donor匹配、预算与阻塞。
- 选择机制不同且可比的第一组；新增模块必须补上具体实验轴。第二组用于独立确认，不要求无边界地接入更多论文。
- 原生参考、任务语义和合法donor无法成立时，记录失败并限时重选一次。仍失败则评审边界选择，避免无限集成。

### B03 状态与重放

先研究初始化后的首次handoff，以reset重建同一起点。记录环境任务状态、Consumer本地状态、输入、历史、计数器、预算、oracle；相同observation文本不足以验收。

确定性路径比较状态和无干预后续行为。中途snapshot或reset+动作前缀作为后续能力，需要另通过相同门禁。在线LLM的temperature=0不提供确定性保证；重复实验、执行顺序平衡和误差估计另行处理。

缓存仅用于合法重复输入或干预前固定前缀；改变Consumer输入后不能重放旧后续答案来证明效果。

### B04 Atom census与合法干预

atom以read site、semantic role和独立可干预性定义；记录重复读取、顺序、值域约束、来源、donor、声明/传输状态。被裁切/不可观察的部分显式标记。

donor来自语义和状态匹配的原生artifact/读取，不来自oracle答案、未来轨迹或额外解题提示。干预通过正常parser/Consumer路径；保持非目标条件一致。无法独立操作的联合信息按group定义，不能拆成无效单项。

### B05 Arms、controls与判定

必需arms：同Consumer兼容参考R、crossed X、X-noop、X+a、匹配载体control、完整参考恢复X+F；有依据时加入预注册group及R-a。不同Consumer之间总差异只用于组合分析，局部恢复效应始终固定Consumer。

输出measurement_status与contract_verdict。局部有效反例可推翻具体充分性主张；阴性结论只覆盖完成的有限干预域；无效状态、donor、control或精度不足触发abstention。

### B06 校准套件

| 案例 | 预期能力 |
|---|---|
| 已知单项依赖人工缺失 | 合法恢复能检出效应；标签为校准 |
| 无关信息 | 不误报为承重依赖 |
| 已声明字段被adapter丢失 | 区分实现不遵守与契约遗漏 |
| 信息在opaque文本中但无独立字段 | 不因字段名缺失而误报传输遗漏 |
| 单项无效、联合有效 | 保留交互与残余，不能宣布完整 |
| 非法donor/类型/跨字段组合 | 拒绝或标为无效干预 |
| 重放漂移/no-op改变行为 | 阻止无根据的因果结论 |
| 中断、重复arm、预算耗尽 | 可恢复、无重复计数，未完成可见 |

所有预定义确定性案例的预期判断必须一致通过，任何失败保留为阻断项。套件验证实现正确性，不证明真实世界漏洞存在。

### B07 直接相关工作与基线

正式冻结前完成方法级对照：schema/静态检查、adapter friction日志、逐字段ablation/restoration、适用的delta debugging、agent故障归因/反事实重放。来源和阅读范围记录在比较表中；不继承旧idea-spark结论作为新版本novelty证明。

同一合法候选集、oracle和预算比较；同时报告BLM census构建成本。评估定位有效性、误归因/abstention、覆盖范围和调用成本，不只报告任务成功率。

若简单方法同样有效且成本相当，将贡献收缩为Skill领域的协议、工具与实证；不通过改名维护算法创新主张。

## 6. 实验、统计与论文路线

### E01 开发pilot与自然案例

先用3个开发任务、确定性重复作调试规模；这一数量没有统计功效含义。选择规则在看结果前记录，审查逐任务与trajectory，而非只看聚合成功数。

校准通过后进行来源明确的自然移植，保存全部筛选、无差异、失败与无效案例。只有自然案例有可测信息依赖或有价值的严谨阴性结果，才决定是否扩大。

### E02 正式协议冻结

- 固定RQ/主张、组件/邻居、数据/代码hash、契约、atom粒度、donor、arms、oracle、模型/解码、budget和停止规则。
- 分开发现任务与独立确认任务，记录历史使用重叠。不动既有SkillOps held-out test 20。
- 2×2用于组件组合/交互观察，BLM用于固定Consumer局部诊断；分别定义estimand和表格。
- 以pilot的方差、失效率和目标精度/最小相关效应估算样本数及重复数；不得凭惯例填一个N并称充分。
- 预先规定任务级聚类、配对区间、探索性多重比较处理和独立确认规则。replay/atom不是独立任务样本。
- 对随机LLM的contract反例规定确认规则和不确定性阈值；单次成功不够。
- 冻结总费用/调用/时长上限、retry和错误处理；变更配置创建新run和协议版本。

### E03 正式执行与分析

交付精确可续跑命令和预检报告，由Leo启动长任务；失败数据保留，恢复行为按协议执行。主表包括计划/完成/有效数、配对效应、区间、controls、abstention原因、成本和来源标签。

报告无差异与负效应；full-payload无法恢复时保留残余。对已识别问题提出最小契约修订，在独立任务上检查目标改善、回归和成本，不让发现任务承担确认职责。

### E04 论文与制品

稿件围绕问题、测量定义、有效性、真实案例、基线、独立确认、限制组织。SkillStack是工程贡献，BLM方法与实证的强度由实际结果决定。

完成claim→table→raw evidence→manifest→code版本映射；从原始数据重建图表。目标venue与截止时间另行核查，不用旧日期驱动本计划。

没有自然反例时，可以交付有效阴性与可行性研究；无法证明独立方法增量时，按系统/工具贡献定位。科研交付的完成不以获得预设正结论为条件。

## 7. 资源、分工和运行边界

工程/文档/零模型验收由实现协作者推进；Leo负责科研取舍、长模型任务启动、最终公开范围与投稿决定。计划不假设有额外人手；有独立复现者时用于G5。

第一阶段默认本地CPU、已有ALFWorld数据和现有来源资产，无训练/GPU前置。live provider先做小规模成本预检，再给正式预算。

工作量估算：T任务 × C固定Consumer场景 × R重复 × (5 + K单项 + G联合)，另加组合筛查、可选删除检查和失败预算。真实费用按实际input/output tokens、provider价格与重试计；历史美元数仅作背景。

实施时交付运行单：精确命令、工作目录、依赖、manifest、run ID、预计时间/费用及上限、监测文件、取消方法、恢复命令、输出判读。当前BLM命令尚不存在，不能伪造为已可执行。

每次推进只集中于一项工程变更和一项研究不确定性。先完成它们的验收，再扩大范围；核心稳定接口和BLM实验性接口分别标注。

## 8. 排期与决策点

以下是单人投入的规划窗口，工作包可交错，不把各窗口机械相加；结束条件以gate为准。

| 窗口 | 工程交付 | 研究交付 | 决策 |
|---|---|---|---|
| 第1–2个工作日 | O01，安装包检查清单，缺口登记 | B01/B02最小契约与来源盘点 | 确定支持范围和首个案例 |
| 第1–2周 | O02–O07，核心alpha验收 | B03/B04，首个消费点与状态校准 | G1是否通过；重放是否可行 |
| 第3周 | BLM运行/记录路径与失败测试 | B05/B06与B07对照梳理 | G2；不合格则停效果实验 |
| 第4–5周 | 必要的单一外部集成 | E01自然案例、简单基线与候选第二案例 | G3；继续、缩小或更换边界 |
| 第6周 | 正式批处理与分析验收 | E02样本/预算/协议冻结 | 决定正式实验规模 |
| 第7–8周 | 可复现制品与文档完善 | E03独立确认、契约修订与结果表 | G4；质量不足则补明确缺口 |
| 第9–10周 | O08、版本与复现交付 | E04论文与制品核对 | G5；按证据决定论文定位 |

这是约8–10周的初始工作框架，不是工期承诺。第一周和G3后必须按实际兼容性/案例/方差重估；若只有兼职时间，按实际可投入工作日换算。

## 9. 停止、降级与完成验收

- 发布文件不受控或wheel核心路径不可用：阻断公开发行，继续本地修复，不以已有CI绿灯豁免。
- 状态/no-op不合格：暂停效果归因；先修工具。
- B02候选均不可比：限时重选一次；仍失败时评审D→C范围，不能用人工正例代替真实案例。
- calibration通过但自然案例不支持假设：保留阴性；不无限调整任务追逐效果。
- 简单基线等价：调整为协议/系统贡献，保留工程成果。
- 成本上限或超时：终止新增调用并保存checkpoint；状态记partial，不能记完整实验。
- G1完成须O01–O07验收；G5完成须G2–G4证据以及O08/E04复现。未做任务显式列出，不用整体百分比掩盖。

## 10. 本轮完成与下一执行批次

截至 2026-09-16 的执行增量：O02/O04/O05/O06/O07 已完成一批可直接推进的本地技术项，
包括 wheel/sdist fresh-venv 验收、配置优先级、retry/budget、manifest/summary identity、
offline contract fixture、文档和 CI action pin；代码已改，发布未执行，BLM 仍未运行。
完整证据见 [Week 7 G1 继续执行报告](../../report/week7/g1_continuation_execution_report_zh.md)。

下一批按 gate 顺序执行：Leo 确认 G0 窄范围项目 commit → 在同一 SHA 上跑 hosted CI 与最终
source/wheel/sdist packet → G1 release-ready 审计；随后才进入 BLM G2 calibration。B01/B02
可以在不改变 core release scope 的情况下准备，但不能把计划卡当作已执行实验。

v2仍保留为历史。framework v2继续定义研究idea，无需为扩充工程计划再发明新方法；本v3新增的是完整工程承诺、证据门禁和实施依赖。

参考：[Python生命周期](https://devguide.python.org/versions/)用于支持矩阵排期；[PyPA packaging guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/)用于区分源码、wheel和sdist交付；这些来源不证明当前项目已经满足分发验收。
