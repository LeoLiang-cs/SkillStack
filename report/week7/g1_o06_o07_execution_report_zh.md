# Week 7：G1 Batch 3/4（O06 + O07）执行报告

- 日期：2026-09-16
- 对应计划：[G1 Core Alpha 完成计划清单](../../docs/plan/g1_core_alpha_plan_list_zh.md)
- 对应任务：O06（用户、贡献者与研究文档）+ O07（安全、维护与 release packet）
- 报告状态：`in_progress`
- 执行边界：本轮只完成短时文档、策略和离线回归；没有启动 30 分钟以上实验、训练、benchmark 或 live provider 调用。

## 已完成的交付

### O06 文档

1. 新增 [`docs/user/quickstart.md`](../../docs/user/quickstart.md)，把 wheel/sdist
   的非 checkout 安装、零模型 demo、输出目录和 claim boundary 写成可执行用户路径。
2. 新增 [`docs/user/configuration_and_runs.md`](../../docs/user/configuration_and_runs.md)，
   固定当前 backend metadata 优先级、`.env` 边界、manifest/trace/summary、resume 和状态语义。
3. 新增 [`docs/user/troubleshooting.md`](../../docs/user/troubleshooting.md)，覆盖安装、repo-only
   命令、路径拒绝、identity drift、provider error、可选数据和 skip 边界。
4. 新增 [`docs/development/architecture_and_extensions.md`](../../docs/development/architecture_and_extensions.md)，
   说明 R–A–D–C–L 责任坐标、最小 adapter 扩展和 schema 迁移规则。
5. 新增 [`docs/research/reproducibility.md`](../../docs/research/reproducibility.md)，分开
   implementation、acceptance、performance、paper reproduction，并明确 BLM 仍是 G2/G4 研究任务。
6. 更新 `README.md`、`docs/README.md`、`CONTRIBUTING.md` 入口和目录索引。

### O07 安全、维护与发布准备

1. 新增 [`SECURITY.md`](../../SECURITY.md)，规定凭证、路径逃逸、unsafe execution 和 supply-chain
   问题的报告边界；不在公开 issue 中提交 secret。
2. 新增 [`docs/open_source/MAINTENANCE.md`](../../docs/open_source/MAINTENANCE.md)，记录支持矩阵、
   schema/依赖变更、release-ready 与 owner confirmation 边界。
3. 新增 [`docs/open_source/RELEASE_PACKET_TEMPLATE.md`](../../docs/open_source/RELEASE_PACKET_TEMPLATE.md)，
   将验收 SHA、制品 hash、平台证据、schema、安全和回滚字段固定为同一候选 packet 的必填项。
4. LLM provider 错误详情增加有限长度和 credential-like value 脱敏；trace status counter 修复
   `task_success=null` 不应被计为 `task_failure` 的边界。

## 当前未宣称完成的项目

- G0 正式项目 commit gate、hosted CI URL 和维护平台实际结果仍待 Leo 侧确认/运行。
- wheel/sdist 的 Python 3.10 historical 与 Python 3.12 macOS local smoke 已通过；Python 3.11、
  hosted Linux/macOS 和最终验收 SHA 绑定仍需补齐。
- O04 的 partial-tail/cancelled 基础 writer fixture 已通过，但 missing-summary、retry policy 和
  maintained integration fixture 尚未全部补齐；旧 Week 1–5 脚本仍是 historical entrypoint。
- O07 的 release packet 目前是模板和草稿阶段；没有创建 tag、GitHub Release、PyPI 发布，也没有
  把 BLM cards 纳入 public alpha。

## 本轮验收命令

本轮修改完成后直接运行短时检查，当前结果：

```bash
uv run python -m unittest discover -s tests -q
uv run skillstack check-repo --root .
uv run python -m compileall -q src scripts tests
git diff --check
```

结果为：Python 3.10 与 Python 3.12 的 `unittest` 均为 127 passed、1 conditional skip；`check-repo` 278 files、0
findings；`compileall` 和 `git diff --check` 均通过。wheel/sdist 在 Python
3.10 historical 与 Python 3.12 macOS local fresh venv 中均通过
version/help/config/demo smoke；Python 3.12 macOS local full core gate 也已
通过，但 hosted Linux/macOS evidence 仍未运行。

只有这些检查和同一验收 SHA 的 packaging/hosted 证据齐全后，才可把 O06/O07 或 G1 标为
`verified`/`release-ready`。
