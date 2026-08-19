# SkillStack 合并导师简报（中文版）

- **当前状态：** 换执行器、换难度、factorial 与 Canonical Interface v1 全部完成。
- **一句话结论：** Executor 槽位可替换、Ceiling 稳健；Skill*存在*在预算压力下有效（三次独立实验复现），但 Skill*身份*尚未生效——retrieval × composition ≈ **近似独立**（成功率上 interaction I=0）。

## 1. 三条工作线回顾

- **换执行器**
  - 为什么：验证"执行器这个槽位能不能被 LLM 替换掉"。
  - 怎么做：把写死的确定性执行器换成**零样本 LLM ReAct**——让 LLM 自己"想一步、做一步"，其余组件（Retriever、任务、轨迹）零改动；执行器由两个 backbone 驱动：`deepseek-v4-flash` 和 `glm-4.7-flashx`，互为对照。
  - 结果：DeepSeek 连 no-skill 都 5/5（撞 Ceiling，Skill 效用测不出来）；GLM 动作格式不合法（F-15）。

- **换难度**
  - 为什么：上一步"没技能也满分"，说明 50 步预算太宽、任务太简单，Skill 有没有用**测不出来**。
  - 怎么做：加更难任务集，并把步数预算从 50 **收紧到 20**，制造一个"有压力"的区间。
  - 结果：预算压力下 Skill 开始有用（首个正信号）；同时查清 GLM 之前失败只是 prompt 缺示例（2-shot 解决），不是模型不行。

- **换问法（factorial）**
  - 为什么：光看"有没有 Skill"不够，还要问"挑 Skill 的方式"和"用 Skill 的方式"会不会互相影响。
  - 怎么做：跑第一个真正的 factorial——R1（按任务语义挑 Skill 的 Retriever，修好第一周挑错 Skill 的问题）× E1（注入编号 procedure 步骤的 Executor），9 个 pick_two × 20 步。
  - 结果：四 cell 全 5/9、control 3/9、interaction I=0 → retrieval 与 composition 近似独立；同时起草 Canonical Interface v1（规范一条 Skill 必须写清哪些字段）。

## 2. 核心发现

1. **Executor 槽位可替换**：换执行器时没动任何相邻组件（Retriever/任务/轨迹零改动），且全程带 token/成本核算。
2. **Ceiling 稳健可复现**：`deepseek-v4-flash` 零样本 ReAct 在 50 步下把 ALFWorld `valid_unseen` 打满——原 5 任务 no-skill 5/5、更难 8 任务 no-skill 8/8 = oracle 8/8。这是"环境 + backbone 配对"的负结果，不是 Skill 思路的负结果。
3. **预算压力下 Skill 有用**：因为 50 步下连 no-skill 都满分（撞 Ceiling），Skill 作用测不出，所以把预算收紧到 20 步。在 pick_two 上，oracle 用 **47 步**解完三任务、no-skill 用 **88 步**（约 2 倍效率差）；收紧后效率差转化为成功率差（no-skill 1/3 < skill-bearing 2/3）；factorial 下 control 3/9 < 所有 skill-bearing cell 5/9。
4. **GLM 可移植性归因解决**：加 2 个 few-shot 示例后 GLM 首发动作合法性升到 **97.96%**。F-15 重分类——Executor 能移植到 GLM，只要 prompt 带 few-shot；零样本失败是 prompt 耦合，不是能力上限。GLM-4.7-FlashX 是可行廉价 backbone。
5. **retrieval × composition 近似独立**：成功率 interaction I=0.0；两个因素各有小的可加性效率主效应（R1、E1 各省 ~1 步/集，b11 比 b00 便宜 18%），但无协同、无冗余。Skill 存在有效、身份未生效——20 步预算下 Executor 不依赖 Skill 文本内容。

## 3. 关键数据

### 3.1 换执行器（5 任务 × 50 步，deepseek-v4-flash）

| 条件 | 成功率 | 平均步数 | LLM 调用数 | 估算成本 |
|---|---:|---:|---:|---:|
| no_skill | **5/5** | 14.2 | 71 | $0.016 |
| random_skill | **5/5** | 20.0 | 100 | $0.025 |
| lexical | **5/5** | 21.2 | 106 | $0.028 |
| oracle | **4/5** | 26.3（成功集） | 115 | $0.025 |

- 20 个 episode **0 次非法动作**（格式合法率 100%）；唯一失败是 oracle 条件灯光任务在第 8 步过早宣布 `done`。

