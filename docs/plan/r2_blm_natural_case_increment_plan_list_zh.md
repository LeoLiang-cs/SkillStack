# R2：BLM 自然案例筛选与增量验证 Plan List

## Material Passport

- Origin Skill：`ars-codex:academic-research-suite / experiment-agent`
- Implementation discipline：`ponytail:ponytail`
- Plan status：`IMPLEMENTATION_COMPLETE_LIVE_NOT_RUN`
- Starting SHA：`28a02d1008049865efd63ea2001cee3ba41e59c3`
- Starting branch：`main`
- Starting worktree：clean；与 `origin/main` 同步
- 固定边界：`r2_c2_structured_react_first_handoff`
- 本轮约束：zero model、zero network、zero external-data write；live provider 只由 Leo 在 dry-run 审核后启动
- 状态约定：清单创建时所有项目为 `planned`；以下仅将本轮实际完成项改为 `verified`/受限 verified，未执行项保留 `not run`。

## 1. 固定研究边界

R2 只回答：在固定 Structured ReAct Consumer、真实 ALFWorld 初始状态和非 Oracle Producer 输出下，是否存在值得交给 R3 独立确认的自然 D→C carrier difference，以及 BLM 相对 schema check、raw diff、no-skill ablation 和 full-handoff swap 是否有局部诊断增量。

固定路径：

`DebugLexicalRetriever / TaskSemanticRetriever → adapt_retrieval_for_execution → ReActExecutor(structured_skills=True, DeepSeek V4 Flash)`

固定发现集为 `configs/p0_tasks_picktwo.json` 的三个任务，`top_k=2`、`max_steps=20`、temperature 0；TaskSemantic 允许读取 `task_family`，禁止读取 `expected_skill_id`，并明确标记为 label-assisted reference。Oracle 不进入 R2 natural arms。

R2 discovery 不输出论文级 `falsified`，不运行自然案例 provider、ALFWorld benchmark、训练、p-value 或 power。R2 发现必须在 R3 独立任务/重复/预算冻结后确认。

## 2. 执行清单

### R2-00：基线、计划和证据边界 — `verified`

- [x] 记录 SHA、branch、upstream、dirty 状态、Python、平台、日期和 R1 exit evidence。
- [x] 将 master plan 更新为 `R1 complete_calibration_only；R2 active`。
- [x] 保留并区分 R1 calibration、Week 3 historical screening、R2 本轮 pre-screen、R3 proposal。
- [x] 不修改 R1 envelope、census、raw evidence 或 verdict。

### R2-01：自然候选静态筛选 — `verified_with_environment_block`

- [x] 新增 deterministic candidate screener，重新计算三个任务的 lexical/task-semantic producer 与 adapter carrier diff。
- [x] 记录 task、producer config/output、ranked IDs、scores、native payload/flat-context hash、donor/library/code provenance。
- [x] 记录 `task_family` label assistance 与 `expected_skill_id` 禁读策略。
- [x] 保留所有三任务、score-only/no-carrier-diff 和历史 evidence；不把历史 outcome 当 R2 outcome。
- [x] 由于当前 uv runtime 未安装 optional `alfworld` package，首次 reset gate 为 `not_verified`，没有 case 进入 live protocol。
- [x] 交付 `configs/blm/r2_candidate_screen.json` 与 `docs/research/blm/r2_natural_candidate_register.md`。

### R2-02：Structured ReAct boundary contract 与 atom census — `verified`

- [x] 冻结四层 contract 和 `r2_c2_structured_react_first_handoff`。
- [x] 区分 native host semantic read、flat prompt exposure、skill-id reporting read、score unread negative control。
- [x] 明确 top candidate group/full handoff group，不将派生字段伪装为独立 atom。
- [x] 交付 `configs/blm/r2_structured_react_atom_census.json` 与 `docs/research/blm/r2_structured_react_boundary_contract.md`。

### R2-03：Intervention v3 与首次 provider-call envelope — `verified_offline`

- [x] 在 `src/skillstack/blm.py` 增加 additive v3 schema 常量和 v3 read-tracker mode；R1 v1/v2 行为保持兼容。
- [x] 新增内部 `src/skillstack/experiments/blm_natural.py`，实现 request validation、coherent group materialization、provider projection hash 和 natural envelope/replay helpers。
- [x] Runner 只在 `blm_intervention` 明确为 v3 时路由到自然 boundary；默认关闭仍不写 sidecar。
- [x] envelope scope 只承诺首次 reset、Producer/adapter output 和首次 provider request projection exact；不承诺 live response、trajectory 或 mid-episode snapshot。
- [x] drift 在 provider 前 `abstained: replay_state_incomplete`；不记录 API key、Authorization 或完整 HTTP headers。

