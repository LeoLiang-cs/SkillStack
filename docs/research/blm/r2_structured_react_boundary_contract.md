# R2 Structured ReAct boundary contract

Boundary ID：`r2_c2_structured_react_first_handoff`。

固定路径：

`DebugLexicalRetriever / TaskSemanticRetriever → adapt_retrieval_for_execution → ReActExecutor(structured_skills=True)`

## 四层 contract

| 层 | 本轮可验证内容 | claim boundary |
|---|---|---|
| Declared semantics | top candidate group、full handoff、score negative control | declaration 不是 read evidence |
| Transport availability | adapter 保留 IDs、scores、native payload，并由它生成 `flat_skill_context` | 字段存在不等于 Consumer 消费 |
| Observed host-side read / prompt exposure | `flat_skill_context` 进入 system prompt；native payload 被 `extract_procedure_steps` 解析并进入 numbered steps；skill ID 仅在 action rationale/reporting 读取；score 没有语义读取 | prompt exposure 不是模型内部读取；R2 只记录 host-side request/read |
| Stochastic outcome effect | provider 返回后的 action、stop reason 和 environment oracle | 单次 discovery 不产生 R3 verdict |

## 字段与读取分类

- `selected_native_skills[0]`：`mapping.get` 后由 `extract_procedure_steps` 取 index 0；这是 host semantic read，并且 derived steps 暴露到 prompt。
- `flat_skill_context`：`mapping.get` 后构造 system prompt；这是 prompt exposure。
- `selected_skill_ids[0]`：在已有 action 后用于 rationale/reporting；不能单独写成策略 read。
- `selected_scores[0]`：当前 Structured ReAct host path 不读取；只可作为 unread negative control。
- task、initial observation、admissible commands 是 task/environment state，不是 D→C payload。

## 原子性约束

`top_candidate_group` 由 top ID、score、native payload 和用完整 candidate list 重新生成的 flat context 构成。其内部字段相互派生，不能伪装成四个独立 atom。`full_handoff_group` 只能从同一 donor adapter output 恢复。R2 不开放任意字段路径、自由 replacement 或 mixed donor。

TaskSemantic 是 repository-native、label-assisted reference：它可以读取 `task_family`，但实现与审计均禁止读取 `expected_skill_id`、trajectory、reward、future observation 或人工答案。因此它不是 deployment-unassisted retriever。

## Envelope scope

R2 envelope 保存首次 reset、Producer/adapter output、Consumer prompt/backend/model/config、native library、预算、intervention request 和 pre-provider request projection。只承诺首次 handoff 与首次 provider request projection exact replay；不承诺 live model response、后续 action trajectory 或中途 environment snapshot exact replay。

若 task、reset、代码、library、prompt、backend 或 state hash 漂移，provider 调用前返回：

`measurement_status=abstained`，`reason=replay_state_incomplete`。

证据类别为 `verified_this_run`、`historical_evidence`、`proposal` 或 `not_verified` 时均单独记录；任何 prompt exposure、历史 outcome 或自然发现都不升级为 BLM validity claim。
