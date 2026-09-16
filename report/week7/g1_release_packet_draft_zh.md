# G1 Alpha Release Packet（草稿）

- 日期：2026-09-16
- 状态：`in_progress`；不是发布授权，不是 tag/GitHub Release/PyPI 操作
- 对应计划：[G1 Core Alpha 完成计划清单](../../docs/plan/g1_core_alpha_plan_list_zh.md)
- 模板：[G1 release packet template](../../docs/open_source/RELEASE_PACKET_TEMPLATE.md)

## 身份与范围

| 字段 | 当前值 |
|---|---|
| 验收 commit SHA | `not run`；当前 worktree dirty，G0 正式 project commit gate 尚未完成 |
| branch/tag | `not run`；没有创建 tag |
| release policy | `configs/public_release_scope.yaml` 已存在，但尚未绑定最终验收 SHA |
| BLM cards | held；未纳入 public alpha |
| 外部数据/生成 runs/credentials | 不纳入 packet |

## 已有制品证据

| 制品 | 结果 | 证据边界 |
|---|---|---|
| wheel | PASS（Python 3.10 historical；Python 3.12 macOS local smoke） | 3.10 SHA-256：`51bf879029c4aed852b22c5ee09b37019c9103287760dce1ac98694fe5f3767b`；3.12 SHA-256：`a5b36ae9b7753cdf36e5abf5fcd21a4e984052806327e18476c1366af284b076`；仍不是 hosted-platform 证据 |
| sdist | PASS（Python 3.10 historical；Python 3.12 macOS local smoke） | 3.10 SHA-256：`27a1c4cbe7d00bd5e7322b3cafc2777a204535b217d8e78eee1d9f29a8842025`；3.12 SHA-256：`7d37cb30d37c1afaeb961e13bea75e82b5ac13bcc25eff95f72f2ea971d740d9`；仍不是 hosted-platform 证据 |
| source snapshot | `not run`（以当前验收 SHA） | 需要 G0 commit gate 后生成 |

后续本地 continuation 候选的最新 Python 3.12 wheel/sdist hash、metadata/license/
entrypoint 和卸载检查见 [`g1_continuation_execution_report_zh.md`](g1_continuation_execution_report_zh.md)。

## 当前短时门禁

本页保留第一批草稿证据；后续本地技术验收的最新结果见
[`g1_continuation_execution_report_zh.md`](g1_continuation_execution_report_zh.md)
及 [`g1_package_acceptance_continuation_312.json`](g1_package_acceptance_continuation_312.json)。

| 检查 | 当前结果 |
|---|---|
| `unittest discover` | PASS：后续 Python 3.12 macOS 为 137 passed，1 conditional skip；早期 127-test 记录保留为历史证据 |
| `skillstack check-repo --root .` | PASS：后续 280 files，0 findings |
| `compileall` | PASS |
| `git diff --check` | PASS |
| zero-model demo | PASS：2 runs，0 model/network calls |
| hosted Linux/macOS | `not run`；workflow 已配置；Python 3.12 macOS local packaging smoke 已通过 |
| G0 formal project commit gate | `not run` |

## O04/O07 contract snapshot

- manifest：`skillstack-run-manifest-v1`，带 `run_identity_sha256`；禁止覆盖并原子写入。
- episode trace：`skillstack-episode-trace-v1`，分开记录 run/measurement/task 状态。
- summary：`skillstack-run-summary-v1`，绑定 manifest identity/code commit/time，status counters 从 raw JSONL 重算。
- path boundary：run ID 只允许单一安全相对组件；绝对路径、`..` 和 output-root 逃逸拒绝。
- security：provider error detail 限长并对 credential-like value（含 cookie）脱敏；retry/backoff 与 run-level budget 已有回归测试。
- rollback：只能切回上一个已验证 commit/artifact/config；不删除或改写原始运行证据。

## 尚未满足的 release gate

1. 为同一最终 commit 生成 source snapshot、wheel、sdist，并保存 hash。
2. 完成 Python 3.11/3.12 Linux 与 macOS 的 hosted evidence，并记录 URL/commit。
3. 绑定同一最终验收 SHA 的 source snapshot/wheel/sdist，并将 hosted CI、owner file-list 和 G0 formal gate 证据填入 packet。
4. 完成 owner file-list review、venue/anonymity 决策和 G0 formal gate。

在上述项目完成前，本 packet 只能标为 `draft`，G1 不能标为 `verified` 或
`release-ready`，更不能执行发布操作。
