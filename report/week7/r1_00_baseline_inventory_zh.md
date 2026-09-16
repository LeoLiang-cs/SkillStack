# R1-00 baseline inventory

## Material Passport

- Origin Skill: `ars-codex:academic-research-suite / experiment-agent`
- Origin Mode: validate / reproducibility audit
- Audit Date: 2026-09-16 (America/Los_Angeles)
- Verification Status: VERIFIED for the recorded baseline; historical artifacts were not re-executed unless explicitly listed.

## Git 与运行环境

| 项目 | 本轮观察 |
|---|---|
| repository | repository root（本轮 invocation cwd） |
| baseline HEAD | `67957b9b0630bbe80fde76ca9ca10a7834fad57a` |
| plan commit | `67957b9` (`docs: plan R1-R0 BLM calibration preparation`) |
| execution evidence commit | `5939faf140511aefc5055dc2b457760ac6560447`（最小 replay fixture、协议与审计制品） |
| branch | `main` |
| upstream | `origin/main` |
| ahead / behind | `0 / 0` |
| baseline worktree | clean (`git status --porcelain=v1` 无输出) |
| Python observed | `3.14.7` system；正式测试通过 `uv` 使用 Python `3.12.13` |
| platform | Darwin 25.6.0, arm64 (`Darwin leo-mac 25.6.0 ... RELEASE_ARM64_T8122`) |
| network/model/data | 0 network calls；0 model calls；0 external data |

baseline 时没有未提交用户改动。R1-00 随后新增一个最小 deterministic test fixture，原因是 plan 明确要求 3 次 exact replay 与 no-op control 的实际验证；没有修改 production runner、executor 或 trace contract。

## 审计范围与证据标签

### `implemented`（本轮读源码并可定位）

- `src/skillstack/runner.py`
- `src/skillstack/adapters/retrieval_to_execution.py`
- `src/skillstack/retrieval/{base,lexical,oracle,random,no_skill,task_semantic}.py`
- `src/skillstack/execution/{skillplan,react,recorded}.py`
- `src/skillstack/environments/fixture.py`
- `src/skillstack/{contracts,library,task_semantics}.py`
- GRASP/SkillRL/SkillOps adapters and experiment entry paths under `src/skillstack/adapters/`, `src/skillstack/experiments/`, and their `scripts/run_w4_*`, `scripts/run_w5_*`, `scripts/run_w6_*` callers
- relevant unit tests under `tests/`, including new `tests/test_blm_r1_00_replay.py`
- tracing/quality entrypoints: `src/skillstack/tracing/`, `scripts/run_core_gate.py`, `.github/workflows/ci.yml`

### `historical evidence`（用于理解已有运行，不重写为本轮验证）

- `reports/week1/`～`reports/week5/` 的 pilot、factorial、GRASP/SkillRL/SkillOps run summaries
- `reports/week6/week6_report_script_zh.md`
- `report/week7/g0_*` 与 `report/week7/g1_*` 的 F0 工程记录

这些材料可以证明历史运行或工程 gate 的记录存在；除本轮重新运行的测试外，不称为 R1-00 实际验证。

### `proposal`

- `docs/original/skillstack_draft_framework_2.md`
- `docs/final_cards/`
- baseline 版本的 R1-00 plan list 与 master plan 中尚未执行的 R1-01～R1-05

framework、final cards、计划文档只定义方法/主张边界，不作为实现证据。

### `not verified`

- live provider 的模型内部读取、随机 replay 与真实费用
- 通用 ALFWorld mid-episode snapshot replay
- natural-case hidden dependency
- 正式 benchmark、统计效应、方法增量与 novelty
- 外部 GRASP/SkillRL/SkillOps checkout 的当前可用性与远端状态（本轮不需要，未检查）

## 本轮实际执行范围

- 静态：真实 call path、read sites、transport、Consumer-local registry、outcome derivation、A→L 排除。
- 动态：C1 reference 三次 exact replay、no-op instrumentation exact control、Oracle versus NoSkill outcome sensitivity。
- 协议：donor、arms、invalid cases、threat/stop conditions、R1-01 handoff。
- 未运行：live provider、训练、外部数据、自然案例、R1-02～R1-05、正式模型实验。
