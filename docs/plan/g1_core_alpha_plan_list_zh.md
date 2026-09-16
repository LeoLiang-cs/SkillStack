# G1 健全核心 Alpha 完成计划清单

> 历史工程清单：G0 与 G1 已在[科研主线计划 v4](skillstack_research_master_plan_v4_zh.md)中合并为完成的 F0。本文保留验收细节；下一阶段直接进入 BLM R1，正式开源整理移到论文完成之后。

- 日期：2026-09-16
- 状态：`core_complete`；验收提交 `fc6a446` 已通过 Ubuntu/macOS、Python 3.11/3.12 hosted CI。下一阶段直接进入 BLM；正式 release packet、tag、GitHub Release、PyPI 和 `CITATION.cff` 延期到论文完成后。
- 对应当前总计划：[SkillStack / BLM 科研主线计划 v4](skillstack_research_master_plan_v4_zh.md)
- 对应任务：O02–O07 / G1
- 目标工期：单人约 6–10 个专注工作日；以 gate 为准，不以日历自动结束。
- G1 目标：交付一个第三方能从实际发行包安装、运行、诊断、扩展和维护的 core alpha；正式发布整理留到完整项目完成后处理。
- 范围边界：不实现 BLM 测量、replay 或正式实验；不要求完整 ALFWorld/AgentBench 环境进入核心包；不自动创建 tag、GitHub Release 或 PyPI 发布。

### 当前项目决策（2026-09-16）

- 使用正常项目粒度 commit/push，不再要求开源、BLM 与核心代码分别形成独立提交。
- `.env`、API key 与其他 credential 不得进入 Git；仅保留无真实密钥的 `.env.example`。
- F0 完成后直接进入 BLM；开源发布整理在研究实验与论文完成后单独启动。
- 因此 O07-03 作为延期的发布工作保留清单，但不计入当前核心 G1 Exit Gate。

## 1. G1 的完成定义

G1 只有在以下结果同时成立时完成：

1. 用户在非仓库目录安装 wheel 和 sdist 后，可运行 `import`、版本查询和零模型 demo；不依赖作者 checkout。
2. 贡献者 checkout 路径与普通安装包路径被明确区分，repo-only 命令缺少 root 时给出可执行错误。
3. 核心支持矩阵在 Python 3.11/3.12、Linux/macOS 上有实际证据；历史实验环境与维护支持分开。
4. run manifest、trace、summary、错误状态和 resume identity 形成稳定最小契约。
5. 必需的 offline、packaging、integration 测试均通过；可选环境的 skip 不冒充支持。
6. 用户、贡献者、研究与发布文档中的命令和主张都与实际版本一致。
7. 路径、凭证、网络重试、预算、失败保留和发布回滚边界通过检查。
8. 本轮完成记录绑定唯一验收 SHA、制品 hash、支持矩阵、测试摘要、已知限制和回滚边界；正式 release packet 延期。

## 2. 收口结果与保留边界

- `skillstack demo` 的安装包资源缺口已在 Batch 1 修复；wheel/sdist 已在 Python 3.10 historical、Python 3.12 macOS local 与 Python 3.12 hosted Ubuntu fresh venv 通过 package smoke。
- `src/skillstack/llm/client.py` 已加入包内安全 metadata fallback，`.env` 默认仅看当前工作目录；O02-02 的配置优先级、schema/字段校验和未知 backend 诊断已收口。
- `preflight`、`check-repo`、`release-check` 是 repo/contributor 命令；CLI 诊断和文档已将其与普通安装包用户入口分开。
- `pyproject.toml`、锁文件和 CI 已配置 3.11/3.12 maintained matrix；四个 hosted Linux/macOS cells 均已通过 full core gate。
- demo/core path 已使用统一 manifest/summary/status schema、identity hash 和 writer resume 检查；Week 2–5 脚本仍保留 historical entrypoint，尚未迁移。
- `JsonlTraceWriter` 已规范化用户 `run_id` 并拒绝绝对路径、`..` 和 output-root 逃逸；partial-tail/cancelled/missing-summary、retry/budget policy fixture 已补。
- CI 已验证 Ubuntu 3.11/3.12 与 macOS 3.11/3.12；Ubuntu 3.12 wheel/sdist 已通过脱离 checkout smoke。
- README、CONTRIBUTING、release notes、publication audit 和 O06 指南已同步当前边界；旧版本表述仅保留为 historical reproduction 说明。

