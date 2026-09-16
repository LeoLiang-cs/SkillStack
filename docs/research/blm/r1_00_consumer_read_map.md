# R1-00 Consumer read-site map

基线：`67957b9b0630bbe80fde76ca9ca10a7834fad57a`。行号基于该源码基线；R1-00 新增测试不改变下列 production files。

## SkillPlanExecutor（primary）

| 输入 | 文件 / 函数 / 精确表达式 | read 类型 | 控制流或行为 | trace | 静态证明 / 动态需求 |
|---|---|---|---|---|---|
| all four fields | `execution/skillplan.py:_validate_execution_input`, `field not in execution_input` | schema validation | 缺字段抛错；值不参与决策 | exception 被 runner 记为 warning | 静态已证；type/value rejection 仍需 R1-01 动态 validator |
| `selected_skill_ids` | `SkillPlanExecutor.execute`, `skill_ids = execution_input["selected_skill_ids"]`; `top_skill_id = skill_ids[0] if skill_ids else None` | semantic read | 选择 reference/local/generic plan branch | `plan_skill_id`, `plan_steps`, rationales | 静态与本轮动态 outcome sensitivity 均已证 |
| `selected_scores` | 无其他表达式 | unread after validation | 无 | retrieval response 可见，但无 Consumer effect | 静态已证；R1-01 no-op negative probe |
| `selected_native_skills` | 无其他表达式 | unread after validation | 无 | Runner 保存 native payload | 静态已证；R1-01 no-op negative probe |
| `flat_skill_context` | 无其他表达式 | unread after validation | 无 | 当前 trace 不保存 flat context | 静态已证；R1-01 no-op negative probe |
| task record + initial observation | `parse_task_semantics(task_record, initial_observation)` | semantic environment read | 绑定 object/destination/appliance | `task_binding` | 静态已证；不是 D→C payload |
| initial/current info | `current_info.get("admissible_commands", [])` | semantic environment read | 限制 `_choose_action` 可选动作 | actions/observations 间接可见 | 静态已证；不是 D→C payload |
| executor-local registry | `PLAN_STEPS_BY_SKILL[top_skill_id]`; `APPLIANCE_BY_SKILL.get(...)`; `TRANSFORM_VERB_BY_SKILL.get(...)` | semantic local read | 决定 plan、appliance、verb | plan/rationale 可见 | 静态已证；必须纳入 replay envelope |

## ReActExecutor(FakeClient)（deferred exposure/control）

| 输入 | 文件 / 函数 / 精确表达式 | read 类型 | 控制流或行为 | trace | 静态证明 / 动态需求 |
|---|---|---|---|---|---|
| `flat_skill_context` | `execution/react.py:execute`, `execution_input.get("flat_skill_context")`; `.replace("{skill_context}", skill_context)` | prompt exposure | 改变 system prompt carrier | `system_prompt` | exposure 静态已证；模型内部依赖不可由 FakeClient 证明 |
| `selected_native_skills` | `extract_procedure_steps`, `execution_input.get("selected_native_skills") or []`; `native_payloads[0]` | semantic parser read + prompt exposure | structured 模式解析 Procedure，追加 steps prompt，并用于 grounding | `grounded_steps`, `system_prompt`, rationale | parser 静态/测试已证；不等于 LLM semantic read |
| `selected_skill_ids` | rationale expression `execution_input.get(...)[0]` | trace attribution | 不选择 action，仅标注 rationale | action rationale | 静态已证 |
| `selected_scores` | 无表达式 | unread | 无 | 无 | 静态已证 |
| task record | `task_record['task_instruction']` | prompt exposure | 进入 system prompt | `system_prompt` | 不是 D→C payload |
| initial observation/info | `_observation_message(initial_observation, current_info)`；`current_info.get("admissible_commands", [])` | prompt exposure + action validation | 进入 user message并约束 action | observations/actions；完整 messages 未保存 | 曝光静态已证；FakeClient 收到 messages 可动态记录 |

## RecordedActionExecutor（negative control）

| 输入 | 文件 / 函数 / 精确表达式 | read 类型 | 控制流或行为 | trace | 静态证明 / 动态需求 |
|---|---|---|---|---|---|
| all four fields | `execution/recorded.py:_validate_execution_input`, `field not in execution_input` | schema validation only | 只拒绝缺字段 | runner exception | 静态已证；不需要 semantic instrumentation |
| task record | 无 | unread | 无 | task 在 runner trace，但非 Consumer read | 静态已证 |
| initial observation | `observations = [initial_observation]` | trace initialization | 不决定动作 | observations | 静态已证 |
| admissible commands | `current_info.get("admissible_commands", [])`; `action not in admissible_commands` | semantic environment read | 接受/拒绝 supplied action | actions/stop reason | 静态已证 |
| recorded actions | `list(recorded_actions or [])`; loop | external action source | 直接决定动作序列 | actions | 静态已证；不是 D→C payload |

## R1-01 instrumentation boundary

静态审计已经足以分类当前 read sites，但不能证明运行时每次读取顺序、值来源和 intervention validity。R1-01 只需在 adapter 返回之后、`executor.execute` 之前增加 opt-in side-car hook，记录原始 execution input、允许的 pre-read intervention 与 validity；默认关闭时 trace 必须 byte-equivalent（时间戳除外）。不修改 Consumer 让其读取新字段。
