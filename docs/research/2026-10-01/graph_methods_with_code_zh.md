# 有代码的图组合 / 图进化方法：检索与核实

日期：2026-10-01 ｜ 使用 skill：paper-search
方法：paper-search 检索 11 组查询（arXiv，2024–2026），读 PDF 找代码链接，再用 GitHub API 核实许可证、更新时间、目录和 README（没有 clone、没有运行）。

## 1. 结论

缺口基本补上了。每个槽位现在都有 **≥2 个带代码的 graph 实现**，组件来源论文合计约 15 篇，达到之前估计的主会规模（8–12 篇）。

最重要的新发现是 **SkillDAG**（arXiv 2606.03056，MIT，ALFWorld + SkillsBench）：自进化的类型化技能图，agent 在执行后提出或修改边，每次提交都检查无环性和无矛盾性，并且可以回滚。它可以直接作为**图进化**槽位的主力。

## 2. 图进化（A 槽位）

| 方法 | 代码 | 许可证 | ALFWorld | 机制 | 用法 |
|---|---|---|---|---|---|
| **SkillDAG**（2606.03056） | ✅ `Ericbai06/SkillDAG`（★54，2026-07） | MIT | ✅ 有 `benchmarks/` 集成 | agent 用 `propose-edge`/`edit-edge` 提交有执行证据的边；无环 + 无矛盾检查；append-only 日志支持回滚 | **主力，faithful** |
| **G-Memory**（2506.07398） | ✅ `bingreeky/GMemory`（★280） | ❌ 无 | ✅ `--task alfworld` | 三层图记忆（insight / query / interaction graph），跨任务演化 | 第二个，需要从多智能体改成单智能体（adapted）。无许可证：只能作为外部依赖固定 commit 调用，不能并入我们的仓库 |
| GraphSkillAA（2609.20455） | ✅ `Ziqiao-Shang/SkillAA`（★1，2026-09） | ❌ 无 | ❌ 只有 SearchQA、数学、DocVQA | 一张图同时用于选择、执行、失败归因、定点修改、回归测试和回滚 | 机制最接近 EvoSkillGraph 的 Corrects 边。需要适配 ALFWorld；很新、星少，代码成熟度待验证 |
| PlugMem | ✅ `TIMAN-group/PlugMem` | Apache-2.0 | ❌ WebArena / QA | procedural 记忆图 + 演化 | 备选 |
| A-MEM（2502.12110） | ✅ `WujiangXu/A-mem`（★976） | MIT | ❌ QA | Zettelkasten 式链接生成 + 记忆演化 | 备选 |
| AFlow、GPTSwarm | ✅（MIT） | MIT | ❌ QA / 代码 | 工作流图的搜索和优化 | 粒度是工作流而不是技能，改造成本高，暂不用 |
| SE-GoS（2609.08228）、HyperSkill（2608.16114）、MACLA（2512.18950） | ❌ 没找到 | — | 有的有 | — | 只能引用 |

## 3. 图组合 / 执行（C 槽位）

| 方法 | 代码 | 许可证 | ALFWorld | 机制 | 用法 |
|---|---|---|---|---|---|
| **ADaPT**（2311.05772） | ✅ `archiki/ADaPT`（★95） | MIT | ✅（另有 WebShop、TextCraft） | 执行失败时才递归拆分子任务，形成**树状**组合 | **主力 1，faithful**。注意它是树，不是一般的 DAG |
| **LLMCompiler**（2312.04511，ICML'24） | ✅ `SqueezeAILab/LLMCompiler`（★1890） | MIT | ❌ 函数调用任务 | 规划器输出任务 **DAG**，按依赖并行执行 | **主力 2，adapted**：把技能当成"函数"，用它的 DAG 规划器做组合 |
| GraSP（2604.17870） | ❌ | — | 论文有 | DAG 编译 + 节点验证 + 局部修复 | 自己复现，拆成三档（只有图 / 加验证 / 加修复） |
| Agint、HyperAgent、SkillWeaver（2606.18051）、SkillComposer | ❌ 没找到可用代码 | — | — | — | 只能引用 |

## 4. 图检索（D 槽位，顺带多找到两个）

| 方法 | 代码 | 许可证 | ALFWorld | 备注 |
|---|---|---|---|---|
| Graph-of-Skills | ✅ | MIT | ✅ | 已核实；同一代码库里有 `gos` 和 `vector` 两种模式 |
| **CaSKG**（2608.25500） | ✅ `ZhiyuanLi218/Caskg` | ❌ 无 | ✅ ALFWorld ID-140 + ScienceWorld | 反事实因果技能图；README 报告比 GoS 高约 7 个点 |
| SkillDAG 的 `search` | ✅ | MIT | ✅ | 返回向量匹配 + 类型化邻居 + 冲突信号 |

## 5. Flat 对照（ALFWorld 上有代码的）

ExpeL（Apache-2.0，经验 insight，flat 进化）、AutoManual（无许可证，规则手册，flat 进化）、Agent Workflow Memory（Apache-2.0，flat workflow，原本是 web 任务）、SkillRL（MIT）、仓库里的 GRASP 提案器和 SkillOps，再加 ReAct 和 GoS 的 `vector` 模式。

## 6. 更新后的槽位配对

| 槽位 | Flat | Graph（主力） | Graph（第二） |
|---|---|---|---|
| 底座：存储 | 静态列表 / SkillBank | SkillNet 关系图 | — |
| D 检索 | GoS `vector`、lexical | GoS `gos` | CaSKG、SkillDAG `search` |
| C 组合 | ReAct | ADaPT（树） | LLMCompiler（DAG，adapted）、GraSP 复现 |
| A 进化 | SkillRL、ExpeL、GRASP 提案器 | SkillDAG | G-Memory（adapted） |

**数量**：有代码的组件来源论文约 15 篇（GoS、CaSKG、SkillDAG、ADaPT、LLMCompiler、G-Memory、GraphSkillAA、SkillNet、SkillRL、ExpeL、AutoManual、AWM、PlugMem、A-MEM，加上仓库已有的 GRASP 提案器和 SkillOps），超过之前估的主会门槛（8–12 篇）。

## 7. 需要注意的点

1. **SkillDAG 把检索和进化绑在一起**：它的图既被 `search` 读，又被 `propose-edge` 写。这和"槽位可以独立替换"的假设冲突。替换时一定会碰到隐藏依赖，正好是 BLM 诊断的用武之地，也可能是第一个"由发现引出的创新点"。
2. **无许可证的仓库**（CaSKG、G-Memory、GraphSkillAA、AutoManual）：做研究实验可以用，但只能像现在的 GRASP 一样，作为外部仓库固定 commit 调用，不能复制进我们准备开源的仓库。需要的话可以发邮件问作者要许可证。
3. **已有的"图会伤害"证据**：GoS 的 README 里写着，把图传播改成正向，结果会"比完全不用图还差"。这说明 graph vs flat 不是单调的，benchmark 很可能做出有意思的结论。
4. 以上全部只核实到"仓库存在、有 ALFWorld 入口"，**没有实际跑通**。真正能否复现，要在 pilot 里逐个验证。

## 8. 建议下一步

1. 先 clone 三个 MIT + ALFWorld 的主力仓库（GoS、SkillDAG、ADaPT），在本地各跑通一个 ALFWorld episode，确认能复现。
2. 用这三个仓库加 ReAct 搭第一个 2×2 pilot（检索 × 组合）。
