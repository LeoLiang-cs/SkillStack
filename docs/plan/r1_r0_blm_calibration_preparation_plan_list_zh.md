# R1-R0 BLM 校准准备完成计划清单

## Material Passport

- Origin Skill: ars-codex:academic-research-suite / experiment-agent
- Origin Mode: plan
- Origin Date: 2026-09-16
- Verification Status: UNVERIFIED — 本文件是待执行计划，不是 BLM 实现或实验结果。
- Version Label: r1_r0_blm_calibration_preparation_plan_v1

## 0. 阶段定义

- 对应主计划：[SkillStack / BLM 科研主线计划 v4](skillstack_research_master_plan_v4_zh.md)
- 前置阶段：F0 研究工程基础，已完成。
- 后续阶段：R1-01～R1-05，依次完成 boundary freeze、replay、atom census、restoration controls 和 bounded verdict calibration。
- 状态：`planned`。
- 预计投入：单人约 1–2 个专注工作日；以 exit gate 为准。

`R1-R0` 正式定义为：**BLM 校准前的研究协议冻结与可行性审计**。它不运行正式实验，而是确认当前 repository 中至少存在一个可以合法测量的 D→C（Discovery/Selection → Composition/Execution）边界，并冻结后续实现所需的 Consumer、状态、read sites、donor、controls、outcome 和停止条件。

本阶段不需要训练、GPU、外部数据或 live model call；预期没有单项超过 30 分钟。若执行时出现超过 30 分钟的环境验证，只准备可恢复脚本和运行单，由 Leo 启动。

## 1. R1-R0 研究问题与假设

### Feasibility RQ

当前 SkillStack 是否至少有一个 D→C 路径，使 Producer 输出、adapter 变换、Consumer 实际读取、初始状态、合法 donor 和 outcome 都能在固定 Consumer 下被明确记录和确定性重建？

### 工作假设

- **H1（可行性假设）：** `Retriever → retrieval_to_execution adapter → SkillPlanExecutor` 可作为第一个确定性 calibration boundary。
- **H0（不可行条件）：** 当前候选无法在不注入答案、不直接改动作/reward/success、且不更换 Consumer 的前提下实现可比较的 replay 与 restoration。

H1 只支持“可以开始实现校准工具”，不支持“BLM 有效”“发现了隐藏依赖”或“契约不完整”。

## 2. 当前证据与候选边界

以下是制定计划时从当前源码得到的观察，不是 R1-R0 的执行结果：

| 候选 | Consumer 的实际消费 | 优点 | 限制 | R1-R0 建议 |
|---|---|---|---|---|
| `DebugLexicalRetriever/OracleSkillRetriever → adapter → SkillPlanExecutor` | 语义决策主要读取 `selected_skill_ids[0]`；task/observation 提供对象与目的地 | 零模型、确定性、read site 明确、outcome 可见 | skill-id→plan 是 SkillStack 手写映射；属于已知人工依赖 | primary calibration candidate |
| `Retriever → adapter → ReActExecutor(FakeClient)` | `flat_skill_context` 进入 prompt；structured 模式解析 `selected_native_skills` | 可校准 exposure 与 prompt carrier | fake replies 不会自然响应 prompt；不能代表模型内部读取 | secondary exposure/control candidate |
| `Retriever → adapter → RecordedActionExecutor` | 除输入形状校验外不使用 Skill 内容 | 稳定、零模型 | outcome 与 Skill 输入无关 | negative/irrelevant-information control only |
| GRASP/SkillRL/SkillOps proposer/updater 路径 | 当前主要属于 A→L | 有外部来源 | 不是首轮 D→C；状态与 outcome 不同 | excluded from R1-R0 |

默认推荐 primary candidate，但最终选择必须由 R1-R0-08 的证据表确认；若两个候选同等可行且会改变研究解释，再由 Leo 决定。

## 3. R1-R0 执行清单

### R1-R0-00 冻结审计基线

- [ ] 记录完整 Git SHA、branch、dirty worktree、Python/平台和日期。
- [ ] 固定本阶段只读源码范围：retrievers、D→C adapter、三个 executor、runner、deterministic fixtures、trace contract 和相关历史报告。
- [ ] 对所有输入标记 `implemented`、`historical evidence`、`proposal` 或 `not verified`，不把 framework/final cards 当实现证据。
- [ ] 建立 R1-R0 completion record；后续任何代码变更使用新 SHA 并说明原因。

