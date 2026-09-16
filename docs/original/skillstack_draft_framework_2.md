# SkillStack / BLM v2：面向 Skill 交接契约的可执行诊断

## Material Passport

- Origin Skill: ars-codex:academic-research-suite / experiment-agent
- Origin Mode: plan / existing-idea refinement
- Origin Date: 2026-09-15
- Verification Status: UNVERIFIED — BLM 尚未实现或完成实验。
- Version Label: skillstack_draft_framework_2
- 状态：研究修订方案；本地保存，暂不纳入 public alpha。
- 前版：[framework v1](skillstack_draft_framework_1.md)。执行计划：[项目计划 v2](../plan/project_plan_v2_zh.md)。

## 1. 一句话 idea

**在真实 Skill 组件交接中，固定接收方与起始状态，观测它可见的信息，并受控恢复来源可追踪的原生信息，以检验交接契约是否遗漏了会影响任务结果的依赖。**

建议工作标题：**Boundary Load Mapping: Auditing Skill Handoff Contracts with Controlled Restoration**。

SkillStack 提供实验基础设施；Boundary Load Mapping（BLM）是拟议诊断协议；边界负载图、范围受限的反例与可复现案例是计划产物。独立的方法贡献仍需与已有调试和消融方法比较。

## 2. 为什么现在这样调整

现有基础设施已经支持组件交换、可审计adapter、外部proposer/gate与maintenance实验。继续接入模块可以扩大覆盖，但不会自动回答交换差异的原因。

同时，现有 2×2 的四个 cell 成功计数相同。这个小样本结果没有证明组件独立，也没有证明完全不消费 Skill，但说明不能假定它们天然适合做“隐藏信息恢复”的测量场景。

当前 adapter 将完整 `native_payload` 同时作为 `selected_native_skills` 和 `flat_skill_context` 交给 Executor。因此，“某语义没有单独schema字段”与“某信息没有传过来”必须分开。此前关于 `required_appliance` 的示例只能作为假设示例，不能直接当成当前实现已经发生的遗漏。

