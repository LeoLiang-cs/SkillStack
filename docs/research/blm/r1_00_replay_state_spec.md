# R1-00 first-handoff replay state specification

## Scope

本规范只承诺在第一次 D→C handoff 前重新创建 deterministic fixture。它不承诺通用中途 snapshot、任意 ALFWorld internal state、live provider context 或跨版本 replay。

## Envelope v1

| 类别 | 必须保存或重建 | C1 当前来源 | 完整性规则 |
|---|---|---|---|
| task | 完整 task record，包括 `expected_skill_id` 的 calibration 标记 | `TASK` fixture | hash/值 exact |
| Producer config | class/name、top_k、seed/selection policy、library ordering | Oracle/NoSkill config | exact；Oracle 标记 `calibration_oracle` |
| Producer output | 完整 retrieval response | `retrieve` return | canonical JSON exact |
| adapter output | 四字段与 adapter event | adapter return | canonical JSON exact |
| environment state | fixture class/version、constructor state、transition table version | `HeatCalibrationEnvironment` | 每个 arm 新建实例；不得复用已 step 的实例 |
| initial observation/info | 原始 string 与完整 info dict | environment factory | exact |
| Consumer config | class、`step_budget_per_plan_step`、`max_steps` | `SkillPlanExecutor`, 24, 12 | exact |
| Consumer-local registry | `PLAN_STEPS_BY_SKILL`、generic plan、appliance/verb mappings、源码 commit | imported code at baseline | commit + relevant mapping exact |
| seed | fixture/Producer seed；无随机性时仍记录 `none` | 本 fixture `none` | 不得把未使用 seed 伪写成 determinism proof |
| budget | `top_k=1`, `max_steps=12`, per-step budget 24 | test invocation | exact |
| oracle | environment done/reward rule与 success derivation | fixture + Consumer | 不得直接被 intervention 设置 |

任一必需状态无法保存或重建时，输出 `abstained: replay_state_incomplete`，停止 restoration 因果解释。

## 本轮实际验证

测试入口：`uv run python -m unittest -v tests.test_blm_r1_00_replay`。

- reference envelope 独立创建环境、Producer 与 Consumer 3 次；boundary input、actions、stop reason、success、plan branch exact match。
- 无插桩 baseline 与 no-op adapter observation（deep-copy 记录后原值返回）exact match。
- reference action trace：`go shelf → take mug → go microwave → heat mug → go desk → move mug`；`environment_done`, success `true`。
- NoSkill producer action trace：`go shelf → take mug → go desk → move mug`；`environment_done`, success `false`。

这说明 C1 对实际 Producer output 有 outcome sensitivity；它不等于已执行完整 restoration protocol。

## Exact comparison surface

比较 canonical values：retrieval response、selected IDs、selected native payloads、adapter event、action trace、stop reason、success、plan skill ID、plan steps。排除 wall-clock timestamp；排除它不是放宽行为比较，而是 timestamp 本来就不属于 causal envelope。

## No-op 条件

instrumentation 可以观察并复制 input，但返回给 Consumer 的对象在值和类型上必须不变。baseline 与 no-op 的 comparison surface 任一差异均触发 `measurement_invalid:no_op_changed_result`。

## R1-01 前的边界

当前测试 fixture 是 feasibility evidence。正式 R1-01 必须把 envelope/validity 写入 opt-in trace side-car，并加入 type/state rejection；不得把本测试扩建成通用 snapshot framework。