交付：`report/week7/r1_r0_baseline_inventory_zh.md`。

### R1-R0-01 建立 D→C 候选登记表

- [ ] 枚举当前可运行的 Producer/adapter/Consumer 组合，不只列类名，还记录真实调用路径。
- [ ] 对每个候选评估：确定性、read-site 可观测性、outcome sensitivity、状态重建、donor 合法性、外部依赖和执行成本。
- [ ] 将 calibration candidate、negative control、future natural candidate 和 excluded path 分开。
- [ ] 禁止把现有 2×2 聚合结果或 A→L proposer/updater 路径重新命名为 BLM D→C 证据。

交付：`docs/research/blm/r1_r0_boundary_candidate_register.md`。

### R1-R0-02 冻结四层 boundary contract

对每个入围候选逐项填写：

- [ ] **Declared semantics：** 当前契约明确承诺哪些字段、意义、默认行为和任务域。
- [ ] **Transport availability：** adapter 后实际到达 Consumer 的字段、opaque payload、registry 和环境输入。
- [ ] **Observed access/exposure：** 区分 schema validation read、semantic decision read、prompt exposure 和完全未读取。
- [ ] **Outcome：** task success、action trace、stop reason、plan/grounding 与 measurement validity 分别如何记录。
- [ ] 明确契约主张；没有明确充分性主张时，不允许生成 `falsified` verdict。

交付：`docs/research/blm/r1_r0_boundary_contract_v1.md`。

### R1-R0-03 建立 Consumer read-site map

- [ ] 为每个输入 atom 记录源文件、函数、读取表达式、读取类型、下游分支和 trace 可见性。
- [ ] 对 `SkillPlanExecutor` 核查 `selected_skill_ids`、`selected_scores`、`selected_native_skills` 和 `flat_skill_context`，不能把“字段存在校验”写成“语义被消费”。
- [ ] 将 task record、initial observation、admissible commands 和 executor-local registry 与 D→C payload 分栏，避免把环境信息误判为 handoff atom。
- [ ] 对 prompt-based Consumer 只记录 exposure；除非有额外证据，不声称 LLM 内部读取或依赖。
- [ ] 列出静态审计无法证明的动态 read，并为 R1-03 instrumentation 留出明确 hook。

交付：`docs/research/blm/r1_r0_consumer_read_map.md` 与 machine-readable `configs/blm/r1_r0_consumer_read_map.json` 设计草案。

### R1-R0-04 冻结 replay state envelope

- [ ] 列出首次 handoff 前必须保存或重建的状态：task、Producer config/output、adapter output、environment state、initial observation/info、Consumer config/local registry、seed、budget 和 oracle。
- [ ] 规定确定性校准通过标准：相同 envelope 重建至少 3 次，boundary input、action trace、stop reason 和 outcome 必须 exact match。
- [ ] 规定 no-op instrumentation：记录机制开启但值不变；结果必须与无插桩基线 exact match。
- [ ] 区分“重新创建确定性 fixture”与“中途 snapshot replay”；R1 首轮只承诺首次 handoff 重建。
- [ ] 若任何隐状态无法捕获，标记 `abstained: replay_state_incomplete`，不继续解释 restoration effect。

交付：`docs/research/blm/r1_r0_replay_state_spec.md`。

### R1-R0-05 冻结 atom 与 donor 合法性规则

- [ ] atom 由 read site、semantic role 和可独立干预性定义，不只按 JSON 字段名拆分。
- [ ] 初始候选至少审计：skill identity/reference、native payload、flat context、score/rank 和 Consumer-local registry lookup。
- [ ] 将单 atom、不可分割 group、opaque payload 和未读取信息分别标记。
- [ ] donor 必须来自版本固定、来源可追踪、任务语义与 handoff 状态匹配的原生 artifact。
- [ ] 禁止使用 oracle 答案、未来轨迹、人工补写步骤或额外任务知识作为 donor。
- [ ] Oracle retriever 产生的 donor 必须标记为 calibration oracle，不得转化为 natural-case evidence。

交付：`docs/research/blm/r1_r0_atom_donor_rules.md`。

### R1-R0-06 冻结 calibration arms 与 outcome