进一步说，传统 [delta debugging](https://www.debuggingbook.org/html/DeltaDebugger.html) 已经通过输入差异与重复执行定位失败条件，[AgentDebug](https://arxiv.org/abs/2509.25370) 已研究 agent 失败诊断与恢复。BLM 的待验证增量应落在 Skill 交接契约、原生值来源、可执行消费路径与结论有效性，而非“第一次通过干预定位失败”。后者本轮只核查摘要，未完成方法级排除。

## 3. 保留与修订

| 保留 | 本轮修订 |
|---|---|
| R–A–D–C–L 作为责任坐标 | 不把 taxonomy 或通用架构当作主要 novelty |
| controlled swap 与 2×2 | 用于发现组合差异；局部因果诊断另固定 Consumer，不混为同一估计 |
| receiver-side observation | 程序 read 可观测；进入 LLM prompt 只代表可见，不能称为已观测模型内部读取 |
| native artifact / explicit adapter | 先核查信息是否已在 opaque text 中，避免人为定义“遗漏” |
| per-atom restoration | 有明确donor、合法取值、正常消费路径与载体控制才有效 |
| full native-payload control | 改称完整参考恢复对照；信息更多可能降低效果，不是性能上界 |
| replay gate | 从首次handoff和reset重建开始；temperature=0不等于确定性 |
| bounded verdict | 输出有限范围的契约判断；不称完整性证书 |
| interface revision | 经独立确认后形成候选修订，保持 implementation-first |

## 4. 研究问题

- **RQ1：什么差异值得诊断？** 固定任务条件下，组件交换产生哪些逐任务/行为差异，哪些是检索质量、执行能力、实现错误或交接契约问题？
- **RQ2：哪些信息影响结果？** 在同一 Consumer 与handoff状态下，恢复哪些原生信息会改变任务结果；这种效应是否超过no-op与匹配载体对照？
- **RQ3：契约应如何解释？** 有效效应属于已声明但未遵守、已传输但语义未约定、契约内未声明，还是契约外知识？
- **RQ4：诊断能否迁移并改善契约？** 在独立组件/任务上，诊断能否复现，基于它形成的明确交接约定是否减少同类失败？

A→L 作为后续扩展，不列为首轮必须完成的主问题。正式论文范围由 D→C 的可行性、真实案例和对照增量决定。

## 5. 被检验的契约

每次实验冻结一个 boundary-specific contract，而非把历史 Canonical Interface v1 强加给所有论文模块。契约应写明：输入信息、来源和类型、允许的状态/registry、身份与版本语义、缺失时的默认或失败行为，以及它声称支持的任务域。

分别记录：

1. **Declared semantics：** 契约明确承诺哪些意义与依赖？
2. **Transport availability：** 信息实际是否到达 Consumer，可能是字段、文本、registry或上下文？
3. **Observed access/exposure：** 哪些read sites或prompt segments被观测？
4. **Outcome effect：** 有效干预是否改变oracle结果？

据此区分以下情况：

| 情况 | 合理诊断 |
|---|---|
| 已声明的 procedure 被adapter丢弃 | 实现未遵守契约；不宣称新发现未声明语义 |
| procedure已包含在native text中，执行器未解析/利用 | 消费或表示问题；不叫信息未传输 |
| Consumer依赖特定skill ID的本地映射 | 可能是身份/registry约定或Consumer知识；先判断是否属于所测交接契约 |
| 契约未规定的原生上下文通过正常路径恢复后改变结果 | 有限范围内的契约遗漏候选，仍需对照和来源检查 |
| 恢复内容来自oracle答案或额外人工解题知识 | 干预不合格；不能当作遗漏原生信息的证据 |

只有当契约自身声称交接信息足以支持相关行为、而有效反例与这一主张矛盾时，才对该主张判 `falsified`。信息的名称或存储位置本身不能决定这个判定。

## 6. 方法与可识别效应

### 6.1 配对原则

在探索性组合矩阵中可以运行 D1/C1、D2/C2及交叉组合，但“native”必须有真实来源系统作依据。不同Consumer之间的成功率差是总交换差异，混有执行能力、prompt与组件实现等因素。

BLM的恢复实验使用同一个 Consumer C，同一任务与重建起点 s。令 x 为 crossed handoff，a_ref 为语义兼容且来源可追踪的参考值，则局部效应为：

`Delta_a = E[Y(C, s, restore(x, a_ref))] - E[Y(C, s, x)]`

期望只针对已声明的在线执行随机性；确定性校准时退化为逐状态结果差。它不能直接解释另一个Consumer与当前Consumer之间全部性能差，也不自动证明必要性或唯一原因。

### 6.2 六个步骤

1. **冻结契约与来源。** 固定组件commit、task、Consumer、预算、允许信息、donor对齐规则、atom粒度、取值域与结论范围。
2. **建立消费记录。** 从实际read/exposure记录值与来源；同时标出契约字段、opaque payload、共享registry和环境输入，不把它们合并成一个“是否声明”布尔值。
3. **验证起点与工具。** 初始化handoff优先使用reset重建；核查环境和Consumer状态。比较无插桩与no-op插桩，确认测量路径不会产生目标效应。
4. **执行合法恢复。** 从同一起点运行crossed、single-atom、matched-control、完整参考恢复与预定义group arms。改动在正常读取/解析前生效，不硬设动作、reward或success。
5. **比较并检查残余。** 对每个atom报告效应、原始结果、控制有效性和未解释部分。完整参考恢复有效而单项无效时，测试预注册小组；不能由单项零效应推出无依赖。
6. **形成边界图与契约判断。** 按依赖类别组织结果，输出validity、verdict、覆盖范围与未决项；后续候选接口修订在独立任务上确认。

### 6.3 Replay边界

保存对象必须包括影响后续行为的环境状态、执行器局部状态、模型上下文和预算。第一阶段只承诺经验证的首次handoff重建；中途snapshot或固定前缀重放是后续能力。

在线LLM后续轨迹可能随机分叉；不能把同seed或temperature=0等同于完全重放。固定前缀可以重用，处理输入改变后必须重新运行后续Consumer。对随机结果使用重复、配对统计与控制，不靠挑一次恢复成功作归因。

### 6.4 对照

最少包括 no-op插桩、crossed基线、匹配载体的无关干预、完整参考恢复。语义干预改变prompt长度或位置时，应增加等长度/等位置控制，不能只加一个完全不进入prompt的无关metadata。

同一合法候选集与调用预算下，与静态schema检查、adapter friction log、逐字段恢复/消融和适用的delta debugging比较。需要研究的是新增诊断价值；对照更简单且同样有效时，应主动下调方法贡献。

## 7. 证据路线与成功条件

**Calibration → natural case → independent confirmation。**

- Calibration成功：已知依赖能被测到、无关信息不被误判、工具失败能被识别。人工故障注入只证明测量实现可用。
- Natural-case成功：来源固定的真实交接案例能够得到有效诊断，包括负结果。不能在看过结果后改契约或donor定义来制造“遗漏”。
- 研究主张成立：在独立任务/组件确认中，BLM提供超过简单基线的可复算诊断，或揭示有实践价值的契约失配规律。存在一个精心构造案例不足以支持一般性。
- 接口修订成功：仅修改有证据支持的交接约定，在未参与发现的案例中减少目标失配，同时报告新增成本与回归。

自然案例筛选日志需列出全部候选、排除理由、无差异案例和失败恢复，避免只报告正例。正式任务数量与重复数待试验方差、目标精度和预算明确后冻结。

## 8. 判定语义与反驳条件

`measurement_status` 与 `contract_verdict` 分开记录：

- **falsified：** 存在有效干预反例，推翻某条预先声明的契约充分性主张；该结果可局部成立，无须声称已穷尽其他read sites。
- **not_falsified_in_tested_domain：** 在明确、有限且完成测试的干预域内未发现反例；不推广到全部任务、取值或隐状态。
- **abstained：** 覆盖、donor、状态恢复、控制或统计精度不足以作判断；附具体原因。

以下结果会收缩或否定预期研究贡献：

1. 所有有效信息都已在声明且传输的payload中，所谓遗漏只是字段命名问题。
2. 恢复效应与匹配的无关文本/格式改动相当，无法支持语义依赖解释。
3. 只有校准中人为删除的信息能被恢复，自然案例没有相同现象。
4. 只有替换Consumer实现或注入额外答案才恢复成功，固定Consumer的合法恢复无效。
5. 简单字段消融/delta debugging在相同预算下提供相同诊断，BLM没有清楚增量。
6. 重放与干预路径不能达到所需可比性，研究只能报告可行性限制。

这些是停止扩大或调整论文定位的条件，不是继续搜索正结果的理由。

## 9. 当前能写与不能写的贡献

已实现：SkillStack实验harness、组件交换路径、Week 1–5证据、alpha release candidate；本轮核实hosted CI成功，正式tag仍不存在。

拟议贡献：可审计的Skill handoff诊断协议；声明/传输/消费/结果的分层记录；有效反例与明确弃权；通过受控实验形成的契约修订建议。

尚无证据：BLM已有效、普遍隐藏依赖存在、完整接口已认证、跨论文组件可任意插拔、基于BLM的修订已改善泛化结果。正式novelty仍需补齐与程序依赖追踪、delta debugging及agent counterfactual debugging的全文比较。

## 10. 与历史材料的关系

本文件是当前建议的研究方向；v0/v1和 `docs/final_cards/` 中的原始idea卡保持原样用于追溯。原始卡片中“完整性证书”“temperature-0确保完全重放”“所有相邻工作都没有相关测量”等表述不能作为当前结论引用。

本轮未重新运行idea-spark全流程，也未继承其原始validator通过状态。所有新方法与实验条件均为待实现、待检验方案。
