# 边界负载图：用差异化原子恢复检验声明的技能接口

**方法名称：** Boundary Load Mapping (BLM)

## 研究动机
模块化 LLM agent 研究形成了一种工作习惯：它悄悄把声称要测量的量条件化掉了。任何评估只要在移植异构实现之前先声明接口，就可能把本来要检测的不兼容吸收掉，因为看起来可以互换的组件，可能依赖不同的隐式状态、适用性、证据、失败与更新语义。本工作针对的问题就是 schema-first 移植：边界在测量之前就被写好，于是 swap 之后结果变了，也没法归因到实现质量、接收方 stack 的兼容性、还是相邻模块的交互。

最接近的几篇工作都体现了这个模式。AgentSquare (arxiv:2410.06153v3) 只有先把规划、推理、工具使用和记忆模块装进同一个统一的四段式边界，才能执行重组，然后在这个边界内搜索 1,050 种组合。SkCC (arxiv:2605.03353v4) 把技能编译进 typed IR 之后就认证跨框架可移植性，却从不拿接收方的行为检验这个 IR 的语义完整性。GraSP (arxiv:2604.17870v1) 允许在 precondition-effect DAG 内做替换，但直接相信声明的契约覆盖了下游真正需要的依赖。SkillAlign (arxiv:2609.07255v1) 只改变暴露形式、把实现轴固定不动，跨配对的依赖因此从不进入它的设计。这些系统里没有任何一个测量过：接收方实际消费了哪些未声明的依赖，其中哪些决定了结果。

本工作把锚点场景当作这类问题的主实例：把 GRASP-proposer 和 SkillRL-updater 组件移植进非原生的 SkillStack 接收方，跑在两个冻结的 ALFWorld 任务清单上，声明的 schema 固定在 `docs/canonical_interface_v1.md`。方法不把语义规整进统一边界，而是测量已经存在的边界：普查接收方在读取点消费的每个原子，再逐个恢复原子，用环境 oracle 打分。问题不再是 swap 能不能用，而是已声明的接口覆盖——而不是行为——是不是可移植性的承重轴，答案则变成每个声明边界上一条可证伪的完整性证书。

这个 gap 现在可解，是因为三件东西第一次凑齐，而相邻工作都没有组装它们：一个不依赖被评估方的环境 oracle（ALFWorld 的 goal predicate）；temperature-0 解码下保存状态的 replay，让逐原子干预完全可复现；以及 SkillStack 的 JSONL tracer 加 typed registry，让每个 channel 都能构造出 canonical 替代值。缺的那台仪器——用 oracle 打分的逐原子 presence 探针——现在可以由这三件东西搭出来。

之前的工作都停在声明边界上，没有闭合它：有的搜索目标活在一个固定抽象内部；有的证书定义在编译产物上，而不是实测的接收方行为上；有的相信声明的契约却不检验它们；有的把移植轴固定不动——没有一家的测量原语能暴露被声明边界过滤掉的依赖。gap 闭合之后，报告组件排名的论文就能说清收益依赖哪些边界原子，未披露的原生配对从混淆变量变成显式声明的产物；GraSP 这类替换机制和 SkCC 这类编译流水线得到一个测量目标——经 oracle 认证的承重覆盖——声明的契约和 IR 完整性可以对照它被检验，而不是被假定；互换性声明也变成按声明边界可证伪，而不是按整个系统。

## 方法
### M1_background
*探针所依附的冻结测量基础：不可变的 cell manifest 与声明的 schema 基线、边界原子 census 插桩、确定性 replay lattice 上的原生与 crossed cell 运行、canonical 替代值的 typed registry。*

1. 把实验依赖的一切锁进一份不可变的 manifest 文件：两份任务清单 `configs/p0_tasks_picktwo9.json` 与 `configs/p0_tasks_hard.json`、预先注册的 seed 列表(每行一个整数，任何运行开始前固定)、GRASP-proposer 与 SkillRL-updater 两个 A-slot 变体的确切源码 commit 编号(各带一个 fidelity 标签，faithful 表示与论文发布的实现一致，adapted 表示有改动)、接收方与邻居的配置、prompt、budget，以及从 `docs/canonical_interface_v1.md` 一次性提取的机器可读声明表(该接口文档正式声明的每个 (channel, key) 及其声明的取值范围)。manifest 以 JSON(JavaScript Object Notation)文件存储，条目按固定顺序排列，文件内记录其内容的 SHA-256 哈希(一种标准加密指纹)；之后任何对象被改动都会让哈希对不上，所有下游结果作废。这个对象定义了冻结的运行总体，以及后续步骤判定 declaredness 所对照的官方声明接口。
   - _为什么：_ 所有下游效应只有在一个冻结的有限总体上才是精确的，所以 declaredness 判定和 swap delta 需要一个固定的参照对象。
