# Graph Skill 模块化 Benchmark：撞车检查 + SkillStack 去留盘点

日期：2026-10-01 ｜ 使用 skill：scoop-check（内含 paper-search）
检索：5 组查询，arXiv + Crossref，共 79 篇（Semantic Scholar、OpenReview 本次限流，覆盖不完整）。精读全文 4 篇：2606.24775、2603.04448、2608.18104、2410.06153；另外复核了仓库 `papers/` 里已有的 MAFBench（2602.03128）和 Dynamic Agent Skills（2607.10113）。

---

## Part 1：撞车检查

### Verdict：Level 3 — Medium Overlap（中度重叠，可以做）

"拆模块 + 受控对照"这个**研究范式**已经有人用过，但用在别的领域。在 **skill agent** 上逐槽位做 **flat vs graph**、并测**跨模块交互**的工作没有找到。

### Delta（论文里可用的一句话）

> 不同于 *Are We Ready For An Agent-Native Memory System?* 在对话记忆系统内部每次只改一个模块、用 QA 指标评测，我们在 skill agent 的存储、检索、组合、进化四个槽位上，把来自不同已发表系统的 flat 与 graph 实现交叉替换、做析因实验，在交互式环境里测量"图化"的主效应和跨模块交互，并用边界恢复诊断替换损失的来源。

### 最接近的工作

| 论文 | 做了什么 | 重合轴 | 对我们的意义 |
|---|---|---|---|
| **Are We Ready For An Agent-Native Memory System?**（arXiv 2606.24775，全文） | 把 agent memory 拆成 4 模块（表示存储、抽取、检索路由、维护），评测 12 个系统；Section 5 "每次只改一个模块"生成受控变体 | 问题框架 ✔、机制部分 ✔；领域 ✘（对话记忆 / QA）；关键洞见部分 | **最近的范式先例**，必须引用。它只做单模块消融、不做跨系统交叉组合和交互效应。它的发现之一"graph-based 方法在知识更新上最可靠"可以作为我们的假设来源 |
| **MAFBench**（arXiv 2602.03128，仓库已存） | 多智能体框架的架构分类法 + 统一执行管线下的受控对比 | 问题框架 ✔；领域 ✘（多智能体框架） | 第二个范式先例 |
| **SkillNet / SkillNet-Gym**（arXiv 2603.04448，全文） | 技能本体 + 关系图；Gym 是从技能图随机游走合成的**任务数据集**，测检索、使用、组合 | 领域 ✔；机制 ✘ | 不是受控对照，是任务集。可以当我们的环境之一，或者当 graph 存储槽位的实现 |
| **Self-Evolving Agents as Dynamic Graph Transformation**（arXiv 2608.18104，综述，全文） | 把自进化 agent 统一为动态图变换；提出图感知评测协议（support-subgraph accuracy、counterfactual rewrite locality），Challenge I 就是 benchmark | 问题框架部分 ✔ | 没有实验，但它**点名要这类 benchmark**。它的 rewrite locality 指标可以直接拿来评测进化槽位。要盯紧作者后续工作 |
| **AgentSquare**（arXiv 2410.06153，全文） | 规划、推理、工具、记忆 4 模块统一 IO，做模块进化和重组**搜索** | 机制部分 ✔ | 目标是搜最优组合，不是归因；没有 flat vs graph |
| Graph-of-Skills（2604.05333）、GoSkills（2605.06978）、GraSP（2604.17870）、SkillNet | 各自把**一个**槽位图化，并和 flat 做整机比较 | 领域 ✔ | 这些就是我们 graph 槽位的候选实现 |
| Dynamic Agent Skills（2607.10113，TMLR 综述） | 8 阶段技能生命周期架构 | 框架 | 可以用来论证槽位划分的合理性 |

### 需要警惕

1. 2606.24775 的作者组（OpenDataBox）有可能把同样的方法搬到 skill 上，要尽快做出东西。
2. 审稿人可能会说"这只是把 memory benchmark 的方法套到 skill 上"。我们的区别必须落在三件 memory 研究没做的事上：**跨系统交叉组合**、**交互效应**、**边界诊断（BLM）**。

---

## Part 2：盘点前的一个重要更正

