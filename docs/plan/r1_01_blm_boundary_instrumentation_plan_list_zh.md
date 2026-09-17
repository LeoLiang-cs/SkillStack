# R1-01 BLM 首次边界捕获与干预机制实现清单

## Material Passport

- Origin Skill: `ars-codex:academic-research-suite / experiment-agent`
- Implementation discipline: `ponytail:ponytail`
- Plan status: `IN_PROGRESS`
- Plan date: 2026-09-16
- Starting commit: `c31f270827f5c50a6c82562d02323f1ad688fc94`
- Starting branch: `main`
- Starting worktree: clean; synchronized with `origin/main`
- Evidence boundary: zero-model, zero-network, deterministic first-handoff fixture

## 1. 目标与固定研究边界

R1-01 在 R1-00 已选定的真实路径上实现最小、默认关闭的测量机制：

`Retriever → adapt_retrieval_for_execution → SkillPlanExecutor`

本阶段只证明：

- 可以在 adapter 完成后、Consumer 首次读取前捕获 boundary input；
- 可以合法替换一个已确认被读取的 atom：`selected_skill_ids[0]`；
- 可以对未读字段做 negative probe；
- 可以拒绝 donor、类型、状态或来源不合法的干预；
- 默认关闭及 no-op instrumentation 不改变原有执行结果。

本阶段不产生 BLM 的 `supported` / `falsified` verdict，不运行自然案例、live model、训练、统计显著性分析，也不实现 R1-02～R1-05。

本阶段的 identity restoration 只属于 SkillPlanExecutor 手写 dependency 上的 calibration-only evidence；不把它写成自然案例、benchmark 或 novelty evidence。

## 2. 执行清单

### R1-01-00：基线与计划落盘

- [x] 新建本文件，作为唯一 R1-01 执行计划。
- [x] 记录执行前 SHA、branch、upstream、dirty 状态、Python、平台、日期和 R1-00 handoff。
- [x] 更新科研总计划中将 boundary 选择误写为 R1-01 工作的旧表述；boundary 已由 R1-00 冻结。
- [x] 不修改 R1-00 冻结的 contract、read map、replay spec、donor rules 和 protocol。

### R1-01-01：冻结最小接口与状态摘要

- [x] 在 `EpisodeRunner.run(...)` 增加向后兼容的 keyword-only `blm_intervention=None`。
- [x] `None` 时不调用 BLM 模块、不增加 sidecar，并保持既有行为。
- [x] hook 固定在 adapter return 后、`executor.execute(...)` 前。
- [x] 只允许 `SkillPlanExecutor` 使用 R1-01 hook；其他 Consumer 返回 `invalid_input`。
- [x] 保持 top-level `skillstack-episode-trace-v1` 不变，sidecar 单独使用 `skillstack-blm-boundary-v1`。
- [x] `state_sha256` 覆盖 task、initial observation/info、environment class、Consumer config、Consumer-local registry digest、`top_k` 和实际 `max_steps`。
- [x] 明确状态范围为 `first_handoff_reconstructed_fixture_v1`；不宣称通用隐藏状态或中途 snapshot replay。

### R1-01-02：实现内部 boundary 模块

- [x] 新增单一内部模块 `src/skillstack/blm.py`，不建设通用 intervention framework。
- [x] 实现 `apply_boundary_intervention(execution_input, request, context)`。
- [x] 实现 `finalize_boundary_record(record, executor_report)`，只回填 Consumer 产生的 branch/outcome observation。
- [x] request schema 固定为 `schema_version / arm_id / operation / atom / expected_state_sha256 / donor`，拒绝未知字段。
- [x] operation 只允许 `capture` 和 `copy_atom_from_donor`；不接受自由 replacement。
- [x] atom 只允许 `selected_skill_ids[0]`、`selected_scores[0]`、`selected_native_skills[0]`、`flat_skill_context`。
- [x] donor 只能来自真实 retrieval response，经现有 adapter 重建后再复制 atom。
- [x] 验证 task/task family/state、native artifact、payload hash、library hash、score 类型、list 对齐和 calibration-oracle 来源。
- [x] 递归拒绝 action/reward/done/success/trajectory/future observation 等 outcome 或未来信息。

### R1-01-03：Runner 集成与 trace sidecar

- [x] valid sidecar 记录 boundary ID、state scope、arm、operation、atom、read-map ID、state/input hashes、changed、donor provenance、intervention position、validity reason。
- [x] `intervention_position` 固定为 `post_adapter_pre_consumer_read`。
- [x] `consumer_branch` 和 `outcome_observation` 只在 Consumer 执行后由 Runner 写入。
- [x] invalid request 不调用 Consumer，写入 `stop_reason=invalid_input`、空 action/reward、`executor_report={}` 和精确 validity reason。
- [x] 不把 valid calibration sidecar 伪装成 benchmark measurement success；global writer semantics 保持不变。

### R1-01-04：确定性 calibration fixture