2. 扩展 `src/skillstack/tracing/jsonl.py`，让接收方在 adapter 的每个显式读取点上每消费一次，就向该次运行的 census 文件追加一条原子记录。每条记录是 JSON 格式的一行，字段固定：递增的 atom 编号、run 与 cell 标识、task 与 seed、episode 步数、读取发生的代码位置、被读取的 channel 与 key、按原样记录的值(附类型标签)、读取位置(含该 key 的第几次读取，以便之后的重放能精确对准这次读取)，以及 event class——恰好是七类之一：raw_read、default、drop、rejection、no-op、fallback、version。census 文件只追加：逐行写入、绝不修改，运行结束后计算哈希。记录发生在消费的那一刻、任何转换之前，所以 census 记的是接收方实际消费了什么，而不是生产方声称提供了什么。
   - _为什么：_ 负载图定义在接收方实际消费的东西上，而不是生产方声明的东西上，所以 census 用观察到的消费取代了对 schema 的信任。
3. 把 manifest 里冻结的 cell 网格全部跑一遍。一个 cell 是这几个因素的组合：插在 A-slot 里的是哪个变体、消费它的是哪个接收方、邻居、task、seed。每个变体各跑两种 cell：在自家 stack 里的原生 cell，以及移植进另一个 stack 的 A-slot、adapter 保持不动的 crossed cell；两种 cell 的接收方、邻居、task、seed 完全一致，唯一变化是 A-slot 的源码。所有 cell 都用贪心解码(temperature 0，每一步只取概率最高的下一个 token)，随机数发生器(Random Number Generator, RNG)的种子全部固定；重放网格就是每个 cell 的 manifest seed $\times  8$ 次重放$R_{rep} = 8$，每次重放从同一份保存的初始状态重新开始。保存完整的重放轨迹、episode 完成记录，以及 ALFWorld 内置的是/否目标判定；每个 seed 的 goal success 是该 seed 8 次二值目标判定的平均。每个 (receiver, neighbor) cell 的 swap delta 按 seed 配对平均：(原生 cell 的每 seed 成功率 $- $ crossed cell 的每 seed 成功率)，为正表示移植损失了目标成功率。
   - _为什么：_ 让 swap delta 和每个逐原子效应落在同一条 replay lattice 上，它们才相互可比，不会被解码噪声混淆。
4. 为每个 channel 建立替代值 z 的注册表。候选值来自三处：逻辑取反(把真换成假、假换成真)，但只有该 channel 现有的 parser 接受取反后的值才算；第1步（把实验依赖的一切锁进一份不可...） 声明表为该 key 声明的每一个 enum 成员；以及对象类 channel 上，保存在游戏状态里同类型的其他对象(例如同类的其他容器)。每个候选都要走一遍现有的 parser 和接收方在该读取点本来就执行的 admission 检查：只有解析无错且通过类型/范围检查的候选才被 admitted，失败的进 rejected 日志并记下原因。注册表按 (channel, key) 记录：按固定顺序排列的 admitted 列表、rejected 日志、fail-closed 标记——当 channel 的值是数值型、连续范围、或只允许一个取值、或没有任何候选通过时，标记为 fail-closed。注册表写成 JSON 文件，排序、计算哈希，并在任何探测开始前冻结。
   - _为什么：_ 内容类的声明需要能构造出来的替代值；在数值、schema 范围、单值这些不存在 canonical 对比的 channel 上，fail-closed 标记让证书保持诚实。

### M2_probe
*presence 探针：把每个原子记录的真实值重新注入其读取位置，测量逐原子配对 presence 效应，再用 canonical 替代值区分 presence 与 content。*

