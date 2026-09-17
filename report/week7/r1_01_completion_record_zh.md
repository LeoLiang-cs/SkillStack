# R1-01 completion record：BLM 首次边界捕获与干预机制

## Material Passport

- Origin Skill: `ars-codex:academic-research-suite / experiment-agent`
- Implementation discipline: `ponytail:ponytail`
- Audit date: 2026-09-16
- Baseline commit: `c31f270827f5c50a6c82562d02323f1ad688fc94`
- Implementation commit: `4e3e4179b98a184faa9333d4d557e7dcf205b44c`
- Execution evidence: [r1_01_boundary_fixture_evidence.json](r1_01_boundary_fixture_evidence.json)
- Local gate evidence: [r1_01_core_gate_local.json](r1_01_core_gate_local.json)
- Plan: [r1_01_blm_boundary_instrumentation_plan_list_zh.md](../../docs/plan/r1_01_blm_boundary_instrumentation_plan_list_zh.md)
- Verification status: `IN_PROGRESS` until hosted CI completes
- Measurement status: `boundary_instrumentation_verified_calibration_only`

## 结论先行

R1-01 已在 R1-00 冻结的 C1 路径上实现一个默认关闭的 first-handoff boundary hook：

`Retriever → adapt_retrieval_for_execution → SkillPlanExecutor`

本轮实际验证了：adapter 返回后、Consumer 首次读取前的 input capture；只从真实 donor adapter output 复制一个 atom；`selected_skill_ids[0]` 的已知语义读取；三个 unread-field negative probes；donor/task/state/type/source rejection；以及 default-off/no-op exact behavior。

本轮没有产生 BLM `supported`、`falsified` 或 `not_falsified` verdict。identity restoration 只重现 SkillPlanExecutor 手写 skill-id→plan dependency，证据等级为 `calibration_only`，不是自然案例、ALFWorld benchmark 或 novelty evidence。

## 已实现的代码面

| 文件 | 实际实现 |
|---|---|
| `src/skillstack/blm.py` | 固定 schema、canonical SHA-256、C1 state identity、arm/atom contract、donor reconstruction、artifact/provenance validation、forbidden outcome-content rejection、sidecar finalization |
| `src/skillstack/runner.py` | keyword-only `blm_intervention=None`；adapter 后/Consumer 前 hook；invalid pre-consumer stop；valid sidecar branch/outcome 回填；default-off compatibility |
| `tests/test_blm_r1_01_boundary.py` | deterministic reference/crossed/no-op/single-atom/unread arms、3× replay、invalid controls、unsupported Consumer、JSONL invalid status |
| `docs/plan/` 与 `report/week7/` | 独立 R1-01 plan、evidence JSON、local gate 和本 completion record |

没有修改 `SkillPlanExecutor` 的读取语义，没有增加通用 intervention framework，没有升级 top-level `skillstack-episode-trace-v1`，也没有引入 live provider、网络、模型或训练依赖。

## 实际验证结果

| 检查 | 结果 | 证据等级 |
|---|---|---|
| default-off Runner | 与当前 Oracle/Random 行为 exact | `verified_this_run` |
| first-handoff position | `post_adapter_pre_consumer_read` | `implemented + verified_this_run` |
| reference capture | heat branch，environment success；3× projection exact | `verified_this_run` / calibration fixture |
| crossed capture | `skill_cool_then_place` branch，`plan_step_unavailable`，failure | `verified_this_run` / calibration fixture |
| crossed-noop | `changed=false`，与 crossed action/branch/outcome exact | `verified_this_run` |
| crossed+identity | 只复制 `selected_skill_ids[0]` 后恢复 heat branch/outcome | `calibration_only` |
| unread score | 与 crossed branch/action/outcome exact | `verified_this_run` / negative control |
| unread native payload | 与 crossed branch/action/outcome exact | `verified_this_run` / negative control |
| unread flat context | 与 crossed branch/action/outcome exact | `verified_this_run` / negative control |
| invalid donor/task/state/type/source | Consumer 调用次数为 0，`stop_reason=invalid_input` | `verified_this_run` |
| JSONL invalid status | `measurement_status=invalid`，`task_success=null` | `verified_this_run` |
| model/network | 0 / 0 | `verified_this_run` |
| zero-model demo | existing packaged demo fingerprint unchanged | `verified_this_run` |
| package acceptance | isolated Python 3.12 wheel/sdist install, CLI and demo pass | `verified_this_run` |

## R1-01 exit audit