### 3.2 换难度：紧预算 Skill 效用（3 个 pick_two × 20 步）

| 条件 | 成功率 |
|---|---:|
| no_skill | **1/3** |
| random_skill | 2/3 |
| lexical | 2/3 |
| oracle | 2/3 |

### 3.3 换问法：factorial（9 个 pick_two × 20 步，deepseek）

| Cell | Retriever × Executor | 成功率 | 平均步数 | 成本 |
|---|---|---|---|---|
| b00 | lexical × flat ReAct | **5/9** | 16.44 | $0.0334 |
| b10 | task-semantic × flat ReAct | **5/9** | 16.00 | $0.0293 |
| b01 | lexical × structured ReAct | **5/9** | 15.56 | $0.0319 |
| b11 | task-semantic × structured ReAct | **5/9** | 15.44 | $0.0278 |
| control | no-skill × flat ReAct | **3/9** | 18.22 | $0.0326 |

| interaction 指标 | I = Y11 − Y10 − Y01 + Y00 | 解读 |
|---|---|---|
| 成功率 | **0.0** | 近似独立 |
| 平均步数 | +0.32 | 轻微次加性（~2%，噪声级） |
| 成本 | ≈ 0 | 独立 |

## 4. Gates 汇总

| Gate | 结果 |
|---|---|
| G1 format（deepseek） | 通过（0 非法动作） |
| G1 format（GLM zero-shot） | 失败 → 2-shot 解决（97.96% 合法） |
| G2 skill channel（5 任务 × 50 步） | 失败（Ceiling：5/5 = 5/5） |
| G3 swap | 通过（零相邻改动、轨迹同形 + LLM 核算字段） |
| G4 skill channel（更难集 × 50 步） | 失败（Ceiling：8/8 = 8/8） |
| G4′ skill channel（pick_two × 20 步） | 部分（no_skill 1/3 < skill-bearing 2/3，但 oracle 未胜 random） |

## 5. 当前结论

1. Executor 槽位在结构上可互换，且含完整 token/成本/延迟核算。
2. `deepseek-v4-flash` 零样本 ReAct 在 50 步下使 ALFWorld `valid_unseen` 饱和——跨两个任务集可复现的 Ceiling 发现。
3. Skill 通道效应（Skill 存在）在三个独立实验复现：确定性执行器、换难度紧预算、factorial。
4. 预算约束下 Skill 上下文可测地有帮助（pick_two no-skill 1/3 vs skill-bearing 2/3；factorial control 3/9 vs 5/9）。
5. 严格 Executor 配 2-shot prompt 可移植到 GLM（首发合法性 97.96%）。
6. 两种 Retriever × 两种 Executor，在成功率上近似独立（interaction I=0）；框架的 interaction 测度已可运行。
7. R1（task semantics + 适用性）是机制不同的第二个 Retriever，在选择层面修复了第一周的 F-01/F-02 错配。
8. Canonical Interface v1 有证据链：3 个 required 字段（`goal_operation`、`required_transformation`、`procedure`）各自要么被 ≥2 个实现需要，要么解释一个已复现失败。

## 6. 当前疑惑

1. "正确 Skill"是否真的胜过"任意 Skill 文本"？pick_two 上 oracle 未与 random 分离（都 2/3）；factorial 成功率 I=0。
2. 更好的 retrieval 或 structured 注入能否提升成功率？该预算下两者都是零效应（F-22/F-23）。
3. retrieval 与 composition 到底有没有协同/冗余？I ≈ 0 可能是分辨率限制，不是不存在。
4. 样本还太少（n=3 或 n=9，单 seed），还不能下统计结论。
5. 这个区间之外的 Skill 效用如何？还没法下一般性结论（Ceiling 会掩盖它）。

## 7. 下周目标

目前 Skill 发挥不出"内容"作用，症结在于：Skill 里写好的 **procedure** 没有被 Executor 真正当回事——现有两种注入形式（flat、lightweight structured）都偏弱（F-23）。按序推进：

