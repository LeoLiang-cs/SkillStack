# SkillStack Week 5 科研周报

**主题：** 从 A-slot 真实性能闭环到 SkillOps maintenance 可插拔周期

**截至时间：** 2026-09-03

**当前阶段：** A-slot 严格性能实验完成；SkillOps M1–M5 完成；held-out test 尚未运行

## 本周进展

### 本周最重要的变化

本周完成了两个相互衔接、但结论层次不同的工作。

第一，Week 4 只证明 GRASP proposer 与 SkillRL-shaped updater 可以通过 adapter
进入同一个 GRASP repository 和 gate。本周恢复 AgentBench 环境，补完严格
13/13 A-slot 性能实验，使证据从“组件接得上”推进到“候选会改变真实
ALFWorld 结果”。

第二，在 A-slot 产生的两个有效 skill 上接入 SkillOps maintenance，完成
`GRASP/SkillRL-produced library → SkillOps maintenance → unchanged GRASP host`
的 M1–M5 周期：先验证可逆 adapter 和受控重复债务，再在不修改下游 selector、
prompt injection、environment 和 evaluator 的前提下完成三次 val 重复运行。

```text
A-slot：GRASP / SkillRL proposer → fixed GRASP gate
                                  ↓
             two effectiveness-accepted skills
                                  ↓
Lifecycle：raw library → SkillOps exact-duplicate merge → maintained library
                                  ↓
                    unchanged GRASP D/C host
```

### 当前阶段性结论

1. **A-slot performance：** A0 与 A1 各产生一个 12/13、1 fix、0 regression
   的有效候选；由于只有一个 seed 且候选数量不等，不能比较 A0/A1 谁更优。
2. **Maintenance compatibility：** 两个 Week 5 skill 可以通过可审计的 opaque
   adapter 无损进入和离开 released SkillOps library。
3. **Maintenance correctness：** 对预先注入的 exact duplicates，SkillOps
   只删除预期 clone，merge precision/recall 均为 1.0。
4. **Task performance：** 三次 val 重复中 raw 为 63/72，maintained 为 64/72；
   差值只有 +1/72，bootstrap 95% CI 跨过 0，因此没有方向稳定、可分辨的性能差异。

这个结果完成了第一轮 exact-duplicate maintenance 周期。它支持跨论文组件边界
与受控维护动作的正确性，但不支持“maintenance 提升任务性能”或“复现完整
SkillOps”的主张。

## 论文阅读总结

### 阅读主题与重点论文

本周重点刷新了 SkillOps 论文与官方代码，并把它与 Week 4 的 GRASP、SkillRL
组件分析连接起来。SkillOps 把长期增长的 skill library 视为需要维护的软件
生态：skill 用 `(P,O,A,V,F)` 表示，即 Precondition、Operation、Artifact、
Validator 和 Failure modes；library 通过 dependency、compatibility、redundancy、
alternative 和 lineage 等关系组织。

### 主要收获

论文提出 merge、repair、retire、add-validator 和 add-adapter 等 library-time
动作，但当前 released `MaintenanceEngine.sweep()` 只自动执行其中一部分：
signature merge、可选 usage retirement，以及特定 synthetic tag 下的 validator
补充；repair 和 adapter 仍需要调用者提供 domain-specific 内容。官方代码没有
公开论文规模的完整 health diagnosis、200–2000 skill libraries 或对应原始 runs。

因此，本周没有把 GRASP Markdown 中的自然语言建议强行解释成完整语义
`(P,O,A,V,F)`，而是采用 `source_variant_opaque_contract`：保留原始 bytes、
native payload 和 provenance，只用 `description + content + tags` 的稳定
fingerprint 识别人工构造的 exact duplicates。

### 对当前研究的影响

- Lifecycle 必须区分候选 admission 与既有 library maintenance。
- 跨论文 adapter 的首要要求是可逆和可审计，而不是主动猜测缺失语义。
- Compatibility、maintenance correctness、gate admission 和 task performance
  必须分开报告。
- 第一轮只测试 released exact-duplicate merge；semantic duplicate、repair、
  validator 和 adapter maintenance 属于新的实验轴。

## 实验结果总结

### 1. A-slot 严格 13/13 性能闭环

