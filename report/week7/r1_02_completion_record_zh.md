# R1-02 completion record：首次 handoff envelope 与 exact replay

- 阶段状态：`complete`
- evidence class：`verified_this_run`、`calibration_only`
- baseline：`b213d48f7623c04b2e08ca683196e63c136e2b36`
- implementation：`2ca2fd73e880d98f2e4716deb63761231977639c`
- verification run：`5cd55912aa14acefe6ec07f60ea9da989fed183e`
- fixture：`r1_00_heat_calibration`
- scope：`first_handoff_reconstructed_fixture_v1`

R1-02 已将 reference、crossed、crossed-noop 的首次 handoff 保存为完整 v1 envelope。每次 replay 会重新构造 fixture、Producer、adapter、Consumer-local registry 和预算，在调用 Consumer 前比较真实 output 与 envelope；代码模块、fixture、library、state 和 envelope digest 漂移时 fail-closed。

## 实际证据

| arm | Producer | replay | branch / outcome | 结论 |
|---|---|---:|---|---|
| reference | OracleSkillRetriever | 3× exact | `skill_heat_then_place` / success | valid calibration input |
| crossed | RandomSkillRetriever(seed=1) | 3× exact | `skill_cool_then_place` / failure | valid crossed baseline |
| crossed-noop | 同一 crossed response | 3× exact | 与 crossed action/stop/outcome exact | no-op 未改变行为 |

实际 envelope 和 hash 见 [`r1_02_replay_envelope_evidence.json`](r1_02_replay_envelope_evidence.json) 与 [`r1_02_first_handoff_envelopes.json`](../../configs/blm/r1_02_first_handoff_envelopes.json)。

## Exit audit

| Gate | 状态 | 证据 |
|---|---|---|
| R1-02-A envelope 完整且 hash 可重算 | verified | 三个 envelope 的整体、state、Producer/adapter hash |
| R1-02-B 每个 arm 3× exact | verified | focused replay tests 与 evidence |
| R1-02-C no-op 与 crossed exact | verified | crossed/no-op projection exact |
| R1-02-D 状态/代码/fixture 漂移 pre-Consumer 停止 | verified | 七类 drift rejection cases |
| R1-02-E 不宣称中途 snapshot | verified | scope 明确为首次 handoff；mid-episode `not supported` |
| R1-02-F local/credential/push/hosted CI | verified | [`r1_02_core_gate_local.json`](r1_02_core_gate_local.json)；hosted CI 在 R1 总出口统一记录 |

## Claim boundary

已实现和验证的是固定 deterministic fixture 的首次 handoff 重建，不是通用 snapshot framework，也不是自然案例、ALFWorld benchmark、模型内部读取或 BLM validity 结论。R1-03 只进入 atom census；没有提前运行自然案例或 live provider。
