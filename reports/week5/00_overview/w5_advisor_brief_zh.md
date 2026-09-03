# SkillStack Week 5——第七次导师简报（中文版）

- **当前状态：** Week 4 被环境阻塞的严格 13/13 A-slot 性能实验已完成。
- **一句话结论：** A0 与 A1 都产生了一个达到 12/13、1 fix、0 regression
  的有效候选；这把证据从“组件接得上”推进到“候选能改变真实 ALFWorld
  结果”，但单 seed 和不等候选数仍不足以比较两种方法谁更优。

## 1. 本周回答的问题

Week 4 已证明 GRASP proposer（A0）和 SkillRL additive updater（A1）能通过
显式 adapter 接入同一个、未改写的 GRASP repository 和 admission gate。
当时只能回答**兼容性**，因为 AgentBench/Docker 不可用，不能回答候选是否
真的改善任务。

Week 5 保持 A-slot 之外的边界不变，补上严格 task-performance 闭环：

```text
13 条 proposal evidence → A0 或 A1 生成 ADD 候选
                                      ↓
空 library → isolated fork/apply → 另一组 13-task fresh probe
                                      ↓
                   原生 GRASP gate + effectiveness sensitivity
```

本周要区分三个问题：

1. **兼容性：** 候选能否经过 adapter、repository 和固定 gate？
2. **Gate admission：** 原生规则是否接受候选？
3. **实际性能：** 候选在 13 个真实 ALFWorld 任务上成功多少、修复多少、
   回归多少？

三者不能混为一谈。

## 2. 严格 13/13 设计

使用 GRASP 固定 commit 的 26 个 dev 任务，按 epoch-0 的
`2:shuffle:0` 顺序切成两个无重叠子集：

| 子集 | 任务数 | 用途 | 初始结果 |
|---|---:|---|---:|
| Proposal source | 13 | 只给 proposer 看，用于生成候选 | 8/13 |
| History/probe source | 13 | 冻结 reference，并用于候选评估 | 11/13 |

两个 cell 共享同一 evidence snapshot、空 learned library、DeepSeek Flash
writer、ADD-only action、最多 3 个候选、相同 repository、相同原生 gate 和
相同 effectiveness rule。val/test split 没有进入组件实验。每个候选重新跑
13 个 baseline 和 13 个 candidate episode，并在隔离 repository fork 中应用，
完成后 cleanup。

这套设计防止 proposer 看到 probe 任务，但不消除 agent 自身的运行随机性；
因此每个候选的 fresh baseline 仍有波动。

## 3. A0 / A1 机制

**A0（GRASP proposer）**先给失败分类，再诊断、分组，最后为选中的 failure
mode 生成 proposal。本次使用 3 次 writer 调用，生成 1 个候选：
`infer_goal_from_task_instruction`。

**A1（SkillRL-shaped updater）**把 5 条失败轨迹一次性交给 released
SkillRL prompt/parser。本次只调用 1 次 writer，生成 3 个候选：

1. `use_valid_actions_only`
2. `systematically_search_all_locations`
3. `act_after_each_observation`

A1 仍需要显式 adapter 把 SkillRL 字段转换成 GRASP ADD proposal；所以准确
称呼仍是 **adapter-compatible**，不是零转换 plug-and-play。

## 4. 运行完整性

正式运行共 **130 个 ALFWorld episode**：26 个共享 evidence episode、A0
的 26 个 candidate-evaluation episode、A1 的 78 个 candidate-evaluation
episode。逐项核对后，**0 个正式 episode error**。

正式状态中有 96 个 `completed`、33 个 `task limit reached`、1 个
`agent validation failed`。后两类是 evaluator 使用的任务结果状态，不等于
运行异常；该 `agent validation failed` 样本仍被判为成功。

## 5. 核心结果