上述条目记录核心 G1 的实际完成面；Week 2–5 historical entrypoint 迁移、Windows、正式发布与 BLM 仍在当前范围之外。

## 3. 依赖与执行顺序

```text
G0 verified
   ↓
O02 安装与资源 ──→ O03 支持矩阵
   ↓                  ↓
O04 运行与输出契约
   ↓
O05 测试与 CI
   ↓
O06 文档同步
   ↓
O07 安全、维护与 release packet
   ↓
G1 Exit Gate
```

O02/O03 可以交错；O06 可以提前建立目录和清单，但涉及命令、schema、支持版本的正文必须等 O02–O05 稳定后定稿。

## 4. O02：安装与资源访问

### O02-00 冻结用户入口和贡献者入口

- [x] 列出 CLI 子命令并分类：普通用户、贡献者/repo-only、研究脚本、内部命令。
- [x] 普通用户最低入口固定为：版本查询、零模型 demo、输出读取；不要求 repo root、数据集或 API key。
- [x] `preflight`、`check-repo`、`release-check` 明确为 repo-only；缺少 repo marker 时输出缺什么和正确用法。
- [x] 不把 Week 2–5 一次性研究脚本承诺为稳定安装包 CLI。

验收：README 和 `--help` 对每个入口的环境前提一致；安装包用户不会被引导到不存在的 repo 文件。

### O02-01 打包零模型 demo 资源

- [x] 将 demo 必需的 task、recorded actions、expected outputs 和最小 skill library 作为 package data 随 wheel/sdist 分发。
- [x] 使用 Python `importlib.resources` 读取内置资源；显式 `--root` 仍保留为 contributor override。
- [x] 默认 demo 输出写入用户显式目录或当前目录的安全子目录，不写回安装包位置。
- [x] package resource 和 repo fixture 的语义/指纹一致；回归测试比较两条路径的固定 fingerprint。
- [x] 核心 demo 全程零模型、零网络、零外部数据。

建议改动面：`src/skillstack/demo.py`、package resource 目录、`pyproject.toml`、demo tests。

验收：从任意非 repo 目录执行安装后的 `skillstack demo` 成功，且输出仍明确不是 benchmark-performance 证据。

### O02-02 明确配置来源与优先级

- [x] 将安全的 backend defaults 作为包资源或显式示例配置提供；真实 endpoint/model 配置允许通过明确路径传入。
- [x] 固定优先级：显式调用方路径 > 环境变量 > 用户配置文件 > checkout 配置 > 包内安全默认值。
- [x] `.env` 自动读取只允许在用户明确指定或 contributor 文档路径中发生；核心 import/demo 不自动扫描作者目录。
- [x] 有效配置与错误边界不显示 key 值、Authorization header 或完整敏感错误体；公开 CLI 不提供隐式 live 配置入口。
- [x] 配置缺失、字段非法、backend 不存在时在发起网络请求前失败。

建议改动面：`src/skillstack/llm/client.py`、CLI/config tests、example config docs。

验收：在没有 repo、`.env`、API key 的环境中 import/demo 成功；需要模型的路径在缺配置时给出确定性诊断。

### O02-03 wheel/sdist 脱离 checkout 验收

- [x] 已提供 `scripts/check_package_install.py`，从指定 checkout 构建 wheel 和 sdist 并记录二者 SHA-256；wheel/sdist 已在 Python 3.10 historical 与 Python 3.12 macOS local fresh venv 通过。
- [x] 为 wheel、sdist 分别创建全新虚拟环境；不能复用开发 checkout 的 editable install（已验证 Python 3.10 historical 与 Python 3.12 macOS）。
- [x] 切换到非仓库目录执行 package import、版本、CLI help、零模型 demo、内置配置解析（已验证 Python 3.10 historical 与 Python 3.12 macOS）。
- [x] 检查 metadata、license、THIRD_PARTY_NOTICES、package data 和 console entry point。
- [x] 卸载后确认不残留依赖作者路径的入口。
- [x] packaging 测试脚本可在 CI 重复执行；失败时保留失败命令、错误摘要和已生成制品 hash。