5. 对 crossed run 消费过的每个原子，从它保存的消费前状态出发——这份状态是 ALFWorld 环境的快照加上接收方在该次读取前一刻暂停下来的执行上下文，第2步（扩展 `src/skills...） 的插桩已把每个消费点变成了可恢复的暂停点。可探测总体就是 crossed run 消费过的原子：只出现在 native run 记录里的原子(cross-absent)在 crossed 重放里没有读取点，被排除；其 (channel, key) 从未出现在配对 native run 记录里的原子没有可恢复的原生值，作为 censored 排除。对可探测原子，native value v* 是配对 native run 对同一 (channel, key) 记录的值，按消费顺序逐次配对(第 k 次对第 k 次)；若 crossed run 本来消费的就是 v*，该原子 value-identical，在构造上就是 inert——不用重放，效应记为恰好为零。对其余每个原子，side-car 恢复快照，在记录的 read/default/drop 点上把 v* 通过正常的接受路径喂进去(restored arm)；un-restored arm 从同一快照恢复、不注入任何值。【作者需决定：第2步（扩展 `src/skills...） 的 census 还记录了 rejection、no-op、fallback、version 四类事件，但本步只点名 read/default/drop 三种位置——这四类事件是同样方式注入探测，还是标记为 censored、交给 第7步（把所有原子按两个标签分组） 的 joint mask 与 第10步（对每个声明边界——这里就是...） 的 abstention 规则处理，需要作者定夺；这一选择决定可探测原子范围与证书覆盖程度。】两个 arm 在 crossed run 消费过该原子的每个 seed 上各重放 8 次$R_{rep} = 8$，temperature 0、RNG 冻结；每个 seed 的 goal success 是 8 次二值目标判定的平均。配对的 presence 效应 $\Delta _{a}$ 按 seed 平均：goal_success(restored) 减去 goal_success(un-restored)，保留正负号。

*原子级 presence 效应：在种子集上，对 restored 与 un-restored 两个 arm 的 ALFWorld goal success 配对差取均值；两臂来自同一保存的消费前状态。*
$$ \Delta_a = \frac{1}{|S|} \sum_{s \in S} \left( G_s^{+} - G_s^{-} \right) \tag{1} $$

   - _为什么：_ 这正是 gap 点名的缺失测量原语：它把声明的覆盖从假设变成逐原子可证伪的假设，而且不用改写生产方或邻居的代码。
6. 对每个 channel 在 第4步（为每个 channel...） 注册表里有至少一个 admitted 替代值的原子，把每个 admitted 替代值 z 通过未改动的 parser 注入到同一个读取点、从 第5步（对 crossed run...） 用的同一份消费前状态出发，用同样的 8 次重放网格打分：z 的效应按同样的方式计算——按 seed 平均的 goal_success(z-arm) 减去 goal_success(un-restored)。因为重放网格是确定性的，比较就是精确比较、不做任何统计检验：只要有某个 admitted z 的效应与 v* 的效应不同，该原子就是 content-sensitive；若所有 admitted z 的效应都恰好等于 v* 的效应、且该效应不为零，则是 presence-sensitive；若所有效应——v* 效应和每个 z 效应——都恰好为零，或该 channel 是 fail-closed、没有 admitted 替代值，则不分类，写一条 abstention 记录。每个原子保存其分类——content-sensitive、presence-sensitive 或 abstained——实测的效应值，以及 abstention 的原因。
   - _为什么：_ 联合依赖可能让两个 arm 都为零，硬要分类就会把依赖误标成惰性；abstention 记录保住了证书的 fail-closed 纪律。

### M3_loadmap
*负载图：把按 declaredness 分层的逐原子效应与 joint-mask 效应汇总成负载图，再闭合每个 cell 的 accounting identity。*

7. 把所有原子按两个标签分组：declaredness——(channel, key) 出现在开头从 `docs/canonical_interface_v1.md` 提取的机器可读声明表里的就是 declared，否则 undeclared——以及来自 第4步（为每个 channel...） 注册表的 channel domain(Boolean、enum、object-symbol、numeric、schema-range、singleton 或各类 event)。若某原子的逐原子效应偏离恰好为零、或 第6步（对每个 channel 在...） 判定为 content-sensitive，就标记为 load-bearing。接着，对「逐原子效应全为零、而该 cell 的 swap delta 偏离零」的每个分组，跑该分组的 joint-mask arm：从每份消费前状态出发，把该分组内 第5步（对 crossed run...） 可探测的所有取值不同的原子——在 crossed run 里有读取点、且其 crossed 值与配对 native 值不同的每个原子——经同一个 carrier 同时恢复，每个 seed 在同一网格上重放 8 次$R_{rep} = 8$，joint 效应 $J_{j}$ 按 seed 平均：goal_success(joint-mask arm) 减去 goal_success(un-restored)；没有任何可探测原子的分组记为 joint-unprobeable、跳过该 arm。已认证的 undeclared load-bearing 集合 = 效应非零或判为 content-sensitive 的 undeclared 原子，加上 joint 效应非零的 undeclared 分组。

*per-stratum joint-mask 效应：将一个 stratum 内所有取值不同的原子经同一 carrier 联合恢复后，与 un-restored arm 在种子集上 goal success 配对差的均值。*
$$ J_j = \frac{1}{|S|} \sum_{s \in S} \left( G_s^{j+} - G_s^{-} \right) \tag{2} $$

   - _为什么：_ 联合要求的负载可能对逐原子探针不可见，所以 per-stratum joint mask 能把联合余项定位出来，而不用对互相依赖的原子组做穷举搜索。
