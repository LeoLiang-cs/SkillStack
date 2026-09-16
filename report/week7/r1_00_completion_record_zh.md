# R1-00 completion record：BLM 测量可行性与实验协议审计

## Material Passport

- Origin Skill: `ars-codex:academic-research-suite / experiment-agent`
- Origin Mode: validate / reproducibility audit
- Audit Date: 2026-09-16
- Baseline Commit: `67957b9b0630bbe80fde76ca9ca10a7834fad57a`
- Execution Evidence Commit: `5939faf140511aefc5055dc2b457760ac6560447`
- Verification Status: VERIFIED — R1-00 exit gate 完成；不表示 BLM 已实现、有效或具有 novelty。
- Measurement Status: `boundary_feasible_for_deterministic_calibration`

## 结论先行

当前 repository 存在一个可合法进入 BLM calibration 实现的 D→C boundary：

`OracleSkillRetriever / deterministic Retriever → retrieval_to_execution adapter → SkillPlanExecutor → deterministic environment oracle`

它通过了 read site、首次 handoff exact replay、calibration donor、outcome sensitivity、protocol/control freeze 与 claim-boundary 硬门禁。primary 机制是 Consumer 对 `selected_skill_ids[0]` 的真实语义读取；这是手写已知 dependency，只能校准测量工具，不能当自然案例。

negative control 选择 `Retriever → adapter → RecordedActionExecutor`：四个 Skill 字段只做存在性 validation，行为由 recorded actions 与 environment 决定，适合验证 unread information 不应产生 semantic effect。

## 实际验证结果

| 检查 | 本轮结果 | 证据等级 |
|---|---|---|
| primary read site | `selected_skill_ids[0]` 选择 local plan registry | implemented + 本轮源码验证 |
| native transport | 完整 payload 同时进入 native list 与 flat context | implemented + 本轮源码验证 |
| 3× reconstruction | comparison surface exact match | 本轮动态验证 |
| no-op control | 与未插桩 baseline exact match | 本轮动态验证 |
| outcome sensitivity | Oracle success；NoSkill failure；actions 分叉 | calibration-only evidence |
| ReAct/FakeClient | prompt exposure 与 structured parser 可见；模型内部依赖未验证 | implemented；内部读取 not verified |
| RecordedAction | Skill values 未被语义读取 | implemented + negative-control selection |
| GRASP/SkillRL/SkillOps | 真实调用链属于 A→L，未混入 D→C | 本轮源码审计；历史运行未重跑 |

## Boundary selection record

| 候选 | read | replay | donor | outcome | controls | 决定 |
|---|---|---|---|---|---|---|
| SkillPlanExecutor C1 | pass | pass (3× + no-op) | pass for calibration oracle/static artifact | pass in deterministic fixture | frozen | **primary** |
| ReActExecutor(FakeClient) C2 | exposure/parser pass；internal read unknown | fixture only | possible | scripted reply confound | frozen | deferred exposure/control |
| RecordedActionExecutor C3 | semantic read fail by design | pass | not applicable | Skill-insensitive | negative control | **negative control** |
| GRASP/SkillRL/SkillOps C4–C6 | wrong responsibility boundary | not applicable | external provenance exists | A→L outcomes | not D→C | rejected from R1 first boundary |

## R0-A～R0-I exit audit

| Gate | 状态 | 证据 |
|---|---|---|
| R0-A Baseline | verified | SHA/branch/worktree/Python/platform/scope/evidence labels recorded |
| R0-B Candidate register | verified | C1–C6 actual paths classified；A→L excluded with reasons |
| R0-C Contract | verified | declared/transport/read/outcome separated；sufficiency claim bounded |
| R0-D Read map | verified | machine-readable records distinguish validation/semantic/exposure/unread |
| R0-E Replay | verified | 3× exact reconstruction；no-op exact match |
| R0-F Atom/donor | verified | identity/group/opaque/unread classified；donor rejection rules frozen |
| R0-G Arms/outcome | verified | six core arms + invalid/negative controls + oracle/validity frozen |
| R0-H Claim boundary | verified | calibration/natural/benchmark/novelty boundaries explicit |
| R0-I Handoff | verified | primary、negative control、deferred/rejected 与 R1-01 scope recorded |

R1-00 status：`complete`。`blocked_boundary_redesign` 未触发；没有两个同等可行但回答不同论文问题的 primary 候选，因此不需要人工分叉决策。

## R1-01 精确 handoff

目标：在不改变 Consumer semantics 的前提下，把 C1 的 first-handoff capture、pre-read intervention validation 与 validity record 做成 opt-in、可测试的最小路径；只覆盖 `selected_skill_ids[0]` 和 unread negative probes，不执行完整 R1-02～R1-05。

代码改动面：

1. 新增单一最小模块 `src/skillstack/blm.py`：定义 boundary record、allowed atom、donor/type/state validation 与 no-op/capture helper；不建通用 framework。
2. `src/skillstack/runner.py`：在 adapter return 后、`executor.execute` 前加入默认关闭的 optional boundary hook；关闭时现有 trace/behavior 不变。
3. opt-in trace 仅增加 versioned `blm_boundary` side-car，记录 original/effective input hash、read-map ID、arm、validity reason；不把 action/reward/done/success 作为可写字段。
4. `tests/test_blm_r1_01_boundary.py`：复用 R1-00 heat fixture，覆盖 capture/no-op、合法 identity change、invalid type/state/donor rejection、unread score/payload negative probes。

测试入口：

- focused：`uv run python -m unittest -v tests.test_blm_r1_01_boundary`
- regression：`uv run python scripts/run_core_gate.py --summary report/week7/r1_01_core_gate_local.json`
- repository/credential gates：沿用 `uv run skillstack preflight`、`uv run skillstack check-repo` 与 credential scan。

验收条件：default-off 与当前 behavior exact；3× envelope exact；no-op exact；intervention 在 Consumer read 前生效；invalid donor/type/state 在 Consumer 前拒绝；unread changes 不产生 semantic effect；trace 含 branch/validity/outcome 但 intervention API 无 outcome setters；所有 core/CI gates 通过。

## 明确排除的 claim

- BLM 已实现或已经有效；
- 当前 boundary 发现了自然隐藏依赖；
- deterministic fixture 是 ALFWorld benchmark；
- prompt exposure 等于模型内部读取；
- native payload 缺少独立字段等于 adapter 丢失信息；
- Oracle retriever 是自然案例 evidence；
- GRASP/SkillRL/SkillOps A→L 路径属于首轮 D→C；
- 本轮提供 novelty、统计 power、p-value 或通用契约完整性结论。

## 未运行

live provider、训练、大规模模型调用、自然案例、正式 ALFWorld experiment、通用 mid-episode snapshot、R1-02～R1-05：`not run`。

## 本地质量检查

- `uv run skillstack preflight`：pass，Python 3.12.13，0 model/network calls。
- `uv run skillstack check-repo --root .`：pass，419 files，0 findings；包含 credential-like value 与 private-path scanner。
- tracked env-file check：仅 `.env.example`；staged changes 不含 `.env`、credential 或 authorization 文件。
- compileall：pass。
- core gate：143 tests passed，1 个允许的 conditional skip（default manifest 无 pick_two task），0 unexpected skips，0 model/network calls。