验收：wheel 与 sdist 两条安装路径独立通过；`uv build` 成功本身不算通过。

### O02-04 O02 完成记录

- [x] 记录用户入口、repo-only 入口、资源来源、配置优先级和安装验收结果。
- [x] 将 PyPI 保持为 `optional/deferred`；未确认包名、凭证和发布策略前不发布。

O02 exit：安装包在非 repo 目录可使用；所有默认资源来自包内或用户显式路径；没有作者目录依赖。

## 5. O03：支持矩阵与依赖

### O03-00 冻结支持声明

- [x] maintained core：Python 3.11、3.12；Ubuntu Linux 与 macOS（hosted matrix 已验证）。
- [x] Windows 标为 `unverified`，不写成支持或不支持。
- [x] Python 3.9/3.10 标为 `historical reproduction`，不再作为 maintained core 承诺。
- [x] ALFWorld、AgentBench、GRASP、SkillRL、SkillOps 使用各自锁定环境/服务边界，不因 core 升级改写历史证据。

验收：README、metadata、CI 和 SUPPORT 文档只有一份一致的支持矩阵。

### O03-01 更新 metadata 与锁文件

- [x] 更新 `requires-python`、classifiers、CI matrix 和 `uv.lock`。
- [x] 核心依赖保持最小；ALFWorld 继续作为 optional extra，不能被普通 import/demo 隐式加载。
- [x] 为 optional integration 记录来源、版本/commit、许可证和已知 Python 约束。
- [x] 核查依赖升级后的行为差异；旧报告保留其当时版本，不回写新环境结果。

验收：core install 不下载数据或模型；依赖解析在 3.11/3.12 成功；历史环境说明可定位。

### O03-02 平台矩阵验证

- [x] Ubuntu：Python 3.11/3.12 已跑 hosted core offline gate；3.12 另跑 packaging acceptance。
- [x] macOS：Python 3.11/3.12 已跑 hosted core offline gate；3.12 另有 local wheel/sdist install smoke。
- [x] 记录本地与 hosted 架构、Python patch、uv 版本、依赖锁 hash、运行日期和 hosted URL。
- [x] 平台特有失败进入 known issues；当前验收无平台特有失败。

O03 exit：维护支持与历史复现彻底分开，目标矩阵有实际运行证据，未验证平台不被宣传。

## 6. O04：稳定运行与输出契约

### O04-00 冻结最小稳定公共面

- [x] 稳定对象仅包括：组件调用边界、run manifest、episode trace、summary、配置和 schema version。
- [x] R–A–D–C–L 继续作为责任词汇，不要求为每个槽位建立一个新的抽象层；O06 architecture guide 已明确其为责任坐标而非强制模块。
- [x] 旧 Week 1–5 脚本默认标为 historical experiment entrypoints；只有迁入 core contract 的部分获得稳定承诺。
- [x] 外部组件必须经显式 adapter 接入并保留 native payload/source/fidelity；不支持的语义明确拒绝。

### O04-01 统一 run manifest identity

- [x] 定义 `skillstack-run-manifest-v1`，至少包含：run/schema、code commit、package version、task/data hash、组件 ID/source/fidelity、config hash、model effective ID、prompt hash、decoding、budget、seed scope、oracle 和创建时间（已在 demo/core path 落地；旧研究脚本迁移仍待补）。
- [x] 将影响结果的字段归一化后生成 `run_identity_sha256`；字段列表和 canonical serialization 固定并测试。
- [x] manifest 一次写入、原子落盘、禁止覆盖；核心 writer 不写入 credential value。
- [x] live/provider 错误、日志和 manifest 的 credential-like value 脱敏边界已由 client 与回归测试覆盖；完整 release audit 仍在 O07。
- [x] repo dirty 状态和外部 checkout commit 字段明确记录；未知时写 `unavailable`，不推测。

验收：改变任一结果相关字段会改变 identity；非结果展示字段不应静默创建新实验身份。

### O04-02 统一 trace 和状态模型