26 个 GRASP dev 任务按冻结顺序分为 13 条 proposal evidence 和 13 条独立
history/probe。两个 cell 共享空 library、DeepSeek Flash writer、ADD-only、
相同 repository、原生 gate 与 `native admitted AND fixes > 0` sensitivity。

| Cell / 候选 | Baseline | Candidate | fixes | regressions | 原生 gate | Effectiveness |
|---|---:|---:|---:|---:|---|---|
| A0 `grasp-001` | 10/13 | **12/13** | **1** | **0** | accepted | accepted |
| A1 `skillrl-001` | 9/13 | **12/13** | **1** | **0** | accepted | accepted |
| A1 `skillrl-002` | 9/13 | 9/13 | 0 | 2 | no-op | rejected |
| A1 `skillrl-003` | 8/13 | 9/13 | 0 | 2 | accepted | **rejected** |

正式运行 130 个 ALFWorld episodes，0 个正式 episode error。A0 proposer 调用
3 次、生成 1 个候选；A1 proposer 调用 1 次、生成 3 个候选，但三个候选带来
更高的总 probe 成本。整体为 2,608 次模型调用，估算成本约 **$1.98665**。

`skillrl-003` 说明原生 gate admission 不能等同实际有效性：它 fixes=0 且有
2 个 regression，却因 fresh baseline 波动被原生 gate 接受；effectiveness
sensitivity 将其拒绝。

### 2. SkillOps M1–M3：边界与受控维护

| 阶段 | 检查 | 结果 |
|---|---|---|
| M1 | L-clean 2 skills identity round trip | bytes 完全一致；required field loss=0 |
| M1 | L-clean released sweep | no-op；0 false merge |
| M2 | L-stress 4→2 exact-duplicate merge | precision=1.0；recall=1.0 |
| M2 | survivor 与意外 mutation | 两个 non-synthetic parent 保留；bytes 不变 |
| M3 | 24 val descriptions × 2 libraries | recorder 与原生 selector 48/48 parity |
| M3 | host boundary | 未导入 SkillOps planner；无 SkillOps-specific host branch |

M3 的静态 prompt 诊断显示，去重后 24 个任务累计注入字符从 207,792 降到
111,816，减少约 46.2%。这只证明下游输入发生预期结构变化，不代表实际 token
成本或任务性能改善。

### 3. SkillOps M4–M5：三次 val 重复

M4 先跑 seed 42 的 48-episode pilot；M5 再补 7、123 两次重复。两个 cell
共享相同 24 个 val task IDs、DeepSeek Flash、temperature 0、GRASP selector、
environment、evaluator 和预算，唯一实验变量是 raw/maintained learned library。

| Replicate | Raw | Maintained | 差值 | fixes | regressions |
|---|---:|---:|---:|---:|---:|
| 42 | 21/24 | 22/24 | +1 | 1 | 0 |
| 7 | 22/24 | 20/24 | −2 | 0 | 2 |
| 123 | 20/24 | 22/24 | +2 | 2 | 0 |
| **合计** | **63/72** | **64/72** | **+1** | **3** | **2** |

- Raw success：87.50%；maintained success：88.89%。
- Mean paired difference：+1.39 个百分点。
- Task×replicate bootstrap 95% CI：**[−4.17, +8.33] 个百分点**，包含 0。
- 144/144 episodes 完成，0 formal episode error，0 `.failed` diagnostic。
- 2,224 次模型调用，估算成本 **$1.29214**。
- Raw：1,065 calls、$0.61345；maintained：1,159 calls、$0.67870。
- 32 次孤立 tool-message 清理：raw 17、maintained 15。

尽管 maintained library 静态注入更短，它在实际运行中调用次数和总成本反而略高。
这说明 prompt 结构压缩不能直接推导 end-to-end 成本下降；trajectory 长度与任务
波动仍会主导总调用量。

### 当前最有希望的方向

目前最可信的贡献不是性能提升，而是**跨论文 lifecycle component 的可审计
可插拔性**：外部产生的 library 可以经过显式、可逆 adapter 进入 released
maintenance primitive，得到身份级 old→new mapping，再由未改写的原生 host
继续消费。负向或零性能结果不会抹去这条 compatibility/correctness 证据。

## 当前问题

### 1. Task performance 没有稳定方向

