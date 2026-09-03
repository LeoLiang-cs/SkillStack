# SkillStack Week 5 组会汇报提纲

## 本次希望优先确认

1. 第一轮贡献是否聚焦 **adapter-compatible lifecycle portability** 和受控
   maintenance correctness，而不强调性能提升？
2. Val 三次重复的 CI 跨过 0，是否值得消耗 held-out test？
3. 下一周期优先做 semantic maintenance，还是先加强 provider/randomness 控制？

## 1. 本周核心进展

- 补完 Week 4 阻塞的 A-slot 严格 13/13 性能闭环。
- A0/A1 各找到一个 12/13、1 fix、0 regression 的候选；不能比较谁更优。
- 使用这两个有效 skill 接入 SkillOps，完成 M1–M5：round trip、受控 merge、
  unchanged-host parity、单次 pilot 和三次 val 重复。
- 第一轮 exact-duplicate maintenance 的开发—验证—评估周期已经闭环。

## 2. 论文阅读带来的关键启发

- SkillOps 把 skill 表示为 `(P,O,A,V,F)`，并把 maintenance 与 task-time planner
  分开。
- Released `sweep()` 只覆盖部分 maintenance 行为，不能写成完整论文复现。
- GRASP Markdown 没有足够 typed semantics；第一轮采用可逆 opaque fingerprint，
  不从自然语言猜 semantic contract。
- Compatibility、maintenance correctness 和 task performance 是三个独立证据层。

## 3. 实验结果与变化

### A-slot

- 130 episodes、0 error、2,608 model calls、约 $1.98665。
- A0 最佳 12/13；A1 最佳 12/13。
- `skillrl-003` native accepted，但 fixes=0；effectiveness sensitivity 拒绝。
- A1 是 DeepSeek substituted writer，不是 Azure O3 source-faithful 复现。

### SkillOps M1–M3

- L-clean round trip bytes 完全一致；clean sweep 0 false merge。
- L-stress 4→2，只删除两个预期 clone；precision/recall=1.0。
- Recorder 与原生 GRASP selector 48/48 parity；未导入 SkillOps planner。

### SkillOps M4–M5

| Replicate | Raw | Maintained | 差值 |
|---|---:|---:|---:|
| 42 | 21/24 | 22/24 | +1 |
| 7 | 22/24 | 20/24 | −2 |
| 123 | 20/24 | 22/24 | +2 |
| **合计** | **63/72** | **64/72** | **+1** |

- 144/144 episodes、0 error、2,224 calls、约 $1.29214。
- 3 fixes、2 regressions、67 ties。
- Bootstrap 95% CI 为 [−4.17, +8.33] 个百分点，包含 0。
- 结论：没有方向稳定、可分辨的 task-performance difference。
- 去重后静态 prompt 更短，但实际调用和成本略高，不能声称成本下降。

## 4. 当前最可信的解释

- **已证实：** adapter 可逆、exact-duplicate merge 正确、下游 host 未改写。
- **未证实：** maintenance 能提升任务成功率或降低 end-to-end 成本。
- **推测：** task 17/42 的方向翻转可能来自 provider/environment 波动或 trajectory
  分叉；需逐轨迹核对。
- Seed 只控制任务顺序，没有设置 provider seed，应称三次重复运行。

## 5. 当前主要问题

1. Task 17、42 在不同重复中出现相反结果，缺少 trajectory-level 归因。
2. Task 30、48 在两个 cell、三次重复中都失败，是稳定困难任务。
3. Exact-duplicate debt 是受控 case，不代表 natural semantic debt。
4. Held-out M6 的研究问题尚未冻结；当前也没有 non-inferiority margin。

## 6. 下周计划

1. 分析 task 17、42、30、48 的选择、动作、停止状态与调用长度。
2. 冻结第一周期 advisor report 与 claim boundary。
3. 组会确认 M6 是性能确认还是安全/伤害检查，再决定是否运行。
4. 起草 `semantic_contract_v1` 的证据来源与新实验边界。

## 7. 一分钟口头版

“这周完成了两个闭环。第一，Week 4 只证明 GRASP 和 SkillRL 的 proposer 能接到
同一个 gate；这周补完严格 13/13 性能实验。两边各有一个候选达到 12/13、一个
修复、零回归，但因为只有一个 seed、候选数量也不同，不能说谁更好。原生 gate
还接受了一个 fixes 为零的候选，所以 admission 和 effectiveness 必须分开。

第二，我把这两个有效 skill 交给 SkillOps maintenance。Round trip 没有字节
变化，人工注入的两个 exact duplicate 都被正确删除，precision 和 recall 都是
1。下游仍使用原生 GRASP selector 和 evaluator。之后三次 val 重复共跑了 144
个 episode，raw 是 63/72，maintained 是 64/72，但三次差值分别是加一、减二、
加二，95% 区间跨过零。因此当前最可靠的贡献是跨论文 lifecycle 组件接入和
受控维护正确性，不是性能提升。希望组会决定：是否还值得消耗 held-out test，
以及下一周期是做 semantic maintenance，还是先解决运行波动和 provider 控制。”