- [x] 定义 `skillstack-episode-trace-v1`，保留 raw observation、native payload、adapter events、actions、usage、latency、warnings 和来源。
- [x] 分开记录：`run_status`（running/completed/error/timeout/cancelled）、`measurement_status`（valid/invalid/abstained/not_applicable）和 `task_success`（true/false/null）。
- [x] runner exception、task failure、timeout、无效输入、主动 abstention 不再被同一个 `success=false` 吞并。
- [x] JSONL 每个完成/失败 episode 一行；中断前的完整行保留，截断尾行可诊断且不会被计为完成（fixture 已覆盖 malformed tail/cancelled）。

验收：每一种状态都有 fixture；summary 能区分失败原因，未知不能被填成 false。

### O04-03 resume 与幂等

- [x] resume 必须读取原 manifest 并比较完整 `run_identity_sha256`；漂移时拒绝并提示创建新 run。
- [x] 已完成 episode ID 不重复执行、不重复计数；失败/未完成是否重试由 caller 显式策略决定，client 的 transient retry 与 run budget 已固定。
- [x] 用户提供的 run ID 统一规范化；输出路径必须位于 output root 内，禁止绝对路径和 `..` 逃逸。
- [x] checkpoint/summary 采用原子写；raw JSONL 只追加，derived summary 新建版本或明确覆盖规则。
- [x] 重复 resume、部分写入、缺失 summary、预算耗尽和取消均有策略测试；malformed tail、missing summary、cancelled、transient retry 与 call/token budget 均保留失败证据或明确拒绝。

验收：相同身份 resume 得到一致计数；配置变化、重复 episode 和目录逃逸全部被拒绝。

### O04-04 summary 与证据完整性

- [x] summary 同时列出 planned、started、completed、valid、success、task_failure、error、timeout、cancelled、invalid、abstained、skipped。
- [x] 所有 episode status counters 可从 raw trace 重算；summary 不作为事实来源。
- [x] summary 记录输入 identity/hash、生成代码版本和时间；raw evidence 永不因重新汇总被覆盖。
- [x] demo 和 maintained offline contract fixture 使用统一契约跑通，并可从 raw JSONL 重算 summary counters。

O04 exit：第三方能判断“计划了什么、实际跑了什么、哪些结果有效、为何失败、是否安全续跑”。

## 7. O05：测试分层与 CI

### O05-00 固定 G1 必需层

| 层 | G1 要求 | 失败处理 |
|---|---|---|
| Core offline | 每个 PR 必跑；3.11/3.12 | 任一失败阻断 |
| Packaging | wheel/sdist、非 repo 安装、资源与 metadata | 任一失败阻断 release-related PR 和 G1 |
| Integration offline | adapter round-trip、unsupported semantics、邻接组件不变 | adapter/core 变更时阻断 |
| ALFWorld local | 数据已准备时真实 reset/step/oracle | 缺数据允许 skip，但必须说明来源和命令 |
| Live provider | 手动小规模 preflight | 不进普通 CI；未运行不能写 pass |
| BLM calibration | G2 才启用 | 不计入 G1 |
| Formal evidence | G4 才启用 | 不计入 G1 |

### O05-01 建立测试入口

- [x] 保留一个快速 core offline 命令，默认零网络、零模型、零外部数据。
- [x] 新增 packaging acceptance 入口，真实安装构建出的 wheel/sdist，而不是 import checkout 源码；hosted Ubuntu 3.12 已通过。
- [x] maintained offline contract fixture 合法、轻量、可再分发；`tests/test_offline_contract_integration.py` 重算 raw JSONL 与 summary，外部来源 fidelity 仍由各 adapter 测试覆盖。
- [x] 对 skip 设置允许原因清单；必需层出现意外 skip 时 gate 失败。
- [x] `scripts/run_core_gate.py` 输出运行数、skip 数、平台、Python、失败项和可选制品 hash，不只输出退出码。

### O05-02 更新 CI

- [x] Ubuntu 3.11/3.12 执行 core offline；Ubuntu 3.12 job 另执行 packaging acceptance。
- [x] macOS 3.11/3.12 执行 core offline、demo 和 build smoke。
- [x] workflow 权限维持 `contents: read`，外部 action 固定不可变 commit，PR 不注入 secrets。
- [x] 缓存只加速依赖，不作为实验/测试证据来源；core/packaging JSON 摘要独立上传保留。
- [x] hosted CI URL、commit 和结果进入 G1 completion record；本地通过未被用于替代 hosted gate。

