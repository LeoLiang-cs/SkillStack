# 代码可得性核实 + 槽位配对 + 顶会需要的对比规模

日期：2026-10-01 ｜ 方法：读论文 PDF 找链接 → GitHub API 查仓库（许可证、最近更新、目录、README、ALFWorld 入口代码）。没有 clone，没有运行。

## 1. 四个目标系统的代码情况

| 系统 | 代码 | 许可证 / 活跃度 | ALFWorld 支持 | 能做哪个槽位 | 结论 |
|---|---|---|---|---|---|
| **Graph-of-Skills (GoS)**，arXiv 2604.05333 | ✅ `davidliuk/graph-of-skills`（★216） | MIT，2026-08 仍在更新 | ✅ `evaluation/alfworld_run.py`，同一套代码内置 4 种模式：`gos`（图）、`vector`（扁平向量）、`all_full`（全量注入）、`none` | **检索** | **最理想的一对**：flat 和 graph 在同一个代码库、同一个 agent 里，只差检索方式，天然受控 |
| **SkillNet**，arXiv 2603.04448 | ✅ `zjunlp/SkillNet`（★1371） | MIT，2026-09 仍在更新 | ✅ `experiments/alfworld_run.py`（另有 WebShop、ScienceWorld） | **存储/表示**（`skillnet analyze` 生成 `compose_with`、`similar_to` 等关系图） | 可用。**但我读了它的 ALFWorld 实验代码（`experiments/src/skill.py`，157 行），里面没有用到关系图**，只做 LLM 检索 + 生成步骤。也就是说论文里 ALFWorld "+40%" 很可能不是图带来的（这是读代码推断的，没跑过） |
| **GraSP**，arXiv 2604.17870（腾讯） | ❌ 论文没给链接；搜了腾讯 org 和作者 GitHub 都没有 | — | 论文里有 ALFWorld 结果 | **组合/执行** | 只能按论文**自己复现**，标为 adapted。论文 30 页、24 张表，细节相对多 |
| **GoSkills**，arXiv 2605.06978 | ❌ 论文只链接了 agentskills 规范，没有自己的仓库；GitHub 上搜不到 | — | 论文里有 ALFWorld 结果 | 检索 | 暂时放弃；检索槽位已经有 GoS |

### 顺带核实的其他候选

| 系统 | 代码 | 能做哪个槽位 | 备注 |
|---|---|---|---|
| SkillRL（2602.08234） | ✅ `aiming-lab/SkillRL`，MIT | 进化（flat）、存储（flat SkillBank） | 仓库已经固定了它的 updater（`experiments/skillrl_source.py`）；完整 RL 训练成本高 |
| PlugMem | ✅ `TIMAN-group/PlugMem`，Apache-2.0 | 存储 / 进化（graph） | 记忆图里有 procedural 节点，支持图的更新和进化；但只在 WebArena、LongMemEval、HotpotQA 上做过，需要适配 ALFWorld |
| GRASP 提案器（仓库已有） | ✅ 已固定 commit | 进化（flat） | 注意这不是 GraSP 图方法 |
| SkillOps（仓库已有） | ✅ 已固定 commit | 生命周期（flat） | |
| SkillHone（腾讯） | ✅ `Tencent/SkillHone` | 进化（flat） | 2026-09 仍在更新，可作第二个 flat 进化实现 |
| R3-Skill、Skills Know Their Neighbors（腾讯） | ✅ | 检索（flat） | 可作额外的 flat 检索器 |
| AgentSquare | ✅ 但**没有 license** | 模块搜索 | 只能引用和对比，不能把代码并入仓库 |

## 2. 槽位配对建议

**一个设计上的调整：把"存储"当作共享底座，而不是独立槽位。** 存储结构本身不改变行为，只有检索或组合去读它时才起作用。所以统一用 SkillNet 的关系图建一份图库，flat 视图就是"去掉边"。这样真正做对照的是 3 个行为槽位，2³ = 8 个 cell，比 4 槽位 16 个 cell 更省，也更好解释。

| 槽位 | Flat 实现 | Graph 实现 | 保真度 | 风险 |
|---|---|---|---|---|
| 底座：存储 | 静态 Markdown 列表 / SkillRL SkillBank | SkillNet 关系图（`skillnet analyze`） | faithful | 低 |
| **D 检索** | GoS `vector` 模式；仓库的 lexical、task_semantic | GoS `gos` 模式 | faithful（同一代码库） | **低**，可以最先做 |
| **C 组合/执行** | ReAct + 技能注入（仓库 `react.py`） | GraSP 复现：DAG 编译 + 节点验证 + 局部修复 | adapted | **高**，没有官方代码 |
| **A 进化** | SkillRL updater、GRASP 提案器（仓库已有） | 没有现成的 ALFWorld 代码。候选：PlugMem 图进化（适配）、EvoSkillGraph 的 Corrects 边（自己实现） | adapted / 自研 | **高**，但这正是"由发现引出新方法"最可能落地的槽位 |

**GraSP 复现时顺手拆成三档：** 只有图、图 + 节点验证、图 + 验证 + 修复。这样可以回答 GraSP 论文没回答的问题：+19 分里有多少来自"图"本身。例子：如果"只有图"只比 flat 高 2 分，加上验证后高 15 分，那么结论就是"收益主要来自验证，不是图"。这本身就是一个有分量的发现。

**建议顺序：** 先做 D 槽位（GoS 的 gos 对比 vector，一周内能有 pilot 数据）→ 复现 GraSP（C 槽位）→ 最后做 A 槽位。

## 3. 顶会需要多少篇论文参与比较

参照同类研究（Agent-Native Memory 评测了 12 个系统；MAFBench 对比了多个框架；GraSP 自己比了 ReAct、Reflexion、ExpeL 和 flat skill 4 个基线、8 个 backbone、4 个环境），我的判断如下。这是根据可比论文推断的经验值，不是硬性规则。

| 目标 | 组件来源（不同论文） | 环境 | Backbone | 其他 |
|---|---|---|---|---|
| Workshop | 3–4 篇 | 1 个 | 1–2 个 | 单槽位对照即可 |
| Findings / D&B track | 6–8 篇，每个槽位 ≥1 对 flat/graph | 2 个 | 2–3 个 | 交互效应 + 置信区间 |
| **NeurIPS/ICLR/ICML 主会** | **8–12 篇**，每个槽位最好 ≥2 个 graph 和 ≥2 个 flat 实现 | **≥3 个**（ALFWorld + SkillsBench/WebShop/ScienceWorld） | **≥3 个**（至少 1 个本地开源模型，保证可复现） | 再加 4–5 个整机基线（ReAct、Reflexion、ExpeL、SkillRL、GraSP 报告值），由发现引出的方法，40–60 篇相关工作引用 |

**按现在核实到的情况：** 有可用代码的组件来源约 8 篇（GoS、SkillNet、SkillRL、PlugMem、GRASP 提案器、SkillOps、SkillHone、R3-Skill）。但 **graph 一侧明显偏少**：图检索只有 GoS 一个，图组合 0 个（要复现 GraSP），图进化 0 个。要达到主会规模，主要缺口是**每个槽位再补一个 graph 实现**。下一步应该专门搜一轮"有代码的图组合 / 图进化方法"。
