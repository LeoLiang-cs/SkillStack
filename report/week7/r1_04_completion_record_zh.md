# R1-04 completion record：restoration arms 与 controls

- 阶段状态：`complete`
- evidence class：`verified_this_run`、`calibration_only`
- boundary：`r1_00_c1_skillplan`
- fixture：`r1_00_heat_calibration`

R1-04 已在 v2 request 中开放唯一预注册的 `copy_group_from_donor` / `reference_handoff_group`。没有开放任意 path、patch 或多 donor；所有 donor 都由真实 retrieval response 重新通过 adapter 生成并校验 task/family/state、native artifact、payload、score、list alignment 和 forbidden content。

## 实际 arms

| arm | 实际结果 |
|---|---|
| reference | heat branch，environment success |
| crossed | cool branch，plan unavailable，oracle failure |
| crossed-noop | 与 crossed exact，`changed=false` |
| crossed+single-atom | 仅 identity 从 Oracle 恢复；heat branch/success；其余 crossed carriers 保持 |
| matched-carrier | seed=3 `skill_light_inspection`；非 reference branch、非 oracle success |
| crossed+full-reference | 四字段来自同一 Oracle adapter output；effective input hash 与 reference exact |
| 三个 unread probes | score/native/flat 改变不影响 crossed branch/action/stop/outcome |

每个 arm 均执行 3 次 exact。非法 donor、类型、state、mixed-source/group alignment 和 forbidden trajectory 在 Consumer 前拒绝，且不直接设置 action、reward、done 或 success。

证据见 [`r1_04_restoration_control_evidence.json`](r1_04_restoration_control_evidence.json) 与 [`r1_04_calibration_arms.yaml`](../../configs/blm/r1_04_calibration_arms.yaml)。

## Exit audit

| Gate | 状态 | 证据 |
|---|---|---|
| 六个主 arm + 三个 unread probe 3× exact | verified | focused controls tests/evidence |
| matched carrier 不复制 reference semantics | verified | seed=3 light branch、failure |
| full restoration 与 reference input exact | verified | effective input hash exact |
| single atom 非目标字段保持 crossed | verified | input/adapter/native comparison |
| invalid group/donor pre-Consumer rejection | verified | spy Consumer calls=0 |
| local/credential/push/hosted CI | verified | [`r1_04_core_gate_local.json`](r1_04_core_gate_local.json)；GitHub Actions run `35169959655` 四矩阵通过 |

若未来 matched-carrier 与 semantic restoration 完全相同，应停止语义归因并记录 `abstained: carrier_confound`；本轮未触发。该结果仍只是手写 SkillPlan dependency 的 calibration-only evidence，不是自然案例结论。