O05 exit：G1 必需路径无意外 skip；平台/packaging 证据可定位；研究或模型测试仍与普通 CI 隔离。

## 8. O06：用户、贡献者与研究文档

### O06-00 文档交付清单

- [x] `README.md`：定位、支持矩阵、安装、首个 demo、输出解释、研究状态与 claim boundary。
- [x] `docs/user/quickstart.md`：wheel/sdist 用户路径，不要求 checkout。
- [x] `docs/user/configuration_and_runs.md`：配置优先级、manifest/trace/summary、resume 和费用/重试边界。
- [x] `docs/user/troubleshooting.md`：安装、资源、配置、外部数据、timeout、部分写入和恢复。
- [x] `docs/development/architecture_and_extensions.md`：R–A–D–C–L 责任、稳定面、最小 Retriever/Executor/adapter 接入和测试。
- [x] `docs/research/reproducibility.md`：fidelity、任务划分、随机性、失败、abstention、统计与主张边界。
- [x] 更新 `CONTRIBUTING.md`、`docs/README.md`、release scope、publication audit、release notes 和 changelog。
- [x] 新增 `SECURITY.md` 与 `docs/open_source/MAINTENANCE.md`；`CITATION.cff` 仍等待作者、名称、版本信息得到 Leo 确认。

### O06-01 文档命令验收

- [x] quickstart 中的 version/help/config/demo 无网络命令在 wheel 和 sdist fresh venv 逐条执行；metadata/license/entrypoint 与卸载后 import 也已检查。
- [x] contributor 命令在 hosted CI 的干净 checkout 执行。
- [x] ALFWorld/live provider 命令标明前提、预计调用和未运行状态，不把模板写成完成证据。
- [x] 扫描 broken links、旧 Python 版本、旧测试计数、作者绝对路径和“BLM 已实现”等过期表述。
- [x] 历史报告不重写；通过当前索引解释其时间和支持边界。

O06 exit：新用户无需私有上下文即可完成零模型路径；贡献者知道如何接组件、测试和报告限制。

## 9. O07：安全、维护与 Alpha Release Packet

### O07-00 执行与路径边界

- [x] 核心不接受任意 Python import path、shell command 或外部代码自动执行；研究脚本需要显式 checkout/path。
- [x] output root、run ID、checkpoint 和 artifact path 均做 containment 检查。
- [x] 模型/skill 文本视为数据，不允许其直接改变文件路径、命令或 credential source。
- [x] 非法路径、symlink、只读目录和并发写入产生明确失败，不能破坏已有 raw evidence。

### O07-01 凭证、网络、预算与失败

- [x] 日志和异常统一脱敏 API key、Authorization、cookie 和 credential-like 值；HTTP 错误体限制长度并脱敏。
- [x] 每个 live backend 有显式 timeout、有限 retry/backoff、max tokens 和 run-level 调用/费用上限。
- [x] retry 只处理可重试错误；认证/配置/解析错误不盲目重试。
- [x] API error、timeout、budget exhausted、cancelled 写入失败证据，但不进入 valid result 计数。
- [x] Ctrl-C/取消行为保留已完成记录，resume 不重复计数；writer 与 cancellation fixture 覆盖该边界。

### O07-02 维护与依赖治理

- [x] 检查 CI 权限、固定 action commit、依赖来源和 optional extra；记录依赖更新与回滚步骤。
- [x] issue/PR 模板要求填写测试层、fidelity 变化、claim 变化、外部 source/commit 和已知限制。
- [x] 定义版本策略：core alpha 允许 breaking change，但必须记录 schema/API 迁移；不承诺无法履行的 SLA（见 maintenance policy）。
- [x] 每个里程碑或依赖升级后复核支持矩阵、known issues、provenance 和文档（见 maintenance policy）。

### O07-03 形成 release packet

状态：`deferred_by_owner_nonblocking`。以下项目保留为完整项目结束后的发布清单，不阻塞当前核心 G1。