| Gate | 状态 | 证据 |
|---|---|---|
| R1-01-A default-off compatibility | `verified` | focused tests + full core gate |
| R1-01-B hook placement | `verified` | Runner call order与 sidecar `intervention_position` |
| R1-01-C reference/crossed/no-op replay | `verified` | reference 3× hash exact；crossed capture/no-op exact |
| R1-01-D identity atom | `verified` | crossed single-atom restoration；其余 crossed payload 保持 |
| R1-01-E unread negative probes | `verified` | score/native/flat 三 probe exact behavior match |
| R1-01-F invalid guards | `verified` | task/family/state/payload/score/schema/forbidden/list/Consumer cases |
| R1-01-G invalid trace status | `verified` | JSONL writer regression |
| R1-01-H sidecar/provenance | `verified` | schema、state/input hashes、read-map、arm、branch、reason、donor provenance |
| R1-01-I local quality/credential/build | `verified` | 153 tests、preflight、check-repo、compileall、`uv build`、isolated wheel/sdist acceptance |
| R1-01-J claim boundary | `verified` | 本报告和 evidence 明确 calibration-only 与 excluded claims |
| R1-01-K hosted CI | `not run` | push 后等待 hosted CI |

在 hosted CI 完成前，R1-01 的总体状态保持 `in_progress`，不能写成最终 `complete`。

## Evidence classification

### 本轮已实现

- opt-in C1 first-handoff capture/intervention API；
- canonical state/input hashes；
-真实 adapter donor reconstruction 和 native artifact provenance；
- `selected_skill_ids[0]` 单 atom intervention；
- unread score/native/flat negative probes；
- pre-consumer invalid rejection 和 JSONL invalid status；
- sidecar 中的 read-map、branch、validity 和 output-only outcome observation。

### 本轮实际验证

- 同一 deterministic heat fixture 的 reference 3× exact replay；
- crossed 与 crossed-noop exact；
- identity restoration 复现 Consumer branch/outcome；
- unread probes 不改变 Consumer behavior；
- invalid 请求不调用 Consumer；
- default-off 没有改变已有 R1-00 replay 行为；
- local core、preflight、public/credential scan、compile、package build。

### 历史证据

- R1-00 的 candidate register、四层 contract、read-site map、replay spec、donor rules 和 frozen protocol；
- R1-00 的 primary/negative-control selection。

### Calibration-only evidence

- Oracle donor 提供的 heat identity restoration；
- `SkillPlanExecutor` 的手写 skill-id→plan registry effect；
- heat fixture 的 success/failure 分叉。

### Proposal / 尚未验证

- R1-02 first-handoff envelope 的正式实验 materialization；
- 更完整的 atom census、matched carrier、full restoration 和 bounded verdict calibration；
- ReAct/FakeClient 的模型内部依赖；
- 跨环境、自然任务、ALFWorld benchmark、正式模型实验；
- 通用 mid-episode snapshot replay；
- 任何 `supported` / `falsified` / `not_falsified` 或 novelty claim。

### 被排除的 claim

- “BLM 已实现/有效”；
- “deterministic fixture success 是 benchmark evidence”；
- “prompt exposure 等于模型内部读取”；
- “native payload 没有独立字段等于 transport omission”；
- “Oracle retriever 是自然案例”；
- “GRASP、SkillRL、SkillOps A→L 路径是首轮 D→C”；
- p-value、power、general causal completeness 或 paper novelty。

## 停止条件审计

本轮没有触发以下停止条件：

- default-off/no-op instrumentation side effect；
- first-handoff replay drift；
- unread probe 改变 branch/outcome；
- invalid donor/type/state 未被拒绝；
- identity restoration 需要更换 Consumer 或直接设置 action/outcome。

这些条件仍是后续正式 measurement 的 fail-closed guards；本轮不将“未触发”扩展为自然案例排除证据。

## R1-02 精确 handoff

R1-02 只做一件事：把 R1-01 已验证的首次 handoff 状态、Producer output、adapter output、Consumer config/local registry、预算、seed 和 oracle 固化成可重建的 envelope，并在 reference/crossed/no-op 上重复 exact replay；任一隐藏状态无法捕获时输出 `abstained: replay_state_incomplete`。

R1-02 代码范围只涉及 envelope serialization/reconstruction、可恢复 deterministic fixture 入口和对应 replay tests；验收为相同 envelope 的 boundary input、action trace、branch、stop reason 和 oracle outcome exact match。R1-02 不提前实现 atom census、matched carrier、full restoration、natural cases 或 bounded verdict。
