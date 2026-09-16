# G0 发布隔离完成计划清单

> 历史工程清单：G0 与 G1 已在[科研主线计划 v4](skillstack_research_master_plan_v4_zh.md)中合并为 F0。本文保留原始发布工程拆解，不再作为当前独立 gate，也不阻塞 BLM。

- 日期：2026-09-15
- 状态：`in_progress`；实现已通过临时候选验证，正式项目 commit gate 尚未完成。执行证据见 [Week 7 G0 报告](../../report/week7/g0_execution_report_zh.md)。
- 对应总计划：[SkillStack 开源工程与 BLM 完整计划 v3](skillstack_blm_master_plan_v3_zh.md)
- 对应任务：O01 / G0
- 目标工期：单人约 1.5–2.5 个专注工作日；以验收结果为准，不以日期自动结束。
- 范围边界：只完成基线固定、公开范围策略、发布快照隔离和证据包。wheel/sdist 脱离仓库后的可用性属于 G1/O02；正式 tag、GitHub Release 和公开推送不在 G0 内。

## 1. G0 的最终结果

G0 完成后，给定一个明确的 Git commit，系统能够生成唯一、可复核的公开候选快照。当前工作区中的未提交研究文档、held 文件、外部数据和生成结果，无论是否位于 `docs/` 或 `reports/` 下，都不能静默进入候选。

G0 只在以下五件事同时成立时通过：

1. 发布输入是解析后的完整 commit SHA，而不是会随工作区变化的目录状态。
2. 公开范围由版本化策略决定；未知路径默认排除，研究敏感目录采用显式允许项。
3. 候选包含逐文件 SHA-256、来源 commit、策略版本和排除摘要。
4. 源码快照通过 held、symlink、路径穿越、secret 和未 tracked 文件的回归检查。
5. 同一 commit 和同一策略重复生成的文件清单与 hash 完全相同，且没有未解释的范围差异。

## 2. 已知问题与本轮不变量

当前 `src/skillstack/release.py` 会递归扫描工作区中的 `docs/`、`reports/` 等目录。只读检查已经证明未 tracked 的 framework、scoop-check 和 Week 6 文件会被选中。因此，现有 `release-check` 的通过记录不能作为新 G0 的完成证据。

实施期间必须保持以下不变量：

- 不删除、移动或覆盖当前未提交研究文件。
- 不用宽泛的 `git add .` 将研究材料混入发布修复提交。
- 不修改 Week 1–5 原始实验结果来适配新清单。
- `SkillStack = 已实现基础设施`，`BLM = 尚待实现的研究方法`；G0 不改变这一主张边界。
- G0 的测试只能证明“候选隔离正确”，不能证明安装包已可供外部用户使用。

## 3. 实施顺序

### G0-00 固定输入基线

- [ ] 记录开始实施时的 `HEAD` 完整 SHA、branch、tracked 变更清单、untracked 清单和 submodule 状态。
- [ ] 将现有工作区差异分成：G0 实现、held research、external data、generated/scratch、待人工判断。
- [ ] 为 G0 建立窄范围变更清单；只允许预定的发布代码、测试、策略和发布文档进入实现提交。
- [ ] 不将当前 dirty 工作区复制为候选；候选始终引用明确 commit。

交付：一份本地 G0 基线记录，包含 SHA 和分类后的路径清单，但不包含 secret 内容。

验收：后续任一候选都能回答“来自哪个 commit、当时工作区还有哪些未纳入变化、为什么未纳入”。

### G0-01 建立版本化发布范围策略

- [ ] 新增机器可读的发布策略文件，建议路径为 `configs/public_release_scope.yaml`。
- [ ] 策略至少包含：`schema_version`、公开允许项、held 前缀、外部数据前缀、生成结果前缀、必需文件和禁止的文件类型。
- [ ] 将候选路径归为四类：`public`、`held_research`、`external_data`、`generated`；无法归类的路径为 `unknown`。
- [ ] `unknown` 默认不进入候选，并在报告中可见；不能仅靠 `.gitignore` 或“文件没有 tracked”表达发布策略。
- [ ] 对 `src/`、`tests/` 等工程目录可使用受控根规则；对 `docs/`、`reports/`、`.agents/skills/` 等研究敏感区域使用精确目录或文件允许项。
- [ ] 明确当前 Week 6、BLM final cards、scoop-check、中间 idea-spark、论文全文和原始模型输出的默认分类。
- [ ] 策略路径必须为仓库相对 POSIX 路径；拒绝绝对路径、`..` 和无法规范化的条目。

交付：`configs/public_release_scope.yaml` 及对应策略解析/校验逻辑。

验收：每个 tracked 候选都有唯一分类；新增未知路径不会自动变成 public；策略冲突、重复分类或缺少必需文件时 fail closed。

### G0-02 将收集器改为 commit-based