### R2-04：固定 arms 与简单基线 — `verified_protocol_not_live`

- [x] 生成 `configs/blm/r2_natural_case_protocol.yaml`，固定八类 arms、5 repetitions、seed 42、caps 和 R2 claim boundary。
- [x] 实现 reference/crossed/no-op/top-candidate/matched-carrier/full-reference/score-negative/no-skill 的 request materialization 逻辑。
- [x] 固定 comparison dimensions：schema/static read、raw diff、no-skill、full swap、BLM coherent top-group。
- [x] invalid donor/type/state/group/content 在 Consumer/provider 前拒绝；不开放 arbitrary patch、mixed donor 或 outcome setter。

### R2-05：离线测试与 dry-run gate — `verified`

- [x] 新增 `tests/test_blm_r2_natural.py`，覆盖 default-off、v3 read sequence、group coherence、score negative control、envelope round-trip、forbidden content 和 pre-provider rejection。
- [x] 运行 R1 v1/v2 regression；不修改 R1 evidence。
- [x] 新增 `scripts/run_blm_natural.py` 的 `candidate-screen`、`dry-run`、`run`、`resume`、`summarize` 入口。
- [x] dry-run 写入 `report/week8/r2_dry_run_evidence.json`，列出 eligible/excluded、planned workload、credential redaction 和精确命令。
- [x] 当前 dry-run 为 0 eligible / 0 planned live episodes；不能静默改为 40 episodes，也不能在无人工审核时调用 provider。

### R2-06：DeepSeek live discovery pilot — `not run`

- [ ] Leo 审核 dry-run、安装/验证 ALFWorld runtime，并单独启动 live provider。
- [ ] 固定每个有效 arm 5 次、每次 reset/provider call、seed 42 shuffle 和 live caps。
- [ ] 保存 append-only raw JSONL、manifest、provider metadata（不含 secrets）；达到任何上限即停止并保留 raw evidence。

### R2-07：自然案例诊断与增量判断 — `not run`

- [ ] 只报告 per-arm validity、success/action/stop、hash/read/provenance、calls/tokens/cost/latency 和 crossed/no-op variability。
- [ ] 根据预注册状态输出 `candidate_signal_ready_for_r3`、`complete_bounded_negative`、`abstained_control_confound`、`abstained_provider_variance`、`abstained_replay_state_incomplete` 或 `invalid_donor_or_intervention`。
- [ ] 不输出正式 BLM `falsified`，不把同一 discovery set 当独立 confirmation。

### R2-08：交付、Exit Audit 与质量门禁 — `implementation_verified_live_not_run`

- [x] 交付 candidate screen、contract/census、protocol、dry-run 和离线 focused evidence。
- [x] R2 local implementation gate 记录为 `implementation_complete_live_not_run`；live-dependent gates 明确 `not run`。
- [ ] live raw → summary → diagnostics 可重算；hosted CI 只在本轮代码/doc commit 后验证本地实现，不替代 live gate。
- [ ] 只有 live pilot 完成且所有限制可审查时，才可将状态改为 `complete_candidate_ready_for_r3` 或 `complete_bounded_negative`。

## 3. 当前证据与停止条件

已实现/验证：R2 additive v3 boundary、host-side read tracking、candidate pre-screen、protocol/dry-run、FakeClient no-op/group/score/rejection tests。

历史证据：Week 3 provider runs 只用于帮助理解候选集合，不替代 R2 live outcome。

尚未验证：当前 ALFWorld runtime reset、DeepSeek live response、自然 action trajectory、provider variability、费用、matched-carrier effect、R2 increment、R3 independent confirmation。

如果 TaskSemantic 读取 `expected_skill_id`、没有真实 read-domain carrier difference、reset/request 无法重建、default-off/FakeClient no-op 漂移、matched carrier 与 semantic restoration 无法区分，或 live workload 超过冻结 caps，应停止 causal/increment claim。不得通过增加 Consumer read、修改 task、直接注入 action/model reply/outcome 或添加解题知识修复。

## 4. 下一步 handoff

R2 完成前唯一可执行下一步是由 Leo 审核 dry-run 并决定是否安装/验证 optional ALFWorld runtime、重新运行 candidate screen，再单独启动 live pilot。R2 之后 R3 只接收通过 gate 的候选并冻结独立任务、重复数、预算、统计和确认规则；不自动进入论文结论。
