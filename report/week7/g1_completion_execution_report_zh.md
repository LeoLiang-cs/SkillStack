# G1 核心 Alpha 完成执行记录

- 日期：2026-09-16
- 状态：`core_complete`
- 分支：`main`
- 核心验收提交：`fc6a446`（已推送至 `origin/main`）
- 范围：O02–O07 中的核心工程、测试、文档与安全门禁

## 1. 项目决策与完成边界

项目负责人已决定按正常项目方式管理 commit/push，不拆分开源与科研 scope。G0/G1 合并视为已经完成的研究工程基础；下一阶段直接进入 BLM，完整研究和论文结束后再整理正式开源发布。`.env`、API key 和其他 credential 不得进入 Git。

因此，本轮核心 G1 可以直接收口，不需要新的人工决策。正式 release packet、tag、GitHub Release、PyPI 和 `CITATION.cff` 作者信息推迟到论文完成后；BLM 不再与这些发布事项一起延期。

## 2. 本轮完成内容

### O03 支持与依赖

- 维护矩阵覆盖 Ubuntu/macOS 与 Python 3.11/3.12；Windows 仍为 `unverified`。
- optional integration 的版本或 commit、来源、许可证观察结果和 Python 环境边界已进入 provenance 文档。
- 历史外部环境不因 core 升级而改写；不兼容项保持隔离，不降低 maintained core baseline。

### O04 输出与运行契约

- `skillstack-episode-trace-v1` 的观察、native payload、adapter events、actions、warnings、executor report 和 task source 已由 maintained offline fixture 校验。
- adapter 的 source/fidelity、native payload 与 unsupported-semantics 拒绝路径已有测试。
- JSONL writer 新增 symlink 拒绝、只读失败保护和 Linux/macOS 并发写锁；失败 append 回滚到先前完整长度。

### O05 CI 与安装验收

- CI 矩阵补齐 macOS Python 3.11，形成 Ubuntu/macOS × Python 3.11/3.12。
- core CI 不再执行已延期的 isolated public snapshot/release packet gate；发布代码本身仍由 core tests 覆盖。
- wheel/sdist fresh-environment acceptance 输出改为便携相对标识，不再写入作者绝对路径。

### O06 文档同步

- README 已标明 ALFWorld smoke 的外部数据前提、单次 reset/step、零模型调用和本轮未重跑状态。
- live-provider 命令已标明手动、可能计费、默认预算上限和本轮未重跑状态。
- 历史报告索引明确旧测试计数、Python 版本和 provider 结果只对当周有效。
- 仓库扫描发现并修复 idea-spark reference 文档缺失尾部换行和一个 broken relative link。

### O07 安全与证据完整性

- 路径 containment、非法 run ID、symlink、只读目录、并发 append、重复 episode 和 malformed tail 均有明确行为。
- `.env` 保持 ignored；Git 只允许无真实密钥的 `.env.example`。
- 正式 release packet 被标记为 `deferred_by_owner_nonblocking`，不再误报为核心 G1 阻塞。

## 3. 首次 Hosted CI 发现与修复

基础检查点 `5340b0f` 的 GitHub Actions run：

<https://github.com/LeoLiang-cs/SkillStack/actions/runs/35157897068>

失败发生在 public-repository file check，而非平台运行逻辑：46 个 reference Markdown 缺失最终换行、一个相对链接错误、五个 package acceptance JSON 含作者绝对路径。上述问题均已修复。

核心验收提交 `fc6a446` 的 GitHub Actions run：

<https://github.com/LeoLiang-cs/SkillStack/actions/runs/35158925050>

四个必需 job 全部通过：

| Hosted runner | Python | Core gate | Optional skips |
|---|---|---:|---:|
| Ubuntu x86_64 | 3.11.15 | 140 passed | 2 allowlisted |
| Ubuntu x86_64 | 3.12.3 | 140 passed | 2 allowlisted |
| macOS arm64 | 3.11.9 | 140 passed | 2 allowlisted |
| macOS arm64 | 3.12.10 | 140 passed | 2 allowlisted |

全部 cell 为 0 failures、0 errors、0 unexpected skip。Ubuntu Python 3.12 的 wheel/sdist fresh-environment acceptance 也通过：wheel SHA-256 `b5220ab65b3884c791b202c4de5a934a5dae6ba566dfb01b0a818b1e2c57b2a5`，sdist SHA-256 `a691b63d44769c6ba5d8e28f186d069ad0483fcdea2001dd6289968ab04e8840`。

## 4. 本地验收证据

- `skillstack check-repo --root .`：401 files，0 findings。
- adapter/trace/quality 定向测试：30 tests passed。
- repo-resource 与 packaged-resource demo：均通过，统一 fingerprint 为 `f5733aedcfbf0303248df0ec97bffb28e911a2f6ad0a79bde678114ce0446838`。
- Python 3.12 macOS wheel/sdist fresh-environment acceptance：通过。
- acceptance 记录：`g1_package_acceptance_g1_final_local_312.json`。
- wheel SHA-256：`e6c1652bb88322a1c7641dce5e56b1c254d0bdbc307745605301dda548eee441`。
- sdist SHA-256：`845945727e045628934b7a6ebc616d713fc2887979b8999926dc8d4e23770a43`。
- Python 3.12.13 / macOS 26.6.2 arm64 完整 core gate：140 tests passed，1 个允许的 optional-data skip，0 failures/errors，0 model/network calls。
- `preflight`、Python compile、`uv build` 与 `git diff --check`：通过。
- core gate 记录：`g1_core_gate_local_final_312.json`。
- staged credential-pattern scan：通过；仅 `.env.example` 被 Git 跟踪，`.env` 未进入提交。
- hosted matrix 与 Ubuntu packaging acceptance：通过，证据见上述 run。
- 非阻塞维护提醒：GitHub runner 提示当前 pinned `actions/upload-artifact` 使用的 Node.js 20 action runtime 已被强制迁移到 Node.js 24；artifact 上传成功，不影响本次 gate，后续依赖维护时升级 action pin。

## 5. 当前无需决策的事项

以下工作由既有约束直接决定，可继续自动完成：本地 core gate、build、文档与路径扫描、credential 检查、commit/push、hosted CI 诊断和必要修复。

未来开始对应阶段时才需要项目负责人决定：

1. 是否以及何时创建正式 alpha tag、GitHub Release 和 PyPI release。
2. `CITATION.cff` 的作者顺序、公开名称和版本信息。

这些发布事项都不需要在研究与论文完成前决定。BLM R1 calibration 使用零模型/小规模确定性路径，可按科研主线直接推进；只有进入正式模型实验前才需要确认预算。
