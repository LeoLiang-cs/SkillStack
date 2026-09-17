# R1-03 C1 boundary-atom census

状态：`verified_this_run`（确定性 calibration-only evidence）

本 census 只覆盖 R1-00 选定的 `Retriever → adapter → SkillPlanExecutor`。runtime tracker 在 adapter 后包装 execution input，在 Consumer 执行返回前冻结事件；它不会观察模型内部读取，也不会把 Runner 写 trace 的访问误计入 Consumer。

| atom / group | transport | Consumer read | intervention | donor / claim boundary |
|---|---|---|---|---|
| `selected_skill_ids[0]` | adapter 传输 | `_validate_execution_input` membership 后，`execution_input["selected_skill_ids"]` 与 index `0`；semantic | independent atom | Oracle / matched nonreference；仅限 frozen heat fixture 的 branch calibration |
| top rank/order | adapter 传输 | 与 top identity 同一 index read | inseparable group | 不独立归因 rank |
| `selected_scores[0]` | adapter 传输 | membership validation；无 index/semantic read | negative probe | 不称 transport omission |
| `selected_native_skills[0]` | adapter 传输 | membership validation；opaque payload 未被 Consumer 语义读取 | negative probe | native artifact 可追踪，不能称 semantic read |
| `flat_skill_context` | adapter 生成并传输 | membership validation；derived carrier 未被 Consumer 读取 | negative probe | prompt/exposure 不等于模型内部 read |
| Consumer-local registry | 不属于 Producer payload | `PLAN_STEPS_BY_SKILL[top_skill_id]`；runtime wrapper 不直接观测 | environment/local mechanism | 手写已知 calibration mechanism |
| task / observation / admissible commands | environment state | `parse_task_semantics` 与 `current_info` | 不作为 atom | 不得重命名为 D→C payload |

## Runtime sequence

在 reference v2 capture 的三次运行中，事件序列均为：四次 field membership validation、`selected_skill_ids` field getitem、`selected_skill_ids[0]` semantic index。score/native/flat 没有 semantic index；空 identity list 不产生 index 事件。静态映射、实际事件与三个 unread probe 若发生冲突，状态为 `blocked_atom_census_mismatch`，不得通过增加 Consumer read 修复。

完整 schema/源码 digest/runtime records 见 [`r1_03_atom_census.json`](../../../configs/blm/r1_03_atom_census.json)。
