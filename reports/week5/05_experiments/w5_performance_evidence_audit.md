# Week 5 严格 13/13 A-slot 性能证据核对

**运行目录：** `runs/week5/w5_a_slot_seed2_deepseek_flash/`

**完成时间：** 2026-09-03 UTC（洛杉矶时间 2026-09-02）

**实验状态：** complete

**Provider fidelity：** `provider_substituted_deepseek_flash`

本文件只做“原始结果 → 可报告结论”的审计。它不重新运行实验，也不把
接口兼容、gate 准入和任务性能合并成一个结论。

## 1. 设计与隔离性

GRASP dev split 的 26 个任务按冻结的 epoch-0 顺序
`2:shuffle:0` 划分为两个不重叠的 13-task 子集：

- **proposal source 13：** 只用于生成 A0/A1 候选；初始成绩 8/13，其中
  5 条失败轨迹触发 proposer。
- **history/probe source 13：** 只用于冻结 reference failure map 和评估候选；
  初始成绩 11/13，reference failures 为任务 8、9。

运行 manifest 明确记录 `val_test_access_in_component_split=false`。两边共享
同一份 evidence、空 learned library、相同 library hash、相同 DeepSeek Flash
writer、最多 3 个 ADD 候选、相同 GRASP repository 与原生 gate；没有进行
contrastive revision。每个候选都在隔离 fork 中 apply，结束后 cleanup。

每个候选使用 13 个 fresh baseline episode 和 13 个 candidate episode。
因此正式 episode 数为：

```text
共享初始 evidence       13 + 13 = 26
A0：1 个候选          1 × 26 = 26
A1：3 个候选          3 × 26 = 78
总计                            130
```

## 2. 运行完整性

对 130 个正式 checkpoint 的 `entry.error` 逐项检查：

| 项目 | 数量 |
|---|---:|
| 正式 ALFWorld episode | 130 |
| 正式 episode error | **0** |
| `completed` | 96 |
| `task limit reached` | 33 |
| `agent validation failed` | 1 |

`task limit reached` 和 `agent validation failed` 是任务结果状态，不等于运行
异常；唯一一条 `agent validation failed` 的 episode 仍被 evaluator 判为成功。
脚本只会在 `result.error` 为空时写入正式 checkpoint，因此失败重试或诊断文件
不能混入这 130 条正式记录。

## 3. 候选与 gate 结果

### A0：GRASP proposer

A0 用 3 次 proposer 调用完成 classify → diagnose → group → propose，生成并
原生验证 1 个 ADD 候选：`grasp-001 / infer_goal_from_task_instruction`。

| 指标 | 结果 |
|---|---:|
| Fresh baseline | 10/13 |
| Candidate | **12/13** |
| Gate fixes | **1**（任务 9） |
| Gate regressions | **0** |
| Native GRASP gate | accepted |
| Effectiveness sensitivity | accepted |

### A1：SkillRL-shaped additive updater

A1 用 1 次 proposer 调用，经 released prompt/parser 生成 3 个合法 ADD：

| 候选 | 内容简称 | Fresh baseline | Candidate | fixes | regressions | Native gate | Effectiveness |
|---|---|---:|---:|---:|---:|---|---|
| skillrl-001 | 只使用合法动作 | 9/13 | **12/13** | **1**（任务 8） | **0** | accepted | accepted |
| skillrl-002 | 系统搜索所有位置 | 9/13 | 9/13 | 0 | 2（23、43） | no-op | rejected |
| skillrl-003 | 每次观察后立即行动 | 8/13 | 9/13 | 0 | 2（4、43） | accepted | **rejected** |

`skillrl-003` 是本周最重要的 gate 边界例子：它没有修复 reference failure，
并产生 2 个 regression；但 fresh baseline 自身产生 3 个 regression，原生规则
计算出 `adjusted_score=+1`，所以仍然 accepted。要求
`native_admitted AND fixes > 0` 的 effectiveness sensitivity 将其拒绝。这个
sensitivity 是 SkillStack 的解释性附加分析，不能冒充 GRASP 原生判定。

