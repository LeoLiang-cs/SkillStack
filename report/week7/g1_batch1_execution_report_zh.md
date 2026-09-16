# Week 7：G1 Batch 1（O02 + O03）执行报告

- 日期：2026-09-16
- 对应计划：[G1 Core Alpha 完成计划清单](../../docs/plan/g1_core_alpha_plan_list_zh.md)
- 对应任务：O02（安装与资源）+ O03（支持矩阵与依赖）
- 报告状态：`in_progress`
- 总体边界：本轮只完善可安装 core alpha 的离线入口和支持声明；没有启动 BLM 训练、ALFWorld/AgentBench 长实验、live provider 调用或正式测量。
- G0 前置：G0 实现已通过临时候选验证，但正式项目 commit gate 仍未签字，因此本报告不把 G1 宣布为完成。

## 1. 本轮已执行的实现

### O02：安装与资源

1. 新增 `src/skillstack/resources/` 包资源，包含零模型 demo 的 task、recorded actions、expected output 和最小 static skill library。
2. `src/skillstack/demo.py` 使用 `importlib.resources` 读取内置 fixture；`--root` 仍可显式指定 checkout，供贡献者复现。
3. 未指定 `--root` 时，demo 输出写到用户显式的 `--output-root`，否则写入当前目录的 `runs/demo/`；不会写回安装包临时资源目录。
4. `src/skillstack/llm/client.py` 增加包内安全 backend metadata fallback；显式配置路径优先，源码 checkout 仍读取 `configs/llm_backends.json`。`load_env_file()` 不再扫描作者 checkout 的 `.env`，默认只看当前工作目录；历史研究脚本仍可在 checkout 中工作。
5. 新增 `scripts/check_package_install.py`。它会构建 wheel/sdist、创建全新虚拟环境、从非仓库目录安装并运行安装后的 demo，输出 artifact hash 和运行目录。该脚本是可恢复的用户/CI 入口；本轮已直接执行 Python 3.10 historical 与 Python 3.12 macOS local smoke，仍未执行 hosted 矩阵。

### O03：支持矩阵与依赖

1. `pyproject.toml` 与 `uv.lock` 更新到 `>=3.9,<3.13`，增加 3.11/3.12 classifiers；3.9/3.10 保留为 historical reproduction。
2. CI 已配置 Ubuntu Python 3.11/3.12 与 macOS Python 3.12；release-check 固定在 Ubuntu 3.12 job。
3. 新增 [`docs/open_source/SUPPORT_MATRIX.md`](../../docs/open_source/SUPPORT_MATRIX.md)，将 maintained、historical、unverified 和 experiment-specific 环境分开，并明确 hosted evidence 尚待补齐。
4. README、CONTRIBUTING 和 G1 计划同步了新的支持边界与慢速 packaging gate 命令。

## 2. 本轮实际验证

| 检查 | 结果 | 说明 |
|---|---|---|
| `uv run python -m compileall -q src scripts tests` | PASS | 本地 Python 3.10 historical environment |
| `uv run python -m unittest discover -s tests -q` | PASS | Python 3.10 与 Python 3.12 均为 127 passed，1 conditional skip |
| `uv run python -m unittest tests.test_demo tests.test_llm_client -q` | PASS | 20 passed；含 packaged fixture、package config fallback 和 checkout/package metadata 一致性 |
| `uv run skillstack demo --output-root …` | PASS | fingerprint `266c773e6beb483d91121de31ad65bd75c1eb673bcca4f3d30ed0f097089e0f2`；2 runs；0 network/model calls |
| `uv run skillstack check-repo --root .` | PASS | 278 files，0 findings，0 network/model calls |
| `uv build` + wheel/sdist resource inspection | PASS | 当前 Python 3.10 构建制品约 104,481 / 103,333 bytes；config、demo、skill package resources 均存在 |
| 全新 wheel/sdist venv 安装 | PASS（local smoke） | Python 3.10 historical 与 Python 3.12 macOS local fresh venv 中 wheel/sdist 均通过；hosted Linux/macOS 与完整 maintained test 仍待执行 |
| hosted Linux/macOS CI | `not run` | workflow 已配置，尚无 hosted URL/commit 结果；Python 3.12 macOS local full core gate 已通过 |

本轮没有运行模型、访问 benchmark、发送 provider 请求，也没有产生训练 checkpoint。慢速或可能下载 Python/依赖的动作均保留为脚本，不把“脚本存在”写成“验收通过”。

## 3. 当前 G1 状态

已具备：

- 安装包携带离线 demo 与安全配置 metadata；
- 源码 checkout 和普通安装包的 demo 路径有明确区分；
- maintained Python/platform 目标已写入 metadata、锁文件、CI 和支持矩阵；
- wheel/sdist acceptance 可重复执行，失败时可 `--keep-temp` 保留环境和日志。

仍未完成：

- O02-00 的完整命令分类和完整配置优先级（CLI > env > user file > packaged default）；repo-only 缺少 checkout marker 的诊断已补上；
- Python 3.11/3.12 Linux 与 macOS 的 hosted evidence（当前已有 Python 3.12 macOS local full gate）；
- O04 统一 manifest/trace/summary、identity、resume 和状态模型；
- O05–O07 的测试分层、完整用户/研究文档、安全维护审计与 release packet。

因此当前 G1 仍为 **`in_progress`，不可标记 `verified` 或 `release-ready`**。当前可复核的历史环境验收记录为：

```bash
uv run python scripts/check_package_install.py --python 3.10 \
  --summary report/week7/g1_package_acceptance_current.json
```

本次 Python 3.10 结果：wheel SHA-256 `51bf879029c4aed852b22c5ee09b37019c9103287760dce1ac98694fe5f3767b`，
sdist SHA-256 `27a1c4cbe7d00bd5e7322b3cafc2777a204535b217d8e78eee1d9f29a8842025`；
Python 3.12 macOS local smoke 的 wheel/sdist SHA-256 分别为
`a5b36ae9b7753cdf36e5abf5fcd21a4e984052806327e18476c1366af284b076` 与
`7d37cb30d37c1afaeb961e13bea75e82b5ac13bcc25eff95f72f2ea971d740d9`。
四条路径均在非仓库 fresh venv 中运行 version/help/config/demo，0 network/model calls。
此外 Python 3.12 macOS full core offline gate 为 127 passed、1 skip；Python 3.10
historical full core gate 同样为 127 passed、1 skip。
在 G0 正式项目 commit、maintained packaging acceptance 和 hosted matrix evidence 形成前，
不开始 BLM calibration 或正式实验。