| Cell / 候选 | Baseline | Candidate | fixes | regressions | 原生 gate | Effectiveness |
|---|---:|---:|---:|---:|---|---|
| A0 grasp-001 | 10/13 | **12/13** | **1** | **0** | accepted | accepted |
| A1 skillrl-001 | 9/13 | **12/13** | **1** | **0** | accepted | accepted |
| A1 skillrl-002 | 9/13 | 9/13 | 0 | 2 | no-op | rejected |
| A1 skillrl-003 | 8/13 | 9/13 | 0 | 2 | accepted | **rejected** |

最稳妥的观察有三点：

1. A0 生成 1 个候选；它有 1 fix、0 regression，达到 12/13，原生 gate 和
   effectiveness sensitivity 都接受。
2. A1 生成 3 个候选；只有 `skillrl-001` 有 1 fix、0 regression，并达到
   12/13。`skillrl-002` 没有修复且产生 2 个 regression。
3. `skillrl-003` 没有真实 fix，还有 2 个 regression；原生 gate 因 fresh
   baseline 波动得到 `adjusted_score=+1` 而接受，但 `fixes > 0` sensitivity
   明确拒绝。

因此，gate admission 不能单独作为“skill 有效”的证据。A0 和 A1 的最佳
候选相同，都是 **12/13**。

## 6. 成本与调用结构

| 阶段 | 模型调用 | 估算成本 |
|---|---:|---:|
| 共享 evidence | 535 | $0.40058059 |
| A0 proposer + probes | 467 | $0.33799478 |
| A1 proposer + probes | 1,606 | $1.24806998 |
| **整体** | **2,608** | **$1.98664535** |

按五位小数报告，整体成本约 **$1.98665**。

A0 proposer 调用 3 次，A1 proposer 只调用 1 次；但 A1 一次生成 3 个候选，
每个候选都需要独立跑 26 个 probe episode，所以 A1 的总 probe 调用和成本
反而更高。这个差异来自本次**候选数量不同**，不能解释成 A1 算法天然更贵，
也不能用 proposer 调用更少推断 A1 更高效。

## 7. 新的适配摩擦

DeepSeek/AgentBench 链路中，上游历史截断会留下没有可见前置 assistant
tool call 的孤立 tool message。运行层只删除这种孤立消息，并保留逐条事件。
正式记录中共发生 **72 次**清理：共享 evidence 9 次、A0 probes 11 次、A1
probes 52 次。

这项清理避免了 provider 请求失败，所以 130 个正式 episode 最终保持 0
error；但它仍是必须披露的 provider/环境适配摩擦。准确边界是“适配后运行
完整”，不是“原始 provider 接口天然无摩擦”。

## 8. 现在可以主张的结论

1. Week 4 的两个 A-slot 路径已从 adapter compatibility 进入真实 ALFWorld
   task-performance 评估。
2. A0 与 A1 各产生至少一个有 1 fix、0 regression、12/13 的候选。
3. 原生 GRASP gate 与实际 effectiveness 会发生分歧；`skillrl-003` 是一条
   完整、可审计的真实证据。
4. 完整正式运行包含 130 个 episode、0 episode error、2,608 次模型调用，
   估算成本约 $1.98665。

## 9. 仍然不能主张的结论

1. **不能说 A0 或 A1 更优。** 当前只有一个 seed；A0 只评估 1 个候选，A1
   评估 3 个候选；两边最佳候选又同为 12/13。
2. 不能把 native gate accepted 当成候选真正改善任务的充分条件。
3. 不能声称复现了完整 SkillRL。这里使用的是 **DeepSeek Flash substituted
   writer**，不是 source-faithful Azure O3；只复用了 released prompt/parser
   和 additive updater 形状。
4. 不能从 13 个 probe 任务、单 seed 推断统计显著性或跨 split 泛化。
5. 不能把 72 次 tool-history 清理隐藏在“0 error”后面。

## 10. 当前限制

