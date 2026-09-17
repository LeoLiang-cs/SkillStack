# SkillStack / BLM 科研主线计划 v4

- 日期：2026-09-16
- 状态：当前唯一主计划；取代 v3 的“开源工程 / BLM”双线组织方式。
- 主线：先完成 BLM 研究与论文，再统一整理 repository 的开源体验。
- 方法定义：[framework v2](../original/skillstack_draft_framework_2.md)
- 历史工程记录：[G0](g0_release_isolation_plan_list_zh.md)、[G1](g1_core_alpha_plan_list_zh.md)

## 1. 为什么合并 G0 和 G1

G0 与 G1 的拆分原本是发布工程顺序，而不是科研边界：

- G0 检查从哪个 commit、按什么范围生成公开候选。
- G1 检查实际 package、运行契约、测试和文档是否健全。

这个拆分适合“近期准备公开发布”的目标，但不是开展 BLM 的科学依赖。当前不准备发布，因此从科研项目角度把二者合并为一个已经完成的阶段：**F0 研究工程基础**。旧编号只为历史报告和 commit 可追溯性保留，不再作为两条独立主线。

## 2. 项目定位

项目只有一条主线：验证 BLM 是否能可靠识别 Skill Agent 组件交接处的隐藏信息依赖，并形成可审查的研究结论。

- SkillStack 是实现实验、重放、干预、追踪和复现的研究基础设施。
- BLM 是当前拟验证的研究方法与主要论文内容。
- repository 的可安装性、测试和安全边界服务于研究可靠性，但目前不单独追求发布形态。
- 开源不是另一条并行项目；它是论文和研究制品稳定后的最后整理阶段。

当前不能声称 BLM 已实现或有效。核心 claim 仍需由 calibration、自然案例、正式实验和基线比较支持。

## 3. 统一阶段与出口条件

| 阶段 | 内容 | 出口条件 | 状态 |
|---|---|---|---|
| F0 研究工程基础 | 原 G0+G1：repo 基线、运行契约、trace/resume、测试、package smoke、CI、安全边界 | 本地与 hosted gate 通过；研究运行可追踪、可恢复 | complete (`fc6a446`) |
| R1 BLM 定义与校准 | 明确 D→C handoff、Consumer read sites、boundary atoms、合法 donor、replay 与 controls | 确定性校准套件判断正确；无效干预会拒绝或 abstain | complete_calibration_only |
| R2 自然案例与增量 | 筛选真实跨组件案例；比较 schema check、ablation、restoration 等简单基线 | 至少一个有效自然案例或有价值的可靠阴性；明确 BLM 的增量与成本 | planned |
| R3 正式协议与实验 | 冻结任务、arms、重复数、预算、统计、排除和停止规则；执行确认实验 | raw evidence 完整；结果可重算；发现集与确认集分离 | planned |
| R4 论文完成 | 完成方法、实验、相关工作、限制、图表和 claim-evidence map | 每项论文主张能映射到实际数据、代码和 manifest | planned |
| P1 论文后开源整理 | 重组上手路径、示例、文档、CITATION、release packet、tag/GitHub Release/PyPI | 新用户在干净环境完成教程；公开范围与论文制品一致 | deferred_after_paper |

F0 之后不再插入独立“开源完成 gate”。只有会损害实验正确性、证据完整性、可恢复性或安全性的工程问题，才阻塞 R1–R4。

## 4. 当前下一阶段：R1 BLM 定义与校准

R1-00 已按 [BLM 测量可行性与实验协议审计清单](r1_00_blm_calibration_preparation_plan_list_zh.md) 完成，冻结候选边界、四层契约、read-site map、replay envelope、donor 与 controls。执行证据与 R1-01 handoff 见 [R1-00 completion record](../../report/week7/r1_00_completion_record_zh.md)。R1-01 已完成首次 boundary instrumentation；R1-02～R1-05 依次实现 replay、atom census、restoration controls 与 bounded verdict，分别以独立清单为准。

### R1-01 实现第一个测量边界

状态：`complete`（实现与 hosted CI 已验证；仅限 calibration instrumentation，不是 BLM validity verdict）。

- 使用 R1-00 已选的 `Retriever → adapter → SkillPlanExecutor`，不再重新选 boundary。
- 在 adapter return 后、Consumer read 前增加默认关闭的最小 capture/intervention hook；不改变 Consumer 让其读取新字段。
- 只实现 first-handoff boundary record、donor/type/state validation、identity read atom 与 unread negative probes。
- opt-in trace 保存 original/effective input hash、read-map ID、arm、Consumer branch 与 validity reason；禁止 outcome setter。
- focused test 复用 R1-00 heat fixture，并运行完整 core/credential/hosted CI gate。