1. **硬步骤约束实验（E2）**：给 Executor 加一条硬规矩——**每一步只能执行 procedure 里当前那一步规定的命令，不许自由发挥**。这是检验"步骤内容到底能不能改变结果"的最强实验，也是验证 Canonical Interface v1 里 `procedure` 字段有没有用的直接检验。
2. **确定性步骤阅读器**：做一个"老实照抄 procedure"的 Executor（重访第二周的确定性方案，但改成解析 `procedure`，而不是写死的骨架），端到端证明"机器可读的 procedure"确实能用。
3. **提高测量分辨率**：把 pick_two 从 9 个扩到 17 个、步数预算加 10 步与 30 步两档，让 interaction I 有更宽的量程，也给"正确 Skill 是否胜过随机 Skill"的比较提供统计功效。
4. 把效率（步数/token）作为与成功率并列的主指标。

## 8. 希望与导师讨论的决策

1. **要不要推进"硬步骤约束"实验（E2）？** 现在 Executor 可以自由选动作，E2 会给它套上"只能照当前 procedure 走"的限制——这是唯一可能真正拉动成功率、也最能验证"Skill 里写好的步骤有没有约束力"的实验。
2. **Canonical Interface v1 现在冻结，还是等 E2 结果再定？** 也就是：规定"一条 Skill 必须写清哪些字段"的规范，是现在拍板定稿，还是先等 E2 告诉我们 `procedure` 字段的最终形态再定。
3. **backbone 主力模型用哪个？** 继续用 DeepSeek，还是切到 **GLM-4.7-FlashX + 2-shot**（2-shot 指在 prompt 里先给两个示例；它已验证能正确输出动作、可能更便宜）？
4. **论文框架够不够？** 当前实证核心——Executor 替换、retrieval × composition 独立性、Ceiling 发现、GLM 可移植性归因、Canonical Interface v1——是否足够，还是必须等到 E2 的成功率结果？

## 9. 四页汇报结构

1. **替换 + Ceiling**：Executor 替换成功；DeepSeek 使 ALFWorld 饱和（no-skill 8/8）。
2. **Skill 信号**：pick_two 效率 47 vs 88 步 + 20 步成功率分裂 1/3 vs 2/3；factorial control 3/9 vs 5/9、I=0。
3. **可移植性 + Canonical Interface v1**：GLM 2-shot → 97.96% 合法性；3 个 required 字段及其证据链。
4. **决策**：硬步骤约束 / 冻结 Canonical Interface v1 / backbone 选择 / 论文框架。

## 10. 口头汇报稿

"这三周我把 Executor 从确定性换成了真正的 LLM ReAct，其他组件一个没动——替换本身成功，轨迹里有完整的 token 和成本核算。结果撞上一个硬 Ceiling：DeepSeek 零样本就能解完 ALFWorld——原五个任务和八任务更难集，no-skill 都打到 8/8，所以 50 步下 Skill 效用测不出来。

但更难的 pick_two 给出了第一个真信号：oracle Skill 47 步解完，no-skill 要 88 步；因为 50 步下连没技能都满分、技能作用测不出，我把预算收紧到 20 步——这一压，no-skill 掉到 1/3，所有 skill-bearing 条件都是 2/3。GLM 的失败也查明是 prompt 耦合、不是模型上限——加两个示例后动作合法性跳到 98%。

这一周我又跑了第一个真正的 factorial：两个 Retriever、两个 Executor，四个 cell 加一个 no-skill 对照，九个 pick_two、二十步预算。答案很干净：四个 cell 全部 5/9、对照 3/9、interaction 恰好为零——所以在这个分辨率下，retrieval 与 composition 近似独立。Skill 通道是真的，但它的*内容*还没有被绑定：no-skill 对照仍然输，但'正确 Skill 胜过随机 Skill'还看不到。

我还起草了第一版 Canonical Interface v1：三个 required 字段——目标操作、必需变换、有序 procedure 步骤——每个都有实现证据和失败台账支撑。

下一步真正可能移动成功率的实验是硬步骤约束：让 Executor 只能执行当前 procedure 那一步的动作。如果步骤内容在那里改变结果，Canonical Interface v1 就闭环了；否则我们就拿到一个扎实的独立性结果加 Ceiling 发现，足够写进论文。"

---

- Friction Ledger：F-15…F-21 见 [`w3_friction_ledger.md`](../week3/w3_friction_ledger.md)；F-22/F-23 见 `w3_2_friction_ledger.md`。
- Advisor Brief：第三/四次见 [`w3_advisor_brief_zh.md`](../week3/w3_advisor_brief_zh.md)、[`w3_advisor_brief_4_zh.md`](../week3/w3_advisor_brief_4_zh.md)；第五次见 `w3_2_advisor_brief_zh.md`。