- [ ] 固定同一 Consumer、同一 task、同一 replay state 和同一预算。
- [ ] 预定义最小 arms：reference、crossed、crossed-noop、crossed+single-atom、matched-carrier control、crossed+full-reference restoration。
- [ ] 增加 invalid donor/type/state rejection case 和 irrelevant/unread information negative control。
- [ ] 禁止直接设置 action、reward、done 或 success；干预必须在正常 Consumer 读取/解析前进入。
- [ ] primary outcome 为环境/task oracle；同时保存 action trace、stop reason、Consumer branch 和 validity reason。
- [ ] calibration 使用逐状态 exact comparison，不做无意义的 p-value 或功效声明。

交付：`configs/blm/r1_r0_calibration_protocol.yaml` 设计草案与 arm table。

### R1-R0-07 威胁、反驳与停止条件

- [ ] 明确 primary candidate 的 hard-coded skill-id mapping 只属于人工已知 calibration fault。
- [ ] 明确完整 native payload 已被 adapter 传输；“没有独立字段”不能自动称为“信息遗漏”。
- [ ] 明确 deterministic fixture 成功不是 ALFWorld benchmark 或自然案例证据。
- [ ] 如果 effect 与 matched carrier 相同、no-op 改变结果、donor 携带答案或 replay 不一致，则停止因果解释。
- [ ] 如果 Consumer 根本不读取候选 atom，则把它用于 negative control，而不是强行制造 restoration。
- [ ] 如果只有更换 Consumer 才能恢复，当前 boundary verdict 必须 abstain/fail，不能转写为 BLM 成功。

交付：candidate-specific threat register 与停止原因枚举。

### R1-R0-08 形成 boundary selection record

- [ ] 使用预先固定的评估维度给候选写事实表，不使用综合“创新分数”。
- [ ] 选择一个 primary deterministic calibration boundary、一个 negative control，并记录其不支持的 claim。
- [ ] 明确 R1-01～R1-05 的实施文件、测试入口、trace schema 增量和回滚边界。
- [ ] 将未选候选标为 `deferred` 或 `rejected` 并保留原因，不静默删除。
- [ ] 若没有候选满足 replay/read/donor/outcome 四项硬门禁，将 R1-R0 标为 `blocked_boundary_redesign`，不得进入 restoration 实现。

交付：`report/week7/r1_r0_completion_record_zh.md`。

## 4. R1-R0 Exit Gate

| Gate | 必须证据 | 状态 |
|---|---|---|
| R0-A Baseline | SHA、环境、文件范围与 evidence label 完整 | planned |
| R0-B Candidate register | 所有当前 D→C 路径已分类，排除项有原因 | planned |
| R0-C Contract | declared/transport/read/outcome 四层不混淆 | planned |
| R0-D Read map | validation、semantic read、exposure、unread 可区分 | planned |
| R0-E Replay | 首次 handoff state envelope 可 exact 重建；no-op 不改变结果 | planned |
| R0-F Atom/donor | atom 可操作且 donor 无答案泄漏、来源可追踪 | planned |
| R0-G Arms/outcome | controls、invalid cases、oracle 与 validity 已冻结 | planned |
| R0-H Claim boundary | calibration、natural case、benchmark claim 明确分开 | planned |
| R0-I Handoff | primary/negative candidate 与 R1 实施面已记录 | planned |

判定规则：R0-A 至 R0-I 全部 `verified` 才进入 R1-01。任何 `planned`、`assumed` 或依赖直接 outcome injection 的候选都不算通过。

## 5. 预期实施批次

### Batch 1：只读可行性审计

- 完成 R1-R0-00～03。
- 不改 runner、executor 或 trace；不运行 live provider。
- 若 primary candidate 没有真实 semantic read，立即停止，不为满足计划新增人为读取。

### Batch 2：协议与 replay 设计

- 完成 R1-R0-04～07。
- 只定义最小 state envelope、arms、donor 和 failure taxonomy；不提前实现通用 snapshot framework。

### Batch 3：选择与 R1 handoff

- 完成 R1-R0-08 和 exit audit。
- 输出下一批精确 code/test list；只有通过后才开始写 instrumentation 和 calibration fixture。

## 6. 当前预计不需要的人工决策

可直接推进：基线盘点、源码 read-site 审计、候选登记、状态 envelope、controls、donor 合法性和 threat register。

只有以下情况需要 Leo 决策：

1. 两个候选同时满足硬门禁，但会导致不同论文问题或显著不同工作量。
2. D→C 所有候选均失败，需要改测量边界或提前考虑 A→L。
3. 进入 live-model 或超过 30 分钟的验证，需要确认预算与运行时点。

在这些分叉出现前，R1-R0 可以直接执行。
