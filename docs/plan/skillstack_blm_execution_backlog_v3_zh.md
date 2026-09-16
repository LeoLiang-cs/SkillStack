# SkillStack / BLM 执行清单 v3

- 日期：2026-09-15
- 配套：[完整总计划](skillstack_blm_master_plan_v3_zh.md)、[方法定义](../original/skillstack_draft_framework_2.md)。
- 状态：G0 正式 commit gate 仍待 owner；G1 正在执行，O02/O04/O05/O06/O07 的本地技术项已有验收，hosted/final-SHA gate 未完成。旧能力仍不能替代同一验收 SHA 的最终证据。
- 本地研究材料；公开清单决定前不纳入release。
- 优先级P0为所列gate的阻断项，P1为后续完整交付必需；不是删除低优先级任务。

## 1. 任务与验收

| ID | 优先级 / gate | 输入与依赖 | 具体交付 | 验收证据 |
|---|---|---|---|---|
| O01 | P0 / G0 | 当前release.py、发布范围、dirty清单 | commit/显式清单导出；held与未知文件排除；artifact内容清单；详见[G0计划清单](g0_release_isolation_plan_list_zh.md) | 未tracked研究文件、外部symlink等回归用例；源码/wheel/sdist清单无误入 |
| O02 | P0 / G1 | O01；CLI/demo/配置资源 | 安装包资源与root规则；实际wheel/sdist安装路径；O02–O07详见[G1计划清单](g1_core_alpha_plan_list_zh.md) | 全新环境、非repo目录中version/import/demo成功；缺root错误可诊断 |
| O03 | P0 / G1 | O02；依赖与旧环境 | 受维护Python核心支持；Linux/macOS矩阵；历史环境复现说明 | 对应CI/隔离检查通过；未支持项明示；旧证据不改写 |
| O04 | P0 / G1,G2 | 现有runner/trace/checkpoints | 最小公共契约、manifest身份、错误分类、resume/integrity | 配置漂移拒绝、重复arm不重复计数、部分写入/中断可恢复 |
| O05 | P0 / G1,G2 | O01–O04；BLM随后增补 | 分层测试与CI、artifact门禁、skip规则 | 必需offline及分发路径通过；集成/模型测试独立报告 |
| O06 | P0 / G1 | O02–O05，现有reports | 安装/运行/扩展/输出/故障/贡献/引用文档 | 所有承诺的命令实测；最小新组件无需改邻接业务逻辑 |
| O07 | P0 / G1 | O01–O06 | 凭证/路径/重试/预算边界；维护与版本策略；alpha release packet | 文件清单/制品hash/支持矩阵/测试摘要一致；无阻断问题 |
| O08 | P1 / G5 | E03/E04，O07 | BLM最小demo、复现教程、研究发行制品 | 原始记录可重算表格和判定；独立复现或明确隔离验证标签 |
| B01 | P0 / G2 | framework v2、当前Consumer源码 | RQ/契约/原生来源/声明与传输表 | 四类失配可区分；选定第一次handoff；无虚构native配对 |
| B02 | P0 / G3 | B01、已有来源/候选模块 | 每个候选一页source/fidelity/donor/成本卡 | 至少一个自然案例具备合法对照才进入E01；全体筛选保留 |
| B03 | P0 / G2 | O04、B01 | 状态捕获/初始化重建与可比性报告 | 环境与Consumer状态核对；确定性no-op重复一致；局限可见 |
| B04 | P0 / G2 | O04、B01/B03 | atom/read/exposure记录与正常路径恢复 | provenance、donor、类型/约束校验；错误donor拒绝；不越过parser |
| B05 | P0 / G2 | B03/B04 | arms调度、controls、局部效应和verdict规则 | 同Consumer配对、载体控制、预算/失败清晰；raw→verdict可复算 |
| B06 | P0 / G2 | B05、O05 | 总计划8类校准案例和报告 | 预期判断一致通过；人工缺失标签明确，fail不能被summary吞掉 |
| B07 | P0 / G3,G4 | B01；primary sources | 方法级相关工作表、基线实现/使用说明、增量标准 | 同候选/oracle/预算比较；全文可用性和未排除威胁可见 |
| E01 | P0 / G3 | B02、G2 | 开发pilot、首个自然案例、第二案例选择理由 | 全部case/排除/无效/零结果记录；判定与控制一致 |
| E02 | P0 / G4 | E01、B07 | 正式预注册manifest、样本依据、任务划分、费用/停止规则 | frozen hash；发现/确认分离；多重比较/误差规则明确；脚本dry-run通过 |
| E03 | P0 / G4 | E02、O04/O05 | 可续跑运行单、正式结果、独立确认、修订验证 | 计划和实际计数一致；失败保留；目标精度与排除规则核对 |
| E04 | P0 / G5 | E03、B07、O08 | 稿件、主张证据映射、表图、制品验收 | 每条主张可追溯到已执行数据；复现/限制/负结果完整 |

