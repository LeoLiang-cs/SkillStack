# R1-04 BLM restoration arms 与 controls 清单

- 状态：`PLANNED`（执行期间逐项改为 `VERIFIED`）
- 依赖：R1-02 replay、R1-03 census
- 固定边界：C1 `SkillPlanExecutor`；不修改 Consumer read site

## 目标与排除

本阶段只扩展固定 donor/atom/group 的合法 restoration 和 matched-carrier control。所有干预在 adapter 后、Consumer 前进入，禁止直接设置 action、reward、done、success，禁止混合 donor 和新增解题知识。

## 执行清单

### R1-04-00 intervention v2

- [ ] 保留 request v1 字段，新增 `copy_group_from_donor`。
- [ ] group 只允许 `reference_handoff_group`，成员固定为 identity、score、native payload、flat context。
- [ ] 不开放任意 path、patch 或多 donor。

### R1-04-01 固定 arms

- [ ] 生成 `configs/blm/r1_04_calibration_arms.yaml`。
- [ ] 执行 reference、crossed、crossed-noop、single-atom、matched-carrier、full-reference 和三个 unread probes。
- [ ] 所有 arm 固定 task、Consumer、state、budget、oracle，每个 3 次。

### R1-04-02 donor/group guards

- [ ] Oracle 只接受真实 Oracle output；matched donor 只接受 random seed=3 的 `skill_light_inspection`。
- [ ] 校验 task/family/state、library/payload、score、list 对齐、flat derivation 和 forbidden content。
- [ ] 非法 donor/type/state/group 在 Consumer 前拒绝。

### R1-04-03 control interpretation

- [ ] single atom 恢复 reference branch/outcome，其他 crossed carrier 保持不变。
- [ ] matched carrier 不复制 reference semantics；若与 semantic intervention 完全相同，停止为 `abstained: carrier_confound`。
- [ ] full restoration effective input hash 必须等于 reference；否则记录 group materialization failure。

### R1-04-04 测试与证据

- [ ] 新增 `tests/test_blm_r1_04_controls.py`，覆盖 3× exact、mixed-source/group alignment、forbidden content、pre-consumer rejection 和 v1 compatibility。
- [ ] 生成 restoration evidence、completion record 和 local gate JSON。

## Exit Gate

六个主 arm 和三个 unread probe 可重建；matched carrier 不复制 reference semantics；full restoration 与 reference input exact；single atom 的非目标字段仍为 crossed；所有非法请求在 Consumer 前拒绝；local/credential/push/hosted CI 有实际记录。失败状态按协议写 `blocked_instrumentation_side_effect`、`blocked_control_confound`、`blocked_validity_guard` 或 `blocked_boundary_implementation`。
