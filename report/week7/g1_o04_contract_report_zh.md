# Week 7：G1 Batch 2（O04）执行报告

- 日期：2026-09-16
- 对应计划：[G1 Core Alpha 完成计划清单](../../docs/plan/g1_core_alpha_plan_list_zh.md)
- 对应任务：O04 稳定运行与输出契约（第一批最小实现）
- 报告状态：`in_progress`
- 范围：本轮只处理短时、离线的 writer/trace contract；没有启动任何 30 分钟以上实验、训练或 provider 调用。

## 已完成

1. `JsonlTraceWriter` 现在生成 `skillstack-run-manifest-v1`，为 manifest 计算稳定的 `run_identity_sha256`，并将 `created_at_utc` 从 identity canonicalization 中排除。Demo/core path 同时记录 task/data hashes、component source/fidelity、config hash、model/prompt/decoding/budget/seed/oracle 字段；`repo_dirty` 与 `external_checkout_commit` 未探测时显式写 `unavailable`。
2. manifest 和 summary 改为同目录临时文件 + `os.replace` 原子落盘；重复写入仍 fail-closed。
3. 用户提供的 `run_id` 只允许单一相对路径组件，自动规范化安全字符，并检查 output-root containment；绝对路径、`..` 和跨目录输入会拒绝。
4. 新增 `JsonlTraceWriter.resume(...)`：读取原 manifest，比较完整 identity，配置漂移时拒绝 resume。
5. JSONL episode 写入增加 `skillstack-episode-trace-v1`、`run_status`、`measurement_status`、`task_success`；runner exception、task failure、timeout/cancelled 不再只由 `success=false` 表示。
6. summary 增加可重算的 `planned/started/completed/valid/success/task_failure/error/timeout/cancelled/invalid/abstained/skipped` counters。demo 的 manifest/trace/summary 已使用统一 schema 名称。

## 实际验证

| 检查 | 结果 |
|---|---|
| `tests.test_jsonl_writer` + `tests.test_demo` | PASS：13 tests |
| 完整 `unittest discover` | PASS：Python 3.10 historical 与 Python 3.12 macOS 均为 127 passed，1 conditional skip |
| demo manifest/trace/summary inspection | PASS：schema、identity、status counters 均存在 |
| wheel/sdist fresh-venv acceptance | PASS（Python 3.10 historical 与 Python 3.12 macOS local smoke；两条版本路径均完成 version/help/config/demo smoke 与 2 demo runs；hash 见 `g1_package_acceptance_current*.json`） |
| resume identity drift | PASS：配置改变时拒绝 |
| duplicate episode ID | PASS：拒绝重复追加 |
| absolute/`..` run ID | PASS：拒绝路径逃逸 |
| cancelled / malformed tail | PASS：已完成记录保留；截断 JSONL 尾行给出诊断，不计为完成 |
| unknown `task_success` | PASS：不静默计为 `task_failure` |
| provider error detail redaction | PASS：credential-like value 脱敏且限制长度 |
| model/network calls | 0 / 0 |

## 尚未宣称完成的 O04 项

- manifest 尚未补齐所有 live/model/budget/prompt 字段的统一来源与 secret redaction；
- retry/failed-episode policy、budget exhaustion 和 partial-tail recovery policy 尚未完整覆盖；malformed-tail、missing-summary 与 cancelled evidence 已有 writer tests；
- 至少一个 maintained offline integration 尚未迁移到统一 contract；
- 旧 Week 1–5 research scripts 仍保留 historical entrypoint 身份。

因此 O04 和 G1 仍为 `in_progress`。下一步继续补齐 O04 fixture/summary 重算测试，再进入 O05/O06；BLM calibration 仍保持 G2 之后启用。