- **仓库里的 "GRASP" 不是图方法。** `src/skillstack/experiments/grasp_source.py` 固定的是 *Gated Regression-Aware Skill Proposer*，属于进化（A）槽位里的 **flat** 提案器。图组合方法 **GraSP**（arXiv 2604.17870）只有一张算法卡（`reports/week4/02_paper_analysis/algorithm_cards/grasp.md`），状态是 blocked：源码没有核实。之前项目摘要里"用 GRASP/SkillRL 适配器"的说法把两者混在了一起。
- **仓库里目前没有任何 graph 实现。** 全仓库搜不到 DAG、拓扑排序或图库依赖；`library.py` 加载的是扁平的 Markdown 技能列表。
- **已经有一个 2×2 析因雏形。** `scripts/run_w3_2_factorial.py` 做了检索器 × 执行器的析因实验，交互项 I = Y11 − Y10 − Y01 + Y00，当时成功率上 I ≈ 0。这正是新 benchmark 的分析方法，也提示交互可能很小，需要足够的 seed 数。

---

## Part 3：去留表

### A. 保留，直接用

| 部分 | 位置 | 在新 benchmark 里的角色 |
|---|---|---|
| R-A-D-C-L 责任框架 | `docs/development/architecture_and_extensions.md`、`reports/week3_2/w3_2_rq1_assessment.md` | 直接成为槽位划分：R=存储、D=检索、C=组合、A=进化，L 并入 A 或作为第 5 槽位 |
| Trace / manifest / summary 体系 | `src/skillstack/tracing/jsonl.py` | 每个析因 cell 的原始证据，可重算 |
| LLM 多后端客户端 | `src/skillstack/llm/client.py` | 跨 backbone 实验 |
| 环境 | `src/skillstack/environments/alfworld_text.py`、`fixture.py` | ALFWorld 主环境，fixture 用于零成本测试 |
| Flat 检索器 + 对照 | `src/skillstack/retrieval/`（lexical、task_semantic；no_skill、random、oracle） | D 槽位的 flat 实现和上下界对照 |
| Flat 执行器 | `src/skillstack/execution/react.py`、`skillplan.py`、`recorded.py` | C 槽位的 flat 实现；recorded 用于测试 |
| 固定 commit 的外部源码封装 | `experiments/skillrl_source.py`、`grasp_source.py`、`skillops_*.py` | A/L 槽位的 flat 实现（SkillRL 更新器、GRASP 提案器、SkillOps 维护），保真度标注照用 |
| 任务集与划分 | `configs/p0_tasks_*.json`、`experiments/splits.py` | 任务清单 |
| BLM 核心 + R1 校准 | `src/skillstack/blm.py`、`experiments/blm_calibration.py`、`report/week7/r1_*` | 降级为诊断工具；R1 校准证据仍然有效 |
| 论文分析资产 | `reports/week4/02_paper_analysis/`（算法卡、architecture crosswalk）、`reports/week4/04_matrices/` | 选择 graph 槽位实现时的起点 |
| 质量门禁与测试 | `tests/`（34 个文件）、`scripts/run_core_gate.py`、CI | 保持，防止重构破坏实验正确性 |
| 历史报告与原始证据 | `reports/week1–6`、`report/week7–8` | 保留不改（项目规则：原始证据只追加），作为 pilot 证据 |

### B. 需要重构

