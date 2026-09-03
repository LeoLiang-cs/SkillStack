# SkillOps Maintenance M1–M3 零模型验收报告

**结论：** M1、M2、M3 全部通过。此次只证明 opaque adapter 的往返安全、
released exact-duplicate merge 在受控债务上的正确性，以及记录器不改变原生
GRASP 选择；没有运行 ALFWorld episode，也没有得到任务性能结论。

## 1. 固定边界

- SkillOps commit：`c80b05246369c0b9d82a293390ca5add675c516a`
- GRASP commit：`9d7d125a3e9b46ed591692475eb07aff4ae67d34`
- fidelity：`source_variant_opaque_contract`
- L-clean：Week5 `grasp-001` 与 `skillrl-001`，共 2 个技能
- L-stress：为每个 L-clean skill 注入 1 个 exact duplicate clone，共 4 个技能
- host：未修改的 GRASP `SkillAwareAgent`、repository 与 Top-3 selector
- M1–M3 模型调用：0；ALFWorld episode：0；长耗时实验：未启动

Adapter 保留 native payload、provenance、原始 Markdown bytes 与 SHA-256。用于
SkillOps signature 的 contract 只包含行为 fingerprint 和 opaque injection
标记，不把自然语言内容猜成 semantic P/O/A/V/F。

## 2. M1：往返与 clean no-op

| 检查 | 结果 |
|---|---:|
| L-clean input skills | 2 |
| identity round trip byte-identical | 通过 |
| clean sweep output byte-identical | 通过 |
| required field loss | 0 |
| merge / retire / repair | 0 / 0 / 0 |
| validators / adapters added | 0 / 0 |

ID map 保持 `grasp-001 → grasp-001`、`skillrl-001 → skillrl-001`。这说明当前
opaque boundary 能安全承载这两份 GRASP Markdown；它不是语义兼容性或性能证明。

## 3. M2：受控重复债务

released `MaintenanceEngine.sweep()` 将 L-stress 从 4 个技能降到 2 个，只删除：

- `grasp-001__controlled_clone_01`
- `skillrl-001__controlled_clone_01`

两个 clone 分别映射回 non-synthetic parent `grasp-001` 和 `skillrl-001`。
merge precision=1.0、recall=1.0；survivor 选择正确且原始 Markdown bytes 未变化。
sweep 报告为 merge=2，其余 maintenance action 全为 0。

这是 controlled exact-duplicate setting 下的 primitive correctness。它不能外推
到 semantic duplicate、validator repair、retirement 或自然增长 library。

## 4. M3：unchanged-host parity

在 val split 的 24 个 task descriptions 上，raw stress 与 maintained stress 各自
执行原生 `_select_skills`，再由仅监听原生日志的 recorder 执行同一方法：48/48
task-library checks 的 selected names 均逐项一致。SkillOps planner 未导入，
GRASP host 没有新增 SkillOps-specific branch。

已冻结并记录以下 SHA-256：GRASP selector、repository、ALFWorld evaluator/task、
environment、base skeleton、val split 与 `configs/llm_backends.json`。同时保存 24
个 task IDs 及其整体 hash，并记录未来 performance cell 的 DeepSeek V4 Flash
配置与默认预算。

作为诊断而非性能结果，受控 clone 已实际改变下游输入：raw library 每个任务
选择 3 个技能，24 次选择中共出现 24 个 clone slot；maintenance 后每个任务只
有 2 个技能。24/24 task 的 selected-name list 因去重而不同。按当前静态渲染，
24 个任务累计注入字符从 207,792 降到 111,816（减少 95,976，约 46.2%）。这
只能说明 prompt 输入发生了预期结构变化，不能说明成功率、模型 token 成本或
任务质量改善。

## 5. 验收与下一步边界

仓库测试结果为 83 passed、1 skipped；skip 是既有条件跳过，不是 M1–M3 失败。
机器可读结果位于 `runs/week6/w6_skillops_m1_m3/`：

- `m1_roundtrip_summary.json`
- `controlled_debt_manifest.json`
- `m2_maintenance_summary.json`
- `m3_boundary_parity.json`
- `summary.json`

M4–M6 仍未实现、未启动。下一步若获单独批准，应先实现带 resume/checkpoint 的
双 cell performance runner，再由用户亲手启动 val 24 长跑。compatibility、
maintenance correctness、gate admission 和实际 ALFWorld performance 必须继续
分开报告。