- [ ] 从唯一验收 SHA 构建 source snapshot、wheel、sdist；保存制品 SHA-256。
- [ ] 附带 G0 manifest、G1 测试摘要、支持矩阵、dependency/provenance、known issues、release notes 和回滚说明。
- [ ] 验证 release packet 中不含 held research、外部数据、generated runs、credentials 或作者绝对路径。
- [ ] 回滚仅切换到上一个 tag/制品/config；不删除或改写原始运行证据。
- [ ] G1 只达到 `release-ready`。创建 tag、推送 GitHub Release 或发布 PyPI 必须由 Leo 单独确认。

O07 exit：安全门禁无 P0 finding；release packet 与验收 SHA、制品 hash、测试和文档一一对应。

## 10. G1 Exit Gate

| Gate | 必须满足的证据 | 状态 |
|---|---|---|
| G1-A 项目检查点 | G0/G1 基础已按正常项目粒度提交并推送 | verified (`fc6a446`) |
| G1-B Wheel 用户路径 | 非 repo 全新环境完成 import/version/demo/config smoke | verified |
| G1-C Sdist 用户路径 | 非 repo 全新环境完成同等级验收 | verified |
| G1-D 资源与配置 | 默认资源不依赖 checkout；配置优先级和 secret 边界通过测试 | verified |
| G1-E 支持矩阵 | 3.11/3.12 Linux + macOS 证据与 metadata/CI 一致 | verified |
| G1-F 输出契约 | manifest/trace/summary schema、identity 和状态模型通过 | verified |
| G1-G Resume/完整性 | 漂移、重复、部分写入、取消、路径逃逸测试通过 | verified |
| G1-H 测试分层 | core/packaging/integration 无意外 skip；可选层状态明确 | verified |
| G1-I Hosted CI | 验收 SHA 的必需 jobs 全部成功 | verified ([run 35158925050](https://github.com/LeoLiang-cs/SkillStack/actions/runs/35158925050)) |
| G1-J 文档 | 用户/贡献者/研究文档命令与实际状态一致 | verified |
| G1-K 安全维护 | secret、路径、网络、预算、权限、依赖与回滚检查通过 | verified |
| G1-L Release packet | 正式制品发布整理 | deferred_by_owner_nonblocking |

判定规则：当前核心 G1 要求 G1-A 至 G1-K 全部 `verified`，且没有未关闭 P0 finding。G1-L 已由项目负责人移出当前范围；若未来恢复发布工作，则必须绑定同一验收 SHA，`planned` 或 `pass on a different SHA` 均不算通过。

## 11. 执行批次与停止条件

### Batch 1：O02 + O03

- 交付 package resources、配置解析、wheel/sdist acceptance 和支持矩阵。
- 若 demo 无法脱离 checkout，停止进入 O04；先收缩/修复安装承诺。
- 若 optional integration 阻塞 Python 3.11/3.12，将其隔离到历史环境，不降低 core maintained baseline。

### Batch 2：O04

- 交付统一 manifest/trace/summary、identity、resume 和状态模型。
- 若无法把旧脚本无损迁移，保留为 historical entrypoint，不用兼容层扩大稳定 API。
- identity 或 raw evidence 完整性未通过时，不进入 BLM 插桩。

### Batch 3：O05 + O06

- 交付 CI 分层、packaging test、macOS smoke 和最终用户/贡献者/研究文档。
- hosted CI 未通过时，G1 保持 in_progress；本地测试不能替代。

### Batch 4：O07 + G1 审计

- 交付安全检查、维护规则、release packet 和 G1 completion record。
- 任一 secret/path/data-loss/P0 supply-chain finding 阻断 release-ready 状态。

## 12. G1 完成记录必须包含

- 验收 commit、branch/tag 状态和 dirty-worktree 说明。
- wheel、sdist、source snapshot、policy、manifest 的 SHA-256。
- 每个平台/Python 的命令、环境、pass/fail/skip 计数和 hosted CI URL。
- package install 的工作目录证明，确认不在 repo 内。
- schema/version、resume identity、状态分支和 failure fixtures 的测试结果。
- 文档命令验收清单、known issues、unsupported/unverified 项。
- 安全检查、依赖/provenance、预算/timeout/retry 和回滚说明。
- 未执行检查必须写 `not run`，不能留空或推断为通过。

G1 completion record 建议写入执行当周的 `report/weekN/`，全局计划继续保留在 `docs/plan/`。
