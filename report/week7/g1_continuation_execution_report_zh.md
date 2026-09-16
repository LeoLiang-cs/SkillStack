# Week 7：G1 继续执行报告

- 日期：2026-09-16
- 对应计划：[G1 Core Alpha 完成计划清单](../../docs/plan/g1_core_alpha_plan_list_zh.md)
- 范围：继续完成可直接推进的 O02/O04/O05/O06/O07 技术项
- 状态：`in_progress`；没有进行提交、推送、tag、GitHub Release、PyPI 发布或 BLM 实验
- 长任务边界：没有启动 30 分钟以上实验、训练、benchmark、ALFWorld 服务或 live provider 调用

## 本轮完成

### O02：配置与发行包验收

1. `load_backends()` 固定优先级为：显式调用方路径 →
   `SKILLSTACK_LLM_CONFIG` → `$XDG_CONFIG_HOME/skillstack/llm_backends.json`
   （或 `~/.config/skillstack/llm_backends.json`）→ checkout 配置 → 包内安全默认。
2. 显式路径或环境覆盖不存在时直接报错，不静默切换 provider 配置；配置来源和
   用户/贡献者入口写入 [`docs/user/configuration_and_runs.md`](../../docs/user/configuration_and_runs.md)。
3. `LlmClient` 增加有限 retry/backoff、timeout 校验、run-level call/prompt-token/
   completion-token/cost budget；预算耗尽为显式 `BudgetExceededError`，已记录 usage 不被抹掉。
4. 配置 loader 现在在网络请求前校验 JSON、endpoint scheme、必需字段、retry/budget
   数值和 price metadata；`load_backend(name)` 对未知 backend 给出稳定错误。
5. `scripts/check_package_install.py` 增加 metadata、MIT license、
   `THIRD_PARTY_NOTICES.md`、console entry point 和卸载后不可 import 检查；失败时也会
   写入失败命令、错误类型和已生成制品 hash 的 summary。

### O04：运行与输出契约

1. summary 自动绑定 manifest 的 `run_identity_sha256`、`code_commit` 和
   `generated_at_utc`；传入漂移 identity 会拒绝写入。
2. 新增 [`tests/test_offline_contract_integration.py`](../../tests/test_offline_contract_integration.py)，
   通过 maintained deterministic fixture resume writer，并从 raw JSONL 重算 summary counters。
3. provider error redaction 增加 cookie/set-cookie credential-like 值覆盖；retry 只
   处理 transient HTTP/network error，认证错误不重试。

### O05/O06/O07：门禁、文档与安全

1. CI 的 `actions/checkout` 已固定到 immutable v7 commit；`contents: read` 保持不变。
2. 新增 [`scripts/run_core_gate.py`](../../scripts/run_core_gate.py)，将普通 core gate 的
   `tests_run/failures/errors/skips/skip_reasons` 写入 JSON；只允许计划中明确的条件 skip，
   意外 skip 会使 gate 失败。
3. CI 已改用该 core gate；本地 3.10/3.12 两份摘要均为 `pass`，各自 137 tests、0
   failure、0 error、1 个已知条件 skip：
   [`g1_core_gate_local_310.json`](g1_core_gate_local_310.json) 与
   [`g1_core_gate_local_312.json`](g1_core_gate_local_312.json)。
4. CI 对 core gate 与 packaging acceptance 摘要使用 immutable-pinned
   `upload-artifact` 并设置 14 天 retention；失败时仍会保留 JSON 证据，不上传 runs、数据或凭证。
5. 更新配置、预算、历史脚本边界、安全说明和当前 publication audit；不把 BLM 写成已实现。
6. G1 计划同步勾选已完成的本地技术项，hosted/owner gate 继续保持未完成。

## 实际验收

| 检查 | 结果 |
|---|---|
| targeted contract/client/demo tests | PASS：37 tests |
| full local suite | PASS：Python 3.12.13 macOS 与 Python 3.10.20 historical 均为 137 passed，1 conditional skip |
| `skillstack check-repo --root .` | PASS：280 files，0 findings，0 model/network calls |
| `compileall` | PASS |
| `git diff --check` | PASS |
| core gate（stdlib offline gate） | PASS：Python 3.10/3.12 均为 137 tests、0 failure、0 error、1 个 allowlisted conditional skip |
| packaging failure-path summary | PASS：故意使用不可用 Python selector，非零退出并保留 `status=fail`、failed command 与已生成 wheel SHA-256 |
| wheel/sdist fresh venv | PASS：Python 3.12 macOS；version/help/config/demo、metadata/license/entrypoint、uninstall 后 import 均通过 |
| package wheel SHA-256（Python 3.12 macOS） | `38e950b9e45b94ea93682041b870efab7e8a8523cbf0bec945fb5ee3debae04e` |
| package sdist SHA-256（Python 3.12 macOS） | `3e3e740bf2f39a876bd889b7b296ebc1bc43d26a384ede35f447d70f0f0faf7c` |
| historical Python 3.10 wheel/sdist SHA-256（当前代码重跑） | `66e1e3d42f3fc047e1c361092692f191c4980271c3a767483352f2080f3fbbde` / `4fcb1e12cbae7117dac02b2e046dda57607ac7e9a7d581e88eb4ac39133ceb71` |
| local environment record | macOS 26.6.2 arm64；Python 3.12.13 / 3.10.20；uv 0.11.28；`uv.lock` SHA-256 `8f2f69d3b0b9bb13e757c80198541b8fd1a3e1cdca6b98799af433fb4270890f` |
| model/network calls | `0 / 0` |

本轮结果写入 [`g1_package_acceptance_continuation_312.json`](g1_package_acceptance_continuation_312.json)；历史
Python 3.10 结果写入 [`g1_package_acceptance_continuation_310.json`](g1_package_acceptance_continuation_310.json)。

## 仍未完成、且不应被本轮本地结果替代的 gate

- G0 正式项目 commit gate：当前 worktree 仍包含多批未提交路径，不能由我代替 Leo 选择正式候选文件集。
- Hosted Ubuntu 3.11/3.12 与 macOS 3.12 CI：workflow 已配置，尚无同一验收 SHA 的 URL/结果。
- 同一最终验收 SHA 的 source snapshot、wheel、sdist release packet：需要 G0 commit 后重建并绑定 hash。
- `CITATION.cff` 作者/项目元数据、BLM cards 的 public/held 与 venue/anonymity：需要 Leo 决策。
- 不创建 tag、GitHub Release 或 PyPI 发布；这些仍是单独授权动作。

因此 G1 继续保持 `in_progress`，当前可称为“本地技术项进一步完成”，不能称为
`verified` 或 `release-ready`。