| 部分 | 现状 | 改成什么 | 例子 |
|---|---|---|---|
| **技能表示** | `library.py` 只有扁平 Markdown 列表 | 增加图表示（节点、前置/后置条件、依赖边），flat 列表作为它的一种退化视图 | 同一批 ALFWorld 技能既能以列表喂给 lexical 检索，也能以 DAG 喂给 GraSP 式组合 |
| **接口** | `docs/original/canonical_interface_v1.md` 只有 flat 字段 | v2 加入图字段（preconditions、effects、edges）。仍然坚持"实现先行、接口后归纳"的规则 | `requires` 边只有在 ≥2 个 graph 实现都需要时才进入接口 |
| **适配器拓扑** | 6 个两两适配器（skillrl→grasp、grasp→proposal…），组合数 N² | 改成"每个实现 ↔ 统一接口"的星形结构，任意槽位组合都能拼 | 加一个 GoS 检索器，只写 1 个适配器，而不是和每个执行器各写一个 |
| **实验脚本** | 每周一个脚本：`run_w2_*`、`run_w3_*`、`run_w4_*`、`run_w5_*`、`run_w6_*`（共 30 个脚本） | 一个通用析因 runner + 配置矩阵（槽位 × 实现 × 环境 × backbone × seed），支持断点续跑 | `configs/factorial/v1.yaml` 列出 2⁴ 个 cell，runner 逐 cell 执行并写 trace |
| **析因分析** | `summarize_w3_2_factorial.py` 只支持 2×2 | 推广到 2^k 主效应、二阶交互，加置信区间 | 输出"图检索主效应 +6pp [2, 10]；检索×组合交互 +4pp [−1, 9]" |
| **BLM 自然案例** | `experiments/blm_natural.py` 绑死在 Structured ReAct 的首次交接 | 变成槽位无关的"替换损失诊断"，只在某个 cell 显著掉分时触发 | flat 检索 + GraSP 组合比全 graph 低 15pp 时，自动对该边界跑 BLM |
| **确定性假设** | 依赖 temperature 0 加精确重放 | runner 加入重复 seed 和噪声地板对照 | 每个 cell 跑 ≥5 seed，no-op 对照估噪声 |
| **主计划** | `docs/plan/skillstack_research_master_plan_v4_zh.md` 以 BLM 为主线 | 写 v5：benchmark 主线，BLM 降为诊断 | 待你确认方向后再写 |

### C. 删除或归档（建议移到 `archive/`，不做硬删除）

| 部分 | 理由 |
|---|---|
| 发布工程：`src/skillstack/release.py`、`docs/open_source/*`、`scripts/check_package_install.py`、`check_fresh_clone.py`、`check_public_repo.py`、wheel/sdist 验收门禁 | 开源整理已推迟到论文之后（P1）。现在每次改动都要过这些门禁，拖慢实验。先冻结，开源时再恢复 |
| 一次性脚本：`run_w3d_glm_2shot_probe.py`、`benchmark_llm_backends.py`、`summarize_w2_pilot.py`、`run_p0_*`、`validate_*` 等 | 被通用 runner 取代。保留在 archive 里，供复现历史报告 |
| 旧计划：`docs/plan/` 下的 g0/g1、v2/v3 计划、r1_0x 清单、backlog v3 | 已完成或被取代，留着会误导新开的 thread |
| BLM 主论文卡片：`docs/final_cards/idea.*` | 主线已经换了；归档，作为 BLM 诊断章节的素材 |
| `docs/scoop_ check/`（目录名里有空格） | 是之前 skill 运行留下的中间日志，不是项目文档 |
| R2 live 单独运行（`scripts/run_blm_natural.py run`） | 不再作为独立里程碑；并入 benchmark 的诊断环节 |
| `.agents/skills/`（131 个文件，Codex 格式的研究 skill 副本） | 和本机已装的 skill 重复，不属于研究代码。**这一项要你确认**，可能有别的用途 |

### D. 新增（现在完全没有的）

1. 每个槽位至少一个 **graph 实现**：存储（SkillNet 式关系图）、检索（Graph-of-Skills 或 GoSkills）、组合（GraSP）、进化（Corrects 边 / 图重写）。第一步是核实这几篇的**代码能不能拿到**，决定 faithful 还是 adapted。
2. 第二个环境：SkillsBench 或 SkillNet-Gym（GoS、GoSkills 都用了 SkillsBench，便于和原论文对齐）。
3. 进化槽位的图感知指标：可以直接借用综述的 counterfactual rewrite locality。

---

## Part 4：建议顺序

1. 核实 graph 实现的代码可得性（GraSP、GoS、GoSkills、SkillNet），确定每个槽位的 flat/graph 配对。
2. 归档 C 类内容，冻结发布门禁。
3. 重构技能表示、适配器拓扑和通用析因 runner（B 类前四项）。
4. 先跑 3 槽位 × 2 变体 = 8 个 cell 的小规模 pilot，用 fixture 加少量 ALFWorld 任务。
5. 再扩到 4 槽位、2 个环境、2 个 backbone。