- [ ] 为发布入口增加必需或显式默认的 `--ref`，并立即解析成完整 commit SHA；manifest 中只保存解析后的 SHA，同时保留用户输入 ref 供审计。
- [ ] 从该 commit 的 Git tree 枚举路径并读取内容，不再从当前工作区递归复制 `docs/`、`reports/` 或其他根目录。
- [ ] 发布策略也必须来自同一个 commit；不能用工作区中的新策略解释旧 commit。
- [ ] 只有策略标记为 `public` 且存在于该 commit 的 blob 才能进入候选。
- [ ] 明确处理 Git file mode；v0.1 alpha 默认拒绝候选中的 symlink。未来若确需支持，必须另加白名单和目标边界检查。
- [ ] 保持路径顺序稳定、时间戳归一或不参与内容身份，确保重复构建可比较。
- [ ] 无法解析 ref、不是 Git repo、对象缺失、策略不合法或读取 blob 失败时立即失败，不回退到工作区扫描。

主要改动位置：`src/skillstack/release.py`、`src/skillstack/cli.py`。

验收：在工作区新增、修改或删除未提交文件，不改变同一 commit 的候选文件集合和逐文件 hash。

### G0-03 生成可审计 manifest

- [ ] 为每次候选生成 `release_manifest.json`。
- [ ] 顶层至少记录：schema version、requested ref、resolved commit、policy blob/hash、生成工具版本、文件总数、总字节数、候选内容 hash、分类计数和 gate 状态。
- [ ] 每个 public 文件至少记录：相对路径、Git mode、字节数和 SHA-256。
- [ ] 排除摘要记录各分类的数量与路径；secret 命中只记录规则和文件位置，不打印命中值。
- [ ] manifest 自身不循环计入候选内容 hash；其 canonical serialization 规则固定并测试。
- [ ] 候选目录、source archive 与 manifest 必须共享同一个 resolved commit 和内容身份。

交付：稳定的 manifest schema、生成器和样例测试输出；正式生成物写入临时或 `dist/`，不作为源码输入再次收集。

验收：修改任一纳入文件会改变对应文件 hash 和候选内容 hash；只修改 held/untracked 文件不会改变二者。

### G0-04 增加隔离与安全回归测试

测试必须在临时 Git 仓库 fixture 中构造，不依赖 Leo 当前工作区恰好有什么文件。

- [ ] tracked public 文件会进入候选。
- [ ] 未 tracked 文件即使位于允许根目录内也不会进入候选。
- [ ] tracked held research 文件不会进入候选，并出现在排除摘要。
- [ ] tracked unknown 文件默认排除并可见。
- [ ] 工作区中对 tracked 文件的未提交修改不会污染指定 commit 的内容。
- [ ] symlink 指向仓库外、仓库内或不存在目标时均按当前 fail-closed 策略拒绝。
- [ ] 策略中的绝对路径、`../`、重复/冲突规则和非法 schema 被拒绝。
- [ ] `.env`、凭证形态文件、paper PDF、外部数据和生成输出不会进入候选。
- [ ] 同一 commit 构建两次得到相同的路径列表、文件 hash 和候选内容 hash。
- [ ] 不同 commit 的候选明确显示不同 resolved SHA；ref 漂移不会被静默忽略。
- [ ] held 或 unknown 文件被误设为 public 时，publication audit/secret scan 仍能阻断明显违规内容。

主要改动位置：`tests/test_release.py`；必要时新增最小测试 helper，但不引入大型 fixture 副本。

验收：以上用例全部通过；原先只针对当前 repo 路径存在性的测试被替换或补强为独立 fixture 证明。

### G0-05 重构 release-check 的门禁输出

- [ ] `release-check` 输出中加入 resolved commit、policy hash、manifest 路径/内容 hash、dirty-worktree 摘要和每个 gate 的独立状态。
- [ ] 将“候选构建隔离通过”和“候选内零模型检查通过”分开报告；任一必需项失败时总状态失败。
- [ ] 输出明确区分 `selected`、`excluded-held`、`excluded-external`、`excluded-generated`、`excluded-unknown` 和 `rejected`。
- [ ] 保留现有 fresh-clone 检查，但其 clone 输入必须是 commit-based 候选，而不是工作区复制品。
- [ ] 所有失败都给出可执行原因；不能因缺少 Git、策略或文件而悄悄返回空集合。
- [ ] 默认输出不泄露环境变量、API key 或扫描命中的原文。

验收：人为加入一个未 tracked Week 6 文件后，检查报告能说明工作区 dirty，但候选 manifest 不变；人为制造路径/symlink违规时，检查以非零状态结束。

### G0-06 检查三类拟发布内容

G0 负责检查“内容边界”，不负责宣称三类制品已在外部环境可用。

