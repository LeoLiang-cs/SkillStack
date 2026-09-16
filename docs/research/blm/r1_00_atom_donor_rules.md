# R1-00 atom and donor legality rules

## Atom census（C1 primary）

| 候选信息 | Consumer status | 操作分类 | calibration 用途 |
|---|---|---|---|
| top skill identity/reference (`selected_skill_ids[0]`) | semantic read | **independently intervenable atom**，但必须保持 list shape 与 donor alignment | primary known dependency |
| rank/order | top list position被读取；其余位置在 top-only Consumer 中未读取 | top identity 与 top rank 构成语义 group；不能只改 rank label 而不改 order | group/control |
| score (`selected_scores`) | validation only | unread information | negative control only |
| native payload (`selected_native_skills`) | 已传输，validation only | opaque payload + unread information in C1 | negative control；不能称 transport omission |
| flat context | 已生成，validation only | derived opaque carrier + unread information in C1 | matched-carrier/negative control |
| local registry lookup | semantic read，Consumer-local | 与 identity 共同决定 plan 的 **inseparable mechanism group**；不是 Producer field | 固定 registry 的 calibration mechanism；不得作为 natural D→C atom |
| task/observation/admissible commands | semantic read | environment state，不是 handoff atom | 每个 arm 固定 |

## Donor validity

合法 donor 必须同时满足：

1. 来源固定且可追踪到 commit、library path、artifact hash/ID；
2. task semantics 匹配，且 donor artifact 原生适用于同一 task family；
3. first-handoff environment/Consumer state 与 recipient arm exact match；
4. 不含 action、reward、done、success、oracle answer 或未来 trajectory；
5. 不含研究者临时添加的步骤、提示或额外解题知识；
6. value/type/group relationship 符合 read site contract；identity、payload、flat derived carrier 的联合恢复要么按预注册 group 执行，要么被拒绝；
7. provenance/validity reason 写入 arm record。

`OracleSkillRetriever` 的 `expected_skill_id` 来自 frozen task mapping，只允许标记为 `calibration_oracle`。它可用于已知依赖的 instrument calibration，不能变成 natural-case evidence，也不能证明真实 retriever 会提供同一 donor。

## Rejection taxonomy

- `invalid_donor:untraceable_source`
- `invalid_donor:task_semantics_mismatch`
- `invalid_donor:handoff_state_mismatch`
- `invalid_donor:oracle_answer_or_future_trajectory`
- `invalid_donor:researcher_added_knowledge`
- `invalid_donor:atom_group_misaligned`
- `invalid_type:boundary_schema`
- `invalid_state:replay_envelope`

被拒 donor 不执行 Consumer，不计为 outcome failure，也不能用于 `falsified`/`not_falsified`。
