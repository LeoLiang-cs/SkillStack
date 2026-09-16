# R1-00 boundary contract v1

状态：`frozen_for_calibration`；不是通用 Canonical Interface，也不是充分性证书。

## Contract C1：Retriever → adapter → SkillPlanExecutor

### 1. Declared semantics

- Retriever response 必须包含 `retriever_name`、`ranked_candidates`、`raw_output`、`warnings`；每个 candidate 必须含 `skill_id`、`score`、`native_payload`。
- adapter 声明保留 candidate 顺序，并生成 `selected_skill_ids`、`selected_scores`、`selected_native_skills`、`flat_skill_context`。
- `SkillPlanExecutor` 的源码说明明确：plan skeleton 由 selected skill ID 对应的手写 registry 决定；object/destination/appliance 由 task/environment text 与 executor-local mappings 绑定。
- 任务域只限当前手写的 ALFWorld-style deterministic calibration fixture；不主张任意 Skill、任意环境或自然组件交换。

### 2. Transport availability

四个 adapter 字段全部到达 Consumer。完整 native payload 同时存在于 `selected_native_skills` 与 `flat_skill_context`；因此“没有独立 schema field”不等于 transport omission。task record、initial observation/info、budget 和 local registry 通过 runner/Consumer 参数或进程代码到达，但它们不是 D→C Producer payload。

### 3. Observed access/exposure

| 信息 | C1 observed status | 解释 |
|---|---|---|
| `selected_skill_ids` | `semantic_read` | `[0]` 决定 plan registry branch，并进入 rationale/trace |
| `selected_scores` | `schema_validation_read` only | 只检查 key 存在；不影响 plan/action |
| `selected_native_skills` | `schema_validation_read` only | payload 已传输但 C1 不解析 |
| `flat_skill_context` | `schema_validation_read` only | 已生成但 C1 不使用 |
| `PLAN_STEPS_BY_SKILL` / appliance mappings | `semantic_read`, Consumer-local | 手写已知机制，只可用于 calibration |
| task / observation / admissible commands | `semantic_read`, environment context | 影响绑定与动作，但不是 D→C atom |

### 4. Outcome effect

primary outcome 为 fixture environment oracle（`done` 且 reward > 0）。同时保存 action trace、plan branch、stop reason、warnings 与 validity reason。本轮确认 selected identity 的不同 Producer 输出能够改变 plan/action/outcome，但尚未运行 single-atom restoration arms。

### 充分性主张

C1 **没有**声明“这四个字段对所有任务充分”。R1 calibration 只可检验以下预注册局部主张：在固定 heat fixture、固定 Consumer/local registry、固定初始状态与预算下，reference skill identity 应触发 heat plan，而无 skill identity 不应完成 heat oracle。没有更强的明确主张时，后续不得产生一般性的 `falsified` verdict。

## Contract C2：Retriever → adapter → ReActExecutor(FakeClient)

- Declared：`flat_skill_context` 被模板替换进 system prompt；structured 模式从 top native payload 解析 numbered Procedure。
- Transport：四字段均可到达；该 executor 没有统一的四字段存在性 validator。
- Observed：flat context 是 `prompt_exposure`；native payload 在 structured 模式是 `semantic_parser_read + prompt_exposure`；selected ID 只用于 rationale attribution；score 未读取。
- Outcome：FakeClient 固定回复决定动作，故 prompt 变化没有自然 response sensitivity；只能校准 prompt carrier 与 parser/grounding，不能声称模型内部读取。
- Verdict：`deferred`，且不得用 FakeClient 结果生成模型依赖或契约充分性 verdict。

## Contract C3：Retriever → adapter → RecordedActionExecutor

- Declared/transport：四字段存在并通过 shape validation。
- Observed：四字段均为 `schema_validation_read`，没有 Skill semantic read；task record 未读取。
- Outcome：由外部 supplied actions、admissible commands 与 environment 决定。
- Verdict：仅作为 `unread_information_negative_control`；不能对 Skill atom 生成 semantic effect claim。

## 状态词典

- `field_present`：对象中存在字段，尚不能证明 Consumer 访问。
- `schema_validation_read`：只检查 key/shape/type，不影响语义决策。
- `semantic_read`：值进入可定位的控制流、解析或行为选择。
- `prompt_exposure`：值进入 prompt；不等于模型内部读取、理解或依赖。
- `unread`：静态调用路径没有发现读取；动态 instrumentation 可继续验证，但不得反向推断已读取。
