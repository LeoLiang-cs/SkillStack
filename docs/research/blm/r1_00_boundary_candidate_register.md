# R1-00 D→C boundary candidate register

日期：2026-09-16

审计基线：`67957b9b0630bbe80fde76ca9ca10a7834fad57a`

证据状态：本文件中的源码调用路径为本轮 `implemented + verified`；历史报告仅为 `historical evidence`。

## 分类标准

D→C 必须是 Discovery/Selection Producer 的输出，经 adapter 到达固定 Composition/Execution Consumer，并存在 Consumer 的真实读取点。字段仅存在、只做 schema validation、或 A→L proposer/updater 的输出，均不构成 D→C semantic read。

## 候选事实表

| ID | 真实调用路径 | D→C | 确定性 | Consumer read / outcome sensitivity | 首次 handoff replay | donor / 外部依赖 / 成本 | 结论 |
|---|---|---|---|---|---|---|---|
| C1 | `EpisodeRunner.run` → `OracleSkillRetriever.retrieve` 或 `DebugLexicalRetriever.retrieve` → `adapt_retrieval_for_execution` → `SkillPlanExecutor.execute` → `_choose_action` → `env.step` | 是 | Oracle、lexical、fixture 与 Consumer 均为确定性 | `selected_skill_ids[0]` 选择 `PLAN_STEPS_BY_SKILL`；本轮 heat fixture 中 Oracle 为 success，NoSkill 为 failure | 3 次 reference exact match；no-op exact match | static library/commit 可追踪；Oracle 仅作 calibration oracle；零网络、零模型、毫秒级 | **primary deterministic calibration boundary** |
| C2 | `EpisodeRunner.run` → 任一 Retriever → adapter → `ReActExecutor.execute(FakeClient)` → prompt construction / optional `extract_procedure_steps` → scripted reply → `env.step` | 是，但只支持 exposure/read calibration | FakeClient 确定性；真实 provider 不在本轮 | `flat_skill_context` 进入 prompt；structured 模式解析 `selected_native_skills[0]`；FakeClient reply 不随 prompt 改变，因此不能证明模型内部依赖 | fixture 可重建，但只重建 scripted client | 无 live provider；零费用；不能充当天然模型 Consumer | **deferred exposure/control calibration** |
| C3 | `EpisodeRunner.run` → 任一 Retriever → adapter → `RecordedActionExecutor.execute` → supplied `recorded_actions` → admissibility check → `env.step` | transport 经过 D→C，但 Consumer 不语义读取 Skill payload | 确定性 | 四字段只做存在性校验；动作来自 `recorded_actions`，outcome 对 Skill 信息不敏感 | 可重建 | 无 donor 需要；零网络、零模型、低成本 | **unread-information negative control** |
| C4 | GRASP `SkillUpdater.propose` → `adapt_grasp_output` → proposal envelope → `envelope_to_grasp_add` → GRASP gate/repository update | 否；A→L | 部分路径需 provider；deterministic gate 不是执行 Consumer | proposal/gate/admission，不是 task execution handoff | 与 C1 的环境 state 不同 | pinned external checkout；部分路径有模型依赖 | **excluded from first D→C calibration** |
| C5 | SkillRL updater/output → `adapt_skillrl_output` → proposal envelope → `envelope_to_grasp_add` → GRASP gate | 否；A→L | parser/gate 可确定；原 updater/provider 路径不保证 | 生命周期 proposal 被 gate 消费，不是 execution Consumer | 不适用 | pinned external source / provider-substituted history | **excluded from first D→C calibration** |
| C6 | GRASP Markdown → `adapt_directory` → opaque SkillOps contract → native maintenance → `export_payloads` → GRASP Markdown / later evaluation | 否；A→L | M1–M3 可零模型；M4 有外部 AgentBench/provider | maintenance/identity mapping，不是当前 D→C execution read | 不适用 | pinned SkillOps/GRASP checkout；M4 外部依赖较高 | **excluded; future lifecycle study** |

## C1 的实际调用证据

1. `EpisodeRunner.run` 创建环境后调用 `retriever.retrieve(task_record, initial_observation, native_skills, top_k)`。
2. `adapt_retrieval_for_execution` 从每个 candidate 读取 `skill_id`、`score`、`native_payload`，构造四个 execution fields。
3. `SkillPlanExecutor.execute` 先验证四字段存在，再只用 `selected_skill_ids[0]` 选择本地 plan registry。
4. task record 与 initial observation 经 `parse_task_semantics` 绑定 object/destination；initial/current `admissible_commands` 驱动每一步合法动作。这些是环境/Consumer state，不是 D→C payload。
5. `env.step` 返回 reward/done；Consumer 将 `done && reward > 0` 记录为 success。Runner 保存 actions、stop reason 与 outcome。

## 选择边界

- C1 满足 read site、首次 handoff replay、可追踪 calibration donor、环境 outcome 与对照可冻结五项硬门禁。
- C2 没有独立模型内部 read 证据，不能与 C1 争夺同一 primary scientific question。
- C3 的 unread 属性正好提供 negative control，而不是失败候选。
- C4–C6 保留其 A→L 身份；本轮没有把历史 2×2、proposal gate 或 maintenance outcome 改名为 BLM D→C evidence。
- 当前 **没有**可直接登记为 future natural case 的候选。未来 natural candidate 必须来自非 Oracle Producer、固定 Consumer 的真实失败/分叉，并重新通过 donor 与 replay gate；C2 只算 future exposure/control，不预占 natural-case 结论。

## Claim boundary

本登记只支持“当前 repository 存在可进入确定性 calibration 实现的 D→C 边界”。它不支持 BLM 已实现、契约已被 falsify、自然案例存在、ALFWorld benchmark 有效、或方法具有 novelty。
