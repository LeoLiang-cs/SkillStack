# R2 自然案例筛选与增量验证完成记录

## 状态

当前状态：`implementation_complete_live_not_run`。

本轮已实现并验证 R2 的离线测量机制、候选 pre-screen、Structured ReAct boundary contract、v3 first-provider envelope、固定 protocol、FakeClient controls 和 dry-run。没有调用 DeepSeek、没有运行自然 ALFWorld episode，也没有产生 R2 的 outcome-level 增量结论。

## 实际完成

- `src/skillstack/blm.py`：新增 additive v3 schema 常量和 v3 mapping/list read tracking；R1 v1/v2 regression 保持通过。
- `src/skillstack/experiments/blm_natural.py`：实现自然 boundary request validation、top candidate/full handoff group materialization、pre-provider projection hash、candidate screen、natural envelope/replay helpers。
- `src/skillstack/runner.py`：只对 v3 request 接入自然 boundary；`blm_intervention=None` 不增加 sidecar、不改变默认调用。
- `scripts/run_blm_natural.py`：提供 candidate-screen/dry-run/run/resume/summarize；live `run` 需要显式 `R2-LIVE-APPROVED`。
- R2 contract/census、protocol、candidate register、baseline comparison 和本记录已写入版本化文件。

## 本轮实际验证

- 三个 `p0_tasks_picktwo` task 均进入 candidate log；CD pre-screen 具有 ID/native/flat carrier difference，PepperShaker 与 Pillow 为相同 carrier 加 score difference。由于 uv runtime 未安装 optional `alfworld`，三者首次 reset gate 均为 `not_verified`，因此 eligible case 为 0。
- FakeClient v3 capture 的 `flat_skill_context` prompt exposure、`selected_native_skills[0]` host semantic read、skill-id reporting boundary read sequence 可观察；score negative control 不改变首次 provider request projection hash。
- top-candidate group 会同步替换 top ID/score/native，并按照 adapter 规则重新生成 flat context；full group 只能从同一 donor output 复制。
- forbidden outcome content、invalid schema/state/donor 和 unsupported Consumer 在 provider/Consumer 前拒绝。
- R1 focused replay/boundary/census/controls/verdict regression 共 37 项，R2 focused tests 7 项，通过；compileall 与 `git diff --check` 通过。
- dry-run 输出：3 个 task logged、0 eligible、0 planned live episodes、live provider `not run`；无 API key、Authorization 或完整 HTTP headers 进入证据。

## 历史证据与 proposal

- R1-00～R1-05 是 calibration-only evidence，不能升级为自然案例结果。
- Week 3 DeepSeek runs 仅用于帮助冻结候选集合，仍标记 `historical_evidence`。
- R3 是 proposal：只在 R2 通过 live/reset gate 的候选上独立冻结 task、重复、预算、统计和确认规则。

## 尚未验证 / not run

- optional ALFWorld runtime reset、真实首次 state reconstruction 和 provider request replay。
- DeepSeek V4 Flash live response、action trajectory、provider variability、token/latency/cost 和 environment oracle outcome。
- matched-carrier、no-skill、full-handoff 与 coherent top-group 的自然 outcome 对比。
- R2 `candidate_signal_ready_for_r3`、`complete_bounded_negative` 或 control-confound 状态。
- credential scan、commit/push 后 hosted CI 的最终本轮结果（在提交前质量门禁执行）。

## 排除的 claim

本轮不声称 BLM 已实现有效、已被支持或证伪；不声称发现模型内部读取、普遍隐藏依赖、ALFWorld benchmark 性能、部署无辅助 retriever、novelty、p-value、power 或论文结论。prompt exposure 只写作 host-side exposure，不写作模型内部读取。

## R3 handoff

在 optional ALFWorld runtime 可用且 Leo 审核 dry-run 之后，唯一下一步是单独启动 R2 live pilot；R3 只能接收通过 R2 hard gate 的候选并做独立确认。不得自动进入 R3 或论文结论。
