# R1-05 completion record：bounded verdict calibration 与 R1 exit audit

- 阶段状态：`complete_calibration_only`
- evidence class：`verified_this_run`、`calibration_only`
- boundary：`r1_00_c1_skillplan`
- raw run：[`r1_05_calibration_run/`](r1_05_calibration_run/)

R1-05 已实现 `evaluate_calibration_case(case_record)` 和可恢复的确定性 calibration runner。raw JSONL 只追加 episode；summary 从 raw 重新计数，verdicts 从固定 case record 重算。`measurement_status` 与 `contract_verdict` 分开保存；invalid/abstained 永不生成 falsified；没有显式有限 claim 时只能 abstain。

## 预定义案例实际判断

| case | measurement | bounded verdict | reason |
|---|---|---|---|
| known identity dependency | valid | not_falsified | local identity dependency calibration |
| 三个 unread probes | valid | not_falsified | current Consumer/read domain |
| declared field deleted | invalid | abstained | `adapter_transport_nonconformance` |
| opaque native/flat | valid | abstained | `consumer_semantic_read_unverified` |
| synthetic joint-only | valid | falsified | 只针对 test-only synthetic independent-sufficiency claim |
| invalid donor/type/group | invalid | abstained | measurement invalid |
| replay state drift | abstained | abstained | `replay_state_incomplete` |
| no-op drift | invalid | abstained | `no_op_changed_result` |
| interrupted arm | abstained | abstained | `incomplete_arm` |
| budget exhausted | abstained | abstained | `budget_exhausted` |

raw 运行包含 9 个 execution arms × 3 次 = 27 条 JSONL episode；resume 后 episode 数仍为 27，无重复。完整 core gate 为 177 tests、1 个 allowlisted skip、0 failure/error。summary、verdicts 与 atom census 均可从 raw/config 重算。固定案例配置见 [`r1_05_verdict_calibration.yaml`](../../configs/blm/r1_05_verdict_calibration.yaml)。

## R1 总 exit audit

| Gate | 状态 | 证据 |
|---|---|---|
| R1-02 envelope/replay | verified | R1-02 completion/evidence |
| R1-03 census 与实际 read 一致 | verified | R1-03 completion/evidence |
| R1-04 arms、carrier、full restoration、rejection | verified | R1-04 completion/evidence |
| R1-05 案例得到预期判断 | verified | `r1_05_calibration_run/verdicts.json` |
| raw → summary → verdict 可重算 | verified | run summary 与 verdict tests |
| full local/preflight/repo/compile/build/diff/credential gate | verified | [`r1_05_core_gate_local.json`](r1_05_core_gate_local.json) |
| push + hosted CI 全矩阵 | verified | GitHub Actions run `35169959655` 四矩阵通过 |
| claim boundary 保持 calibration-only | verified | 本报告与 verdict schema |

## 研究边界与下一步

已实现：first-handoff replay、read tracking、固定 restoration/control 和 bounded verdict machinery。本轮实际验证：零模型、零网络、零外部数据的 deterministic suite。历史证据：R1-00/R1-01。calibration-only evidence：SkillPlan 手写 dependency 与 test-only synthetic case。proposal：自然案例、正式模型/benchmark 和后续基线。尚未验证：自然 Consumer、live model、ALFWorld benchmark、跨环境 donor、中途 snapshot replay。排除 claim：BLM 已有效、具有 novelty、普遍发现隐藏依赖或接口已认证。

R2 的唯一下一步是筛选真实自然 D→C 案例和简单基线；不自动进入 live model、R3 正式实验或论文结论。