- **统计限制：** 单 seed、小 probe，且同一任务的 fresh baseline 有波动。
- **预算不对称：** 1 个 A0 候选对 3 个 A1 候选，搜索机会和 probe 成本不等。
- **Provider fidelity：** A1 是 DeepSeek substituted flow；Azure O3
  source-faithful control 仍未完成。
- **Gate 解释：** 原生 adjusted score 会奖励 baseline 波动，因此必须保留
  raw fixes/regressions 和 effectiveness sensitivity。
- **环境适配：** tool-history sanitizer 是完成当前 backend 运行的必要适配层。

## 11. 下一步

### 短期：把 A-slot 结论做稳

1. 先冻结当前单-seed 结果，不覆盖现有 run。
2. 用相同协议增加 seeds，并预先规定比较量：best-of-one、matched candidate
   budget 或 all-candidate yield，不能事后挑口径。
3. 同时报告 candidate success、fix/regression、native gate、effectiveness 和
   provider-cleanup events。
4. 若获得 Azure O3 凭证，再单独做 source-faithful SkillRL control；不能用
   DeepSeek 结果替代它。

### 下一条组件边界：SkillOps maintenance

在不改变下游 D/C host 的前提下，先做 copied-library round trip，再把
GRASP/SkillRL 产生的 library 交给 SkillOps maintenance，比较 raw 与 maintained
library。这个实验将回答：一个跨论文产生的 skill library 能否再经过另一个
论文的 Lifecycle/Maintenance 组件，并继续被原 host 消费。

具体边界、长耗时命令和验收条件见
[`../01_planning/skillops_maintenance_experiment_plan_zh.md`](../01_planning/skillops_maintenance_experiment_plan_zh.md)。

## 12. 希望与导师讨论的决策

1. A-slot 后续比较是否采用 matched one-candidate budget，还是比较在固定总
   probe 预算下的有效候选产率？
2. 是否把 `native admission + fixes>0 sensitivity` 固定为后续所有 lifecycle
   报告的双口径？
3. 下一阶段是否优先验证 SkillOps 的 copied-library round trip 与 released
   maintenance primitives，而把完整论文复现明确留在代码缺失边界之外？

## 13. 口头汇报稿

“Week 4 我们只证明了两个论文组件能接到同一个 repository 和 gate，这周把
被环境阻塞的真实性能实验补完了。我们把 GRASP 的 26 个 dev 任务严格拆成
13 条生成证据和 13 条独立 probe，A0 和 A1 共享空 library、同一个 DeepSeek
writer、同一个 GRASP gate。正式运行一共 130 个 ALFWorld episode，没有
episode error。

A0 生成一个候选，最后是 12/13、一个修复、零回归。A1 生成三个候选，只有
第一个同样达到 12/13、一个修复、零回归；第二个没有修复并产生回归。第三个
尤其重要：它没有真实修复，还有两个回归，但 GRASP 原生 gate 因 baseline
波动仍然接受；我们额外的 fixes 大于零 sensitivity 把它拒绝了。这说明 gate
准入和实际效果必须分开报告。

现在不能说 A0 或 A1 更好，因为只有一个 seed，而且 A0 只有一个候选、A1
有三个，搜索预算不一样；两边最佳结果也完全相同。整体运行是 2608 次模型
调用，估算约 1.99 美元。A1 虽然 proposer 只调用一次，但三个候选带来了更高
的 probe 成本。运行中还记录了 72 次孤立 tool message 清理，这是 DeepSeek
与 AgentBench 历史格式之间的真实适配摩擦。

下一步我建议先不扩大 A-slot 结论，而是验证第二种组件边界：把跨论文生成的
library 交给 SkillOps maintenance，再让不变的检索和执行 host 消费。先做
可逆的 round trip 和 released primitive smoke，确认 ID、版本和语义不会在
维护中丢失，再决定是否值得跑长耗时的 raw-versus-maintained 性能实验。”