三个 replicate 的差值为 +1、−2、+2，aggregate CI 跨过 0。Task 17 和 42
在不同重复中出现相反变化；task 30 和 48 在两个 cell、三次重复中都失败。

**证据：** 运行完整、library hash 固定、0 episode error。

**推测：** 差异可能来自 provider/environment nondeterminism、trajectory 分叉或
任务执行顺序，但目前没有 trajectory-level 归因，不能写成确定原因。

### 2. Replicate seed 的控制范围有限

当前 seed 只控制任务顺序，没有向 DeepSeek provider 传递随机种子。因此应称为
三次重复运行，而不是严格的模型随机种子实验。

### 3. Maintenance fidelity 仍然有限

第一轮只验证人工注入的 exact duplicate debt。它不代表自然增长 library 中的
semantic redundancy，也没有测试 repair、retire、add-validator、add-adapter 或
论文完整 health diagnosis。

### 4. Provider 与来源边界

- A1 使用 DeepSeek Flash substituted writer，不是 source-faithful Azure O3。
- A-slot 有 72 次、SkillOps performance 有 32 次 tool-history sanitizer events。
- 适配后可以完整运行，但不能写成 provider/environment 原生无摩擦。

## 下周计划

1. **先做 trajectory error analysis：** 对 task 17、42、30、48 比较 raw 与
   maintained 的 selected skills、动作序列、停止状态和调用长度，区分稳定困难
   任务与重复运行波动。
2. **冻结第一周期报告：** 把 A-slot、M1–M3 和 M4–M5 的 evidence hierarchy、
   成本及 fidelity 标签统一到 advisor report，保留所有负结果。
3. **决定是否消耗 held-out test：** 在运行 M6 前明确其问题是“确认性能提升”
   还是“检查去重后是否有明显伤害”；当前没有预注册 non-inferiority margin，
   不能事后把零差异改写成“不劣”。
4. **规划下一轮 semantic maintenance：** 只有在明确 canonical fields 的来源与
   验证方式后，才设计 `semantic_contract_v1`；不在 opaque adapter 中静默加入。
5. **保留 fidelity control：** 若获得 Azure O3 凭证，再把 source-faithful
   SkillRL 作为独立 control，而不是覆盖当前 substituted evidence。

## 希望讨论的问题

1. 第一轮论文贡献是否应聚焦 **adapter-compatible lifecycle portability +
   maintenance correctness**，而不强调性能提升？
2. 当前 val 结果 CI 跨过 0，是否仍值得消耗一次 held-out test；如果值得，M6
   的预注册主问题与停止条件是什么？
3. 下一周期应优先做 natural/semantic duplicate，还是更严格地控制 provider
   randomness 与 trajectory variance？
4. Exact-duplicate stress library 是否足以作为第一个 maintenance boundary
   case study，还是需要至少增加一种可验证的 validator/repair debt？
5. Source-faithful SkillRL/Azure O3 是否是论文提交前的必要 fidelity control？

## 本周资源与完整性汇总

| 实验 | ALFWorld episodes | 模型调用 | 估算成本 | 正式 error |
|---|---:|---:|---:|---:|
| A-slot 13/13 performance | 130 | 2,608 | $1.98665 | 0 |
| SkillOps M4–M5 val | 144 | 2,224 | $1.29214 | 0 |
| **合计** | **274** | **4,832** | **$3.27879** | **0** |

M1–M3 为零模型检查，不计入模型调用和 API 成本。当前仓库测试为 89 passed、
1 conditional skip。

## 证据索引

- [Week 5 A-slot 导师简报](../00_overview/w5_advisor_brief_zh.md)
- [A-slot 数字审计](../05_experiments/w5_performance_evidence_audit.md)
- [SkillOps 论文与源码刷新](../02_paper_analysis/skillops_refresh_zh.md)
- [SkillOps M1–M3 验收](../05_experiments/skillops_m1_m3_summary_zh.md)
- [SkillOps maintenance 实验计划](../01_planning/skillops_maintenance_experiment_plan_zh.md)
- M4–M5 机器结果：`runs/week6/w6_skillops_val_pilot/summary.json`
- M4–M5 配对结果：`runs/week6/w6_skillops_val_pilot/paired_summary.json`