- [ ] 检查 commit-based source snapshot 的逐文件 manifest。
- [ ] 构建 wheel 和 sdist，并分别列出内部文件；确认 held、unknown、外部数据和生成结果均不在其中。
- [ ] 记录 source snapshot 与 wheel/sdist 内容差异；包内 metadata 或布局导致的合理差异必须有解释。
- [ ] 校验 wheel、sdist 和 source archive 的 SHA-256，并绑定 resolved commit。
- [ ] 不以 `build succeeded` 替代 G1 的“非 repo 目录安装后可使用”测试。

验收：三类内容清单均通过范围检查，所有差异有明确来源；若 package 配置意外收录文件，G0 阻断。

### G0-07 校正文档状态

- [ ] 更新 `docs/open_source/RELEASE_SCOPE.md`：将宽泛的“curated reports”改为与机器策略一致的真实规则。
- [ ] 更新 `docs/open_source/PUBLICATION_AUDIT.md`：历史 243-file 检查保留日期语境，但不再作为当前通过结论。
- [ ] 更新 release notes/CHANGELOG 中受 G0 影响的发布说明；只写实际完成和实际验证的内容。
- [ ] 明确 alpha release candidate、formal tag、hosted CI、wheel/sdist 安装验证的不同状态。
- [ ] 文档中的文件数、测试数和 SHA 由最终 G0 运行生成或引用，避免手工复制后漂移。

验收：人类文档与机器 manifest 对公开/held 边界没有冲突；搜索不到把 BLM 说成已实现或把未发布 candidate 说成 formal release 的新表述。

### G0-08 形成 Gate 证据包并签字

- [ ] 从准备验收的明确 commit 运行完整 G0 门禁。
- [ ] 保存 manifest、source/wheel/sdist hash、测试摘要、dirty-worktree 分类和已知限制。
- [ ] 逐项核对本文第 4 节的退出表；任何失败项保持 open，不以备注代替通过。
- [ ] Leo 只需确认公开范围和“未解释 diff = 0”；技术测试由执行结果证明。
- [ ] 通过后将 O01 标为 `verified`，记录实际 commit；随后才启动 G1/O02。

交付：`G0 completion record`，明确标注实际验证环境、命令、结果、commit 和仍未覆盖事项。

验收：第三方只看证据包和候选，就能重算文件 hash、识别来源 commit，并证明 dirty/held 研究材料未进入候选。

## 4. G0 Exit Gate

| Gate | 必须满足的证据 | 状态 |
|---|---|---|
| G0-A 来源身份 | requested ref 已解析为完整 commit SHA；候选从该 Git tree 构建 | planned |
| G0-B 范围策略 | 版本化策略通过 schema 校验；所有候选路径有唯一分类 | planned |
| G0-C 工作区隔离 | 新增/修改未提交研究文件不改变指定 commit 的 manifest | planned |
| G0-D held/unknown 隔离 | held、unknown、external、generated 在 source/wheel/sdist 中均为 0 | planned |
| G0-E 路径安全 | symlink、绝对路径、路径穿越和非法模式按策略被拒绝 | planned |
| G0-F 可复核身份 | 逐文件 SHA-256、候选内容 hash、策略 hash 和制品 hash 齐全 | planned |
| G0-G 可重复性 | 同 commit + 同策略重复生成结果一致 | planned |
| G0-H 零模型候选检查 | commit-based fresh clone 的必需检查通过；失败项无隐藏 | planned |
| G0-I 文档一致性 | release scope、audit、notes 与 manifest 和实际状态一致 | planned |
| G0-J 差异解释 | 发布修复范围外的 dirty 路径均分类；未解释 diff 为 0 | planned |

判定规则：十项全部为 `verified` 才能宣布 G0 完成。`waived` 不等于通过；若确需收缩要求，必须先修改本计划并记录原因、风险和新版本。

## 5. 建议的最小变更面

预计需要修改或新增：

- `configs/public_release_scope.yaml`
- `src/skillstack/release.py`
- `src/skillstack/cli.py`
- `tests/test_release.py`
- `docs/open_source/RELEASE_SCOPE.md`
- `docs/open_source/PUBLICATION_AUDIT.md`
- `docs/open_source/RELEASE_NOTES_v0.1.0-alpha.md`
- `CHANGELOG.md`
- 一份本地 G0 completion record

除非测试证明必要，G0 不新增第三方 Python 依赖，不重构 runner、trace、adapter 或 BLM 代码，也不改动历史实验数据。

## 6. 实际执行时的三批提交

为避免把当前研究工作区混入发布修复，建议按以下审阅单元实施；这是提交边界建议，不表示现在创建 commit：

1. **G0 policy + collector**：范围策略、commit-based 收集、manifest。
2. **G0 regression tests**：临时 Git fixture、隔离/路径/确定性测试。
3. **G0 docs + evidence**：scope/audit/notes 校正与最终 completion record。

每批只暂存明确路径并先审阅 staged diff。正式 push、tag 或 GitHub Release 仍需 Leo 另行决定。
