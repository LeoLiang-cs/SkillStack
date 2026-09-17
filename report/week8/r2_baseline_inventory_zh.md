# R2 baseline inventory

## Run passport

- 审计日期：2026-09-16
- 起始 HEAD：`28a02d1008049865efd63ea2001cee3ba41e59c3`
- branch：`main`
- upstream：`origin/main`；起始时已同步
- 起始 worktree：clean；实现期间产生本轮受控改动
- Python host：`3.14.7`；执行测试的 `uv` interpreter：`3.12.13`
- 平台：`Darwin arm64`（macOS）
- 网络/provider：本轮未调用；`DEEPSEEK_API_KEY`、`.env`、Authorization 和完整 HTTP headers 未写入证据
- 当前 R2 状态：`implementation_complete_live_not_run`

## 审计范围

### 源码（本轮实际检查）

- `src/skillstack/runner.py`：adapter return 后、Consumer execute 前的 intervention 路由。
- `src/skillstack/blm.py`：R1 v1/v2 contract 与 additive v3 read-tracker mode。
- `src/skillstack/experiments/blm_natural.py`：R2 candidate screen、v3 boundary、envelope/replay 和 protocol helpers。
- `src/skillstack/adapters/retrieval_to_execution.py`：四个 execution fields 与 flat context 生成。
- `src/skillstack/retrieval/lexical.py`、`task_semantic.py`、`no_skill.py`、`random.py`：R2 Producer。
- `src/skillstack/execution/react.py`：Structured ReAct host read、prompt construction、action/reporting path。
- `src/skillstack/llm/client.py`：backend metadata、budget、secret/redaction boundary。
- `src/skillstack/tracing/jsonl.py`：append-only trace/resume 约束。

### 测试（本轮运行）

- `tests/test_blm_r2_natural.py`：5 项通过。
- R1 replay/boundary/census/controls/verdict regression：37 项通过。
- `compileall` 与 `git diff --check`：通过。
- 完整 core gate、credential scan、commit/push/hosted CI：在本次实现 commit 后待运行；写入 completion record 时按实际结果更新。

### 历史报告/运行（只作历史证据）

- `report/week7/r1_00_completion_record_zh.md`、`report/week7/r1_01_completion_record_zh.md`、R1-02～R1-05 reports：R1 calibration-only evidence。
- `runs/20260818T150521707631Z_w3_picktwo_deepseek_no_skill`、`...random_skill`、`...lexical`、`...oracle`：Week 3 historical screening evidence；不当作 R2 live outcome。

### proposal/计划（不是实现证据）

- `docs/plan/skillstack_research_master_plan_v4_zh.md`：全局 proposal/status。
- `docs/plan/r2_blm_natural_case_increment_plan_list_zh.md`：R2 唯一执行清单。
- `docs/original/skillstack_draft_framework_2.md`：BLM 方法定义/claim boundary；不是实现证据。

## 证据标签规则

| 标签 | 本轮含义 |
|---|---|
| `implemented` | 已进入源码、脚本或配置，但不自动等于运行通过 |
| `verified_this_run` | 本轮实际命令/测试观察到的结果 |
| `historical_evidence` | R1/Week 3 既有 raw/report，只帮助冻结候选或比较背景 |
| `proposal` | 计划、framework、未来 R3 protocol |
| `not_verified` | 需要 optional ALFWorld runtime 或 live provider，当前未运行 |
| `excluded_claim` | 明确不允许从当前证据推出的结论 |

## 当前边界结论

R2 zero-model pre-screen 已重新计算三个任务的 lexical/task-semantic carrier diff，并保留 CD 的历史 pre-screen 差异、Pepper/Pillow 的 score-only/no-carrier-diff 情况；但当前 uv environment 没有安装 optional `alfworld` package，因此三个任务的首次 reset/reconstruction gate 均为 `not_verified`，eligible live case 为 0。该结果是环境依赖阻塞，不是 BLM 阴性结果，也不是自然案例完成证据。

TaskSemantic 的 `task_family` label assistance 已在 candidate register 和 envelope contract 中披露；实现不读取 `expected_skill_id`，但因此不能称为 deployment-unassisted retriever。
