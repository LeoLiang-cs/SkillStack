# R1-00 threat register and stop conditions

| ID | 威胁/反驳 | 检测信号 | 强制处置 |
|---|---|---|---|
| T01 | `SkillPlanExecutor` 的 skill-id→plan dependency 是手写已知 fault | effect 只复现 registry 设计 | 仅称 calibration-only evidence；不得称 natural discovery |
| T02 | native payload 已完整传输，却被误写成 transport omission | adapter output 含完整 payload/context | 改判为 Consumer representation/read 问题或 unread control |
| T03 | deterministic fixture success 被推广为 ALFWorld benchmark | claim 引用 fixture success 作 benchmark 指标 | 排除 claim；fixture 只验证工具链 |
| T04 | matched carrier 与 semantic intervention 效果相同 | outcome/action effect exact same | `abstained:carrier_confound`; 停止语义归因 |
| T05 | no-op 改变结果 | baseline 与 no-op comparison surface 不同 | `measurement_invalid:no_op_changed_result`; 停止因果解释 |
| T06 | donor 泄露答案、动作或未来轨迹 | donor provenance/content audit 命中 | `invalid_donor`; 不执行/不计 outcome |
| T07 | replay 不一致或隐藏 state 未捕获 | 3 次 reference 或 envelope hash 不一致 | `abstained:replay_state_incomplete` |
| T08 | Consumer 不读取 atom | read map 为 validation/unread | 只作 negative control，不制造 semantic restoration |
| T09 | 只有替换 Consumer 才恢复 | 固定 Consumer 所有合法 arms 无效 | 当前 boundary abstain/fail；不得称 BLM success |
| T10 | prompt exposure 被写成模型内部读取 | 只有 system prompt/FakeClient 证据 | 收缩为 exposure/control；live model 需后续单独协议 |
| T11 | task/environment 被误写成 D→C payload | intervention 改 task/observation/admissible commands | arm invalid；这些变量必须固定 |
| T12 | outcome 被直接注入 | intervention 设置 action/reward/done/success | measurement invalid，立即停止 |
| T13 | 没有明确充分性主张却生成 `falsified` | contract claim field 为空/一般化 | verdict 必须 abstain 或 calibration result，不许 falsified |
| T14 | Oracle donor 被当成自然证据 | provenance 为 frozen expected mapping | 标记 calibration oracle；排除 natural-case claim |
| T15 | 简单 schema/ablation 已提供相同诊断 | matched baseline 同成本同结论 | 下调 BLM 增量；R2 前不得扩大 novelty claim |

## Measurement validity 优先级

先判断 replay/no-op/donor/type/state，再判断 outcome effect，最后才判断 contract verdict。任一 measurement-invalid 条件都覆盖成功 outcome；不得用任务成功掩盖无效测量。

## 当前结论

本轮 T05/T07 在 deterministic feasibility fixture 中未触发；其余大部分是冻结的未来停止条件，尚未通过完整 arms 验证。`not triggered in R1-00` 不等于在自然案例中已排除。
