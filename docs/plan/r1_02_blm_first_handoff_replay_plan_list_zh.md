# R1-02 BLM 首次 handoff envelope 与 exact replay 清单

- 状态：`VERIFIED`
- 执行 SHA：`5cd55912aa14acefe6ec07f60ea9da989fed183e`
- 研究边界：`Retriever → adapt_retrieval_for_execution → SkillPlanExecutor`
- 状态范围：`first_handoff_reconstructed_fixture_v1`
- 依赖：[R1-00 replay state spec](../research/blm/r1_00_replay_state_spec.md)、R1-01 boundary hook

## 目标与排除

本阶段只把 reference、crossed、crossed-noop 的首次 handoff 冻结为完整 envelope，并证明同一 envelope 可以重新构造相同的 Producer、adapter、Consumer 初始状态和结果。只运行确定性 heat fixture；不进入 atom census、matched carrier、full restoration、自然案例、live model 或中途 snapshot。

## 执行清单

### R1-02-00 基线与状态修正

- [x] 记录 SHA、branch、upstream、dirty、Python、平台、日期。
- [x] 将 master plan 状态改为 `R1-01 complete; R1-02 active`。
- [x] 冻结本阶段只处理三个 envelope arm。

### R1-02-01 Envelope v1

- [x] 保存 task、Producer config/output、adapter output/event、fixture 初始状态、Consumer registry、预算、seed、oracle、intervention request 和完整 hash。
- [x] canonical hash 排除生成时间但不排除影响首次 handoff 的状态。
- [x] 记录代码模块 digest、fixture digest、library digest，并在 replay 前校验。

### R1-02-02 materializer/replayer

- [x] 在 `src/skillstack/experiments/blm_calibration.py` 实现 `materialize_first_handoff_envelope`。
- [x] 实现 `replay_first_handoff_envelope`；所有 exact identity 检查通过后才调用 Consumer。
- [x] 漂移或状态不完整 fail-closed 为 `abstained: replay_state_incomplete`。
- [x] 提供 `scripts/run_blm_calibration.py materialize-replay` 窄用途入口。

### R1-02-03 固定输入与 replay gate

- [x] 生成 `configs/blm/r1_02_first_handoff_envelopes.json`。
- [x] 三个 arm 各重建三次；比较 Producer/adapter/boundary hash、输入、观察、动作、奖励、branch、plan、stop reason 和 oracle outcome。

### R1-02-04 失败与恢复测试

- [x] 新增 `tests/test_blm_r1_02_replay.py`，覆盖 key order、JSON round trip、task/state/registry/fixture/budget/output drift、缺失状态、no-op 和 default-off regression。
- [x] 明确只支持首次 handoff，不支持通用中途 snapshot。

### R1-02-05 证据与出口

- [x] 生成 replay evidence、completion record 和 local gate JSON。
- [x] 未执行项目写 `not run`，不得推断为通过。

## Exit Gate

| Gate | 验收 |
|---|---|
| R1-02-A | 三个 envelope 完整、hash 可重算 |
| R1-02-B | 每个 arm 3× exact |
| R1-02-C | no-op 与 crossed exact |
| R1-02-D | 任意状态/代码/fixture 漂移在 Consumer 前停止 |
| R1-02-E | 不宣称 mid-episode snapshot |
| R1-02-F | local gate、credential scan、push、hosted CI 有实际记录 |

失败状态：`blocked_replay_state_incomplete`；触发时 R1-03～R1-05 为 `not run`。