验收：default-off、3× replay 与 no-op exact；合法 intervention 在 Consumer read 前生效；invalid donor/type/state 在 Consumer 前拒绝；unread changes 不产生 semantic effect。完整 R1-01 文件与测试入口以 R1-00 completion record 为准。

### R1-02 建立状态重建与 no-op 基线

状态：`complete`；唯一实施清单为 [R1-02 首次 handoff replay 清单](r1_02_blm_first_handoff_replay_plan_list_zh.md)。

- 保存环境状态、Consumer 本地状态、输入历史、预算和 oracle 所需信息。
- 在确定性 fixture 上验证相同状态重建后的无干预行为一致。
- no-op intervention 不得改变后续行为；漂移时停止因果解释。

验收：重复执行产生一致状态与行为；漂移被明确检测，而不是被 summary 吞掉。

### R1-03 建立 boundary-atom census

状态：`complete`；执行依赖 R1-02 envelope/replay；唯一实施清单为 [R1-03 boundary-atom census 清单](r1_03_blm_boundary_atom_census_plan_list_zh.md)。

- atom 由 read site、semantic role 和可独立干预性定义，不只是字段名。
- 记录 atom 的来源、类型/值域、合法 donor、读取次数和顺序。
- opaque text 中的信息、联合依赖和不可独立操作项分别标记，不强拆成伪单项。

验收：每个 atom 都能追溯到 Consumer 的真实读取或明确的不可观察边界。

### R1-04 实现合法 restoration 与 controls

状态：`complete`；执行依赖 R1-03 census；唯一实施清单为 [R1-04 restoration controls 清单](r1_04_blm_restoration_controls_plan_list_zh.md)。

- 通过正常 parser/Consumer 路径注入，不绕过被测接口。
- 最小 arms：reference、crossed、crossed-noop、crossed+atom、载体 control、crossed+full restoration。
- donor 必须语义与状态匹配，不能包含 oracle 答案、未来轨迹或额外解题提示。

验收：错误 donor/type/state 被拒绝；control 能区分信息效应与注入载体效应。

### R1-05 校准 bounded verdict

状态：`complete_calibration_only`；执行依赖 R1-04 controls；唯一实施清单为 [R1-05 bounded verdict 清单](r1_05_blm_bounded_verdict_calibration_plan_list_zh.md)。

- 分开记录 `measurement_status` 与研究 verdict。
- verdict 只允许 `falsified`、`not_falsified` 或 `abstained`，并绑定适用范围。
- 覆盖已知单项依赖、无关信息、adapter 丢字段、opaque text、联合依赖、非法 donor、replay 漂移和中断恢复。

验收：全部预定义案例产生预期判断；任一 calibration failure 阻塞自然案例。

## 5. R2–R4 科研规则

- 先做小规模确定性 calibration，再使用 live model；单次成功不作为证据。
- 自然案例筛选必须保留失败、无差异和被排除候选，不能只报告正例。
- 2×2 组件组合实验与 BLM 局部诊断回答不同问题，分别定义 estimand。
- 正式实验前冻结 manifest、任务划分、重复数、预算、统计和停止规则。
- 超过 30 分钟或涉及训练/大规模模型调用的任务写成可恢复脚本，由 Leo 启动。
- 阴性结果可以完成研究；不通过调整任务或 claim 追逐预设正结论。

## 6. 当前不做的开源工作

在 R4 完成前，不以以下事项阻塞科研：

- alpha tag、GitHub Release、PyPI。
- release packet、公开文件精修和面向陌生用户的完整教程。
- `CITATION.cff` 作者顺序与公开元数据。
- 为展示效果而新增与研究问题无关的集成或抽象层。

仍持续执行的底线包括：`.env`/credential 不入 Git、raw evidence 不覆盖、运行可恢复、CI 不被破坏、外部来源与 fidelity 可追踪。

## 7. 当前执行顺序

1. 以 `fc6a446`/`730a37a` 之后的 `main` 作为 F0 工程基线。
2. 完成 R1-01 的 first-handoff capture、单 atom intervention、unread negative probes 与 validity guards。
3. 完成 R1-02/R1-03 的 deterministic replay 与 atom census spike。
4. 完成 R1-04/R1-05 controls 和 bounded calibration；R1 当前出口为 `complete_calibration_only`。
5. 下一步只筛选真实自然 D→C 案例和简单基线，不自动进入 live model 或 R3 正式实验。
5. R2 结果足以支持研究价值后，才冻结 R3 正式协议。
6. 完成 R4 论文后启动 P1 开源整理，不反向改写历史实验结果。

当前不需要重新选择 boundary。只有实现中出现多个同等可行但回答不同论文问题的 handoff、所有 D→C 候选失效、或需要 live model/训练/超过 30 分钟验证时，才暂停请求人工决策；其他 R1-01 源码审计、确定性测试、文档、质量 gate、commit、push 和 CI 修复直接推进。
