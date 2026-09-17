# R1-03 completion record：boundary-atom census

- 阶段状态：`complete`
- evidence class：`verified_this_run`、`calibration_only`
- baseline / implementation：见 R1-02 completion record
- boundary：`r1_00_c1_skillplan`
- Consumer：`skill_plan_executor`

R1-03 已在 v2 opt-in sidecar 中加入轻量 read tracker。输入 hash 在包装前计算；wrapper 只记录 membership、field getitem 和 list index，并在 Runner 序列化 top-level trace 前冻结 Consumer-only event stream。v1 sidecar 和 default-off 调用保持不变。

## 实际 census

- 四个 execution-input 字段均发生 schema validation membership read。
- `selected_skill_ids[0]` 发生唯一的 semantic index read；top-k=2 仍只记录 index 0，空 list 不伪造 index。
- `selected_scores[0]`、`selected_native_skills[0]` 和 `flat_skill_context` 只有 validation evidence，作为 unread negative controls。
- `PLAN_STEPS_BY_SKILL` 是 Consumer-local hard-coded mapping，记录为 `static_verified_runtime_indirect`，不是 Producer atom。
- task、initial observation 和 admissible commands 是 environment state，不是 D→C payload。

完整记录见 [`r1_03_boundary_atom_census.md`](../../docs/research/blm/r1_03_boundary_atom_census.md)、[`r1_03_atom_census.json`](../../configs/blm/r1_03_atom_census.json) 和 [`r1_03_atom_census_evidence.json`](r1_03_atom_census_evidence.json)。

## Exit audit

| Gate | 状态 | 证据 |
|---|---|---|
| 每个 candidate 可追溯到真实 read 或不可观察边界 | verified | census records + exact static expressions |
| no-op read instrumentation exact | verified | wrapper/default-off behavior projection |
| unread probes 与 census 一致 | verified | 三个 v2 probe 与 crossed exact |
| 未增加 Consumer read | verified | 仅包裹 input；无 Consumer source 改动 |
| local/credential/push/hosted CI | verified | [`r1_03_core_gate_local.json`](r1_03_core_gate_local.json)；hosted CI 在 R1 总出口统一记录 |

动态 tracker 不能证明模型内部读取；若静态 map 与 runtime event 冲突，必须进入 `blocked_atom_census_mismatch`，不得增加人工 Consumer read。