8. 写出每个 cell 的记账表，把账关平：swap delta 等于所有已认证 load-bearing 原子的逐原子效应之和、加上所有已认证 joint-load-bearing 分组的 joint 效应之和、再加上余项。两个已认证求和项在构造上不可能重叠——joint arm 只在逐原子效应全为零的分组上运行——所以不会重复计数。每个 (receiver, neighbor) cell 的表列出：swap delta、已认证的逐原子求和、已认证的 joint 求和、余项(swap delta 减去两个已认证求和)、每个求和平均时用的 seed 数，以及 completion——已认证求和除以 swap delta，精确报告为分数，swap delta 为零时记为 undefined。余项保持为未标注的记账项；只有 第10步（对每个声明边界——这里就是...） 认证了 swap delta 的 joint coverage 时，它才在 第10步（对每个声明边界——这里就是...） 获得标注。

*每个 cell 的 accounting identity：swap delta 分解为已认证的 per-atom 效应、已认证的 joint-stratum 效应，以及仅当 swap delta 的 joint coverage 被认证时才可标注的余项 $\epsilon (r,n)$。*
$$ D(r,n) = \sum_{a \in \mathcal{A}^{*}} \Delta_a + \sum_{j \in \mathcal{J}^{*}} J_j + \varepsilon(r,n) \tag{3} $$

   - _为什么：_ 这个恒等式精确说明已认证的负载图解释了 swap delta 的多少，归因声明永远不会超过实测的覆盖。

### M4_validation
*验证装置：inert-carrier 与 full-native-payload 两个对照 arm，随后给出每个边界的完整性判定与推导出的 schema-later 接口。*

9. 给每个 cell 跑两个对照 arm。negative control：取测量为 inert 的一批原子——实测逐原子效应恰好为零的原子(包括判为 both-arms-zero abstention 的原子、效应为零的 fail-closed 原子)——用同样的 carrier 机制把它们记录的值重新注入各自读取点、在同样的 8 次重放网格上运行；carrier 本身必须不改变成功率。value-identical 的原子不进这批：注入它记录的值等于原样重跑 baseline，无法检验 carrier。inert bulk 为空的 cell 把 negative control 记为 not-run。positive control：恢复完整的 native payload——crossed run 消费过的所有取值不同的原子、跨所有分组、经同一个 carrier 一次性注入——并把它的效应与 cell 的 swap delta 比较；「挽回 swap delta 的大部分」指挽回份额(full-payload 效应除以 swap delta)严格大于一半，且任何时候都报告精确份额；份额小于等于一半就不满足效度边界。两个对照效应都用同一配对计分方式：按 seed 平均的 goal_success(对照 arm) 减去 goal_success(un-restored)。
   - _为什么：_ 两个对照把真实的原子负载和 carrier 伪影分开，并给任何单一 stratum 能解释的份额设了上限。
10. 对每个声明边界——这里就是 `docs/canonical_interface_v1.md` 定义的那一个——按固定的决策流程给出结论，依据 第7步（把所有原子按两个标签分组） 的已认证 undeclared load-bearing 集合和 第8步（写出每个 cell 的记账表） 的记账表。第一步，falsified：已认证的 undeclared 集合非空——有某个 undeclared 原子效应非零或判为 content-sensitive，或某个 undeclared 分组 joint 效应非零。第二步，abstained：可探测总体为空；或每个 undeclared 分组都是 censored(没有原生值、没有 crossed-run 读取点)或 fail-closed(没有 admitted 替代值)；或 swap delta 偏离零而 full-joint 覆盖未通过 第9步（给每个 cell...） 的效度边界——凡是所述条件无法裁决的情形都归为 abstained。第三步，not-falsified：swap delta 等于零；或 full-joint arm——即 第9步（给每个 cell...） 的 full-payload positive control——对 swap delta 的覆盖获得认证(挽回份额严格大于一半)且不存在 undeclared 负载；覆盖获得认证时，第8步（写出每个 cell 的记账表） 的余项标注为已认证残差。最后输出 schema-later 接口：把经 oracle 认证的 load-bearing 分组(效应非零的 declared 与 undeclared 原子和分组)合并成一份接口文档，逐项列出 (channel, key)、declaredness、效应与分类，并附每个 cell 的覆盖表和两个对照效应。
   - _为什么：_ 这把负载图变成 gap 要求的证书——用实测负载而不是假定的覆盖来审判声明边界。