## 4. 为什么“12/13”不等于“1 fix”或“3 分净提升”

本实验中的 agent 调用存在运行随机性。每个候选都有独立 fresh baseline，
所以 A0、A1 三个候选的 baseline 分别为 10、9、9、8/13，不能彼此直接相减
后当成候选的稳定因果效应。

GRASP gate 的 `fixes` / `regressions` 是相对于冻结的 reference failure map
（任务 8、9）统计；`adjusted_score` 再用同一候选的 fresh baseline 波动进行
校正。因此报告必须同时保留：

1. candidate 原始成功数；
2. raw fixes / regressions；
3. 原生 admission；
4. `fixes > 0` effectiveness sensitivity。

这四项回答不同问题，不能互相替代。

## 5. 成本与调用核对

| 阶段 | 模型调用 | 估算成本（USD） |
|---|---:|---:|
| 共享 evidence（26 episodes） | 535 | $0.40058059 |
| A0 proposer | 3 | $0.01744072 |
| A0 probes（26 episodes） | 464 | $0.32055406 |
| A1 proposer | 1 | $0.00131032 |
| A1 probes（78 episodes） | 1,605 | $1.24675966 |
| **合计** | **2,608** | **$1.98664535** |

按报告精度，整体估算成本约 **$1.98665**。A1 proposer 本身比 A0 少两次
调用且更便宜，但 A1 生成 3 个候选、A0 只生成 1 个候选，因此 A1 的总 probe
调用与成本明显更高。这里比较的是本次实际运行开销，不是同候选数预算下的
算法效率，也不是候选质量。

## 6. Provider / 环境适配摩擦

`sanitize_tool_history` 只删除在可见历史中找不到前置 assistant tool call 的
孤立 tool message，并为每次删除留下事件记录。对正式记录逐项计数共有
**72 次**：

| 记录区域 | 清理次数 |
|---|---:|
| 共享 evidence | 9 |
| A0 candidate probes | 11 |
| A1 candidate probes | 52 |
| **合计** | **72** |

因此准确说法是：A1 性能链路暴露并依赖了这项 provider/AgentBench 历史适配；
完整正式运行共记录 72 次清理，其中 52 次直接发生在 A1 candidate probes。
这些事件没有形成正式 episode error，但说明当前 backend 与上游截断历史之间
存在真实摩擦，不能把“0 episode error”解释为“零适配成本”。

## 7. 可主张与不可主张

**可以主张：**

1. 130 个正式 ALFWorld episode 完成，0 个正式 episode error。
2. A0 的唯一候选与 A1 的 `skillrl-001` 都达到 12/13、1 fix、0 regression，
   且同时通过原生 gate 和 effectiveness sensitivity。
3. `skillrl-002` 没有修复并产生 regression；`skillrl-003` 暴露了原生 gate
   接受 0-fix 候选的 sensitivity disagreement。
4. A0/A1 都从兼容性层进入了真实 task-performance 层。

**不能主张：**

1. A0 或 A1 更优：只有一个 seed，且候选数量为 1 对 3；两边最佳候选同为
   12/13。
2. 原生 gate accepted 就代表候选实际有效。
3. 该结果复现完整 SkillRL：writer 是 DeepSeek Flash provider substitute，
   不是论文/源码要求的 Azure O3 source-faithful 路径。
4. 单个 13-task probe 足以支持统计显著性或跨环境泛化结论。

## 8. 原始证据映射

| 报告内容 | 原始文件 |
|---|---|
| split、初始 evidence、共享 snapshot | `evidence_summary.json`、`run_manifest.json` |
| cell 汇总、调用与成本 | `paired_summary.json`、`cells/a0/summary.json`、`cells/a1/summary.json` |
| proposer 调用、原始候选与 adapter | 两个 `proposal_output.json` |
| 每个候选的原始 probe 与 gate | 四个候选目录下的 `result.json` |
| 0 error 与 tool-history 清理 | 130 个正式 episode checkpoint 中的 `entry.error` 与 `request.history_sanitization` |