## 2. 第一批执行任务

### Batch A：发布与核心安装

- G0 的逐项实施、测试和退出条件以 [G0 发布隔离完成计划清单](g0_release_isolation_plan_list_zh.md) 为准。
- [ ] 保存当前tracked/untracked清单与基线SHA，确保已有用户文件不被混合提交。
- [ ] O01：修复release选择，新增实际误入路径的回归测试。
- [x] O02：在隔离环境安装实际发行包，记录资源/配置/root缺口，再完成必要修复；wheel/sdist fresh-venv acceptance 已通过，hosted/final-SHA 仍待补。
- [x] 更新发布文档中的CI状态与测试/skip计数；所有陈述注明验证版本。
- [x] 输出 G0 记录和 G1 剩余缺口；不把包“build成功”当作包“使用成功”。

### Batch B：研究定义与来源可行性

- [ ] B01：选择一次明确的D→C handoff，填契约/传输/消费/结果四层表。
- [ ] B02：审查已有来源资产可用性，列真实参考与crossed路径，记录candidate排除原因。
- [ ] 选择3个开发任务的预定语义规则，核查与历史/held-out的重叠。
- [ ] B03设计：列出必须恢复的环境与Consumer状态，明确每项能否观测。
- [ ] 输出可实施spec；再进入插桩与恢复代码。

Batch A/B可交错进行；默认一个实现者，不能把“可并行”写成已安排额外人力。

## 3. 必需产物约定

以下均为待实现目标，非现有文件/命令。

| 类型 | 目标内容 | 保存原则 |
|---|---|---|
| 发布清单 | commit、纳入/排除文件、制品hash、验证环境 | 与实际发布制品绑定，工作区变化不静默改变清单 |
| 组件卡 | source、commit、license、fidelity、native reference、限制 | 每个新增组件都要有；失败候选也保留 |
| BLM manifest | 契约/任务/Consumer/atom/donor/arms/oracle/model/预算/统计 | 冻结后修改产生新版本及run |
| raw evidence | states、census、interventions、outcomes、errors、usage | 追加写入，checkpoint可恢复，不覆盖旧失败 |
| derived outputs | validity、verdict、coverage、paired effects、baseline comparison | 可从raw重建，有分析代码/hash与输入版本 |
| release packet | 安装包、最小demo、教程、报告、来源、引用 | 只含允许公开的内容，research/raw与core边界明确 |

## 4. 运行前必须填写的单据

每个需要模型的run启动前填写：

1. 问题、主指标、有效性与停止规则。
2. 精确命令、工作目录、必要服务与依赖版本。
3. manifest路径/hash，task/cell/arm/replicate数与planned总量。
4. 预检测得的单次耗时和token消耗、总费用估计、硬上限。
5. 输出目录、checkpoint、错误记录、进度与预计完成条件。
6. 取消/恢复命令，配置漂移和缓存失效处理。
7. 完成后验收命令、预期计数和分析入口。

本轮不填虚构BLM命令。Leo启动长任务；实现协作者提供已验证的零模型预检、运行单和事后审计。

## 5. 每项任务的完成记录模板

- Task ID / 状态：planned → in_progress → verified；blocked/deferred必须附原因与后果。
- 实际改变与交付文件：填写真实路径。
- 验证版本、命令、环境和结果：未执行的检查写not run。
- 新增或修改的研究/兼容承诺：无则写无。
- 已知限制：是否阻断当前gate，为什么。
- 下一依赖任务：只在当前验收通过后标ready。

当前 O01/G0 为 `in_progress`，已完成临时候选验证但尚待正式项目 commit gate；O02/O04/O05/O06/O07 为
`in_progress`（本地技术项部分 verified，hosted/final-SHA 尚未完成）；O03 的 maintained
hosted matrix、O08、B01–B07、E01–E04 仍为 `planned`。