- [x] 新增 `tests/test_blm_r1_01_boundary.py`，复用 R1-00 heat fixture。
- [x] 覆盖 `reference`、`crossed`、`crossed_noop`、`crossed_single_atom`。
- [x] 覆盖 `selected_scores[0]`、`selected_native_skills[0]`、`flat_skill_context` 三个 unread probes。
- [x] reference/crossed/no-op/identity/unread arms 均比较 action、raw observation、reward、branch、stop reason 和 oracle outcome。
- [x] 同一 reference capture 至少重建 3 次并要求 exact match。

### R1-01-05：拒绝路径和副作用

- [x] 覆盖 donor task、task family、state、payload、score、schema、arm、atom、list alignment、forbidden content 和 unsupported Consumer rejection。
- [x] 验证 NoSkill 空列表不能伪造 identity restoration。
- [x] 验证所有 invalid request 在 Consumer 调用前停止。
- [x] 验证 JSONL writer 将 invalid request 标记为 `measurement_status=invalid`、`task_success=null`。
- [x] 验证 default-off 和 no-op instrumentation 的 behavior exact match。

### R1-01-06：证据和状态文档

- [x] 生成 `report/week7/r1_01_boundary_fixture_evidence.json`，记录实际 SHA、arms、hash、provenance、branch、outcome、replay 和 rejection evidence。
- [x] 生成 `report/week7/r1_01_completion_record_zh.md`，区分 implemented、verified_this_run、calibration-only、historical evidence、proposal、not verified 和 excluded claim。
- [x] 生成 `report/week7/r1_01_core_gate_local.json`，只记录实际运行的本地 gate。
- [x] 只给出 R1-02 的精确 handoff；不提前实现 R1-02～R1-05。

### R1-01-07：质量检查、提交和 hosted CI

- [x] 运行 focused boundary tests、R1-00 replay regression 和完整 core gate。
- [x] 运行 repository preflight、public/credential scan、compile、package build 和 `git diff --check`。
- [x] 检查当前 diff 不含 `.env`、API key、Authorization、credential、generated runs 或外部数据。
- [ ] 正常单一 commit、push 当前分支并等待 hosted CI 完成。
- [ ] CI 失败若可在本地安全修复则直接修复、重新验证并 push；否则保留失败证据。

## 3. 冻结的 request / donor / sidecar contract

### request

```text
schema_version
arm_id
operation
atom
expected_state_sha256
donor
```

`capture` 要求 `atom=null`、`donor=null`、`expected_state_sha256=null`。`copy_atom_from_donor` 必须带当前 handoff 的 exact `expected_state_sha256` 和合法 donor。

### donor

```text
kind
task_id
task_family
state_sha256
retrieval_response
```

`calibration_oracle` 只接受 `retriever_name=oracle_skill`；`producer_output` 在 R1-01 只用于与当前 crossed output 完全相同的 no-op。donor 不得带 action、reward、done、success、trajectory 或未来 observation。

### sidecar

```text
schema_version
boundary_id
state_scope
arm_id
operation
atom
read_map_id
state_sha256
original_input_sha256
effective_input_sha256
changed
donor_provenance
intervention_position
validity
validity_reason
consumer_branch
outcome_observation
```

outcome observation 由 Runner 只读回填，至少包含 Consumer `success`、`stop_reason` 和 action-trace SHA-256。

## 4. Calibration arms 与验收硬门禁

| arm | 输入 | 预期检查 |
|---|---|---|
| `reference` | Oracle capture | heat branch、oracle success、3× exact |
| `crossed` | Random seed 1 capture/default-off | wrong branch、oracle failure |
| `crossed_noop` | crossed donor copy identity | 与 crossed behavior exact、`changed=false` |
| `crossed_single_atom` | Oracle donor copy identity | 只改变 `selected_skill_ids[0]`，恢复 heat branch；calibration-only |
| `irrelevant_unread_information` | Oracle donor copy score/native/flat | 与 crossed behavior exact |

只有以下门禁全部实际通过才可将状态改为 `complete`：

- default-off 不改变既有 API 和行为；
- hook 位置确实位于 adapter 后、Consumer read 前；
- reference/crossed/no-op 至少 3× exact replay；
- identity atom 可独立改变，其他 boundary payload 保持 crossed；
- unread probes 不改变 branch/outcome；
- invalid donor/type/state/source 在 Consumer 前拒绝；
- sidecar、provenance、read-map ID 和 validity reason 完整；
- local quality gate、credential scan、push 和 hosted CI 均有实际证据；
- completion report 不越过 calibration-only claim boundary。

## 5. 停止条件、排除范围与下一步

若 default-off/no-op 改变结果、replay 漂移、unread probe 改变 outcome、invalid donor 未被拒绝，或 identity restoration 需要更换 Consumer/直接设置 outcome，则分别记录 instrumentation side effect、replay incomplete、read-map mismatch 或 validity guard failure，并停止因果解释。

R1-01 不实现通用 hook registry、middleware、snapshot framework、matched carrier、full restoration、自然案例、live model、训练、统计 power/p-value、benchmark claim、novelty claim、release、tag、PyPI 或 CITATION。

R1-02 handoff：将本阶段已验证的 first-handoff state envelope、arm materialization、donor provenance 和 exact replay 输入固化为可重复实验记录；不提前进入 atom census、full controls 或 bounded verdict。
