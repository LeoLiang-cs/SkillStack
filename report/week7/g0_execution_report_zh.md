# Week 7：G0 发布隔离执行报告

- 日期：2026-09-15
- 对应计划：[G0 发布隔离完成计划清单](../../docs/plan/g0_release_isolation_plan_list_zh.md)
- 对应任务：O01 / G0
- 报告状态：`implementation_verified`；正式 G0 gate 尚未在项目 commit 上签字
- 关键边界：本轮没有创建项目 commit、tag、GitHub Release，也没有启动 BLM 长实验。

## 1. 本轮完成的实现

### 发布范围与身份

- 新增 `configs/public_release_scope.yaml`，把文件分成 `public`、`held_research`、`external_data`、`generated` 四类；未匹配路径默认为 `unknown` 并排除。
- `src/skillstack/release.py` 已改为从指定 Git ref 解析完整 commit SHA，再从该 commit 的 Git tree 读取 blob；不再从 dirty worktree 递归复制 `docs/`、`reports/`。
- 每个候选生成逐文件 `mode`、Git object ID、字节数、SHA-256，以及整体 `content_sha256`、`manifest_sha256` 和策略 hash。
- 对 symlink、非普通文件 mode、策略路径穿越、非法策略和缺少必需文件采用 fail-closed 行为。
- `release-check` 与 `scripts/check_fresh_clone.py` 增加 `--ref`；输出包含 resolved commit、dirty-worktree 路径、manifest、制品检查和各 gate 状态。

### 测试与制品检查

- `tests/test_release.py` 改为使用独立临时 Git fixture，覆盖未 tracked 文件、held/external/generated 文件、dirty tracked 修改、symlink、路径穿越、重复 manifest 和 CLI ref。
- fresh-clone gate 在 `uv build` 后读取 wheel/sdist 成员，不解压不可信路径；检查绝对路径、`..`、held research、论文/外部数据、生成目录和 pycache。
- 已同步更新 `docs/open_source/RELEASE_SCOPE.md`、`PUBLICATION_AUDIT.md`、release notes 和 `CHANGELOG.md`，明确当前策略与“临时候选通过、项目 HEAD 待提交”的状态。
- 不增加第三方依赖；继续复用已有 PyYAML、Git、`tarfile`、`zipfile` 和 hashlib。

## 2. 实际验证结果

### 本地工作区测试

| 检查 | 结果 |
|---|---|
| `uv run python -m compileall -q src tests` | PASS |
| `uv run python -m unittest discover -s tests -q` | PASS：112 passed，1 conditional skip |
| `uv run skillstack check-repo --root .` | PASS：254 files，0 findings |
| `git diff --check`（实现修改文件） | PASS |
| 当前工作区的 public repository quality 检查 | PASS（包含在完整测试中） |

### 当前 `HEAD` 的预期阻断

执行：

```text
uv run skillstack release-check --root . --ref HEAD
```

结果为 `fail`，原因是当前项目 `HEAD` 尚未包含新策略文件：

```text
cannot read Git blob <current-head>:configs/public_release_scope.yaml
```

这是正确的 fail-closed 行为，不是将工作区策略偷偷用于旧 commit。执行当时检测到 331 条 dirty/untracked 路径；它们没有被复制进该旧 `HEAD` 的候选。

### 临时候选 commit 的完整 gate

为验证实现本身，我在 `/tmp` 建立了临时候选仓库：以当前 `HEAD` 为基底，只叠加本轮 G0 代码、策略、测试和脚本，然后创建临时 commit。该 commit 不属于本项目分支，也不是发布 tag。

| 项目 | 结果 |
|---|---|
| resolved commit | `2ad50819c55d8586ffb58cfc15454645e97a0dec` |
| source snapshot files | 244 |
| source bytes | 1,264,916 |
| content SHA-256 | `d6dde494daff17d2ae65f70c7187dd31ee84cfdedfeaf1aa5fa9ef005e18fde5` |
| manifest SHA-256 | `742b10475446de84c66f71f9e24e8977c010cc2eaad4cd14948d5c4bb3b00d8b` |
| policy SHA-256 | `f948110995eddc9d364458b41196e105921728d446d7f5fcc702c3a1f45b75f7` |
| `uv sync --frozen` | PASS |
| zero-model preflight | PASS |
| public repository scan | PASS：238 files，0 findings |
| zero-model demo | PASS |
| compileall | PASS |
| fresh-clone tests | PASS：112 passed，2 skipped |
| wheel | PASS；91,330 bytes，0 forbidden/unsafe members |
| sdist | PASS；91,006 bytes，0 forbidden/unsafe members |
| license gate | PASS |
| SkillStack network/model calls | 0 / 0 |
| 总 technical/artifact gate | PASS |

完整临时 gate 的退出判定是 `status=pass`；它证明实现可工作，但不等同于项目 G0 已完成。

## 3. G0 退出表

| Gate | 当前状态 | 说明 |
|---|---|---|
| G0-A 来源身份 | `verified-on-temp-candidate` | commit-based collector 已验证；项目正式 SHA 尚未形成 |
| G0-B 范围策略 | `verified-on-temp-candidate` | 策略 schema、分类和 required files 已验证 |
| G0-C 工作区隔离 | `verified` | fixture 证明 untracked/dirty 修改不改变指定 commit manifest |
| G0-D held/unknown 隔离 | `verified-on-temp-candidate` | 候选及 wheel/sdist 未出现 forbidden members |
| G0-E 路径安全 | `verified` | symlink、路径穿越、非法 mode 测试通过 |
| G0-F 可复核身份 | `verified-on-temp-candidate` | file hash、content hash、manifest hash、policy hash 齐全 |
| G0-G 可重复性 | `verified` | 同一 commit fixture 生成的文件和 hash 一致 |
| G0-H 零模型候选检查 | `verified-on-temp-candidate` | fresh clone、preflight、scan、demo、tests、build 全通过 |
| G0-I 文档一致性 | `verified-on-working-tree` | scope、audit、release notes 和 changelog 已与当前策略和状态同步；最终 commit 尚未形成 |
| G0-J 差异解释 | `pending` | 需要窄范围 commit，并由 Leo 确认其余 dirty 路径均不进入发布 |

因此，当前总状态为：**G0 实现、测试和文档已完成并通过临时候选验证；正式 G0 尚未完成。**

## 4. 下一步

1. 只暂存 G0 预定文件：策略、`release.py`、CLI/script、release tests、发布文档和本报告；不暂存当前研究材料。
2. 创建窄范围项目 commit 后运行：

   ```text
   uv run skillstack release-check --root . --ref <resolved-commit-sha>
   ```

3. 只有该项目 commit 的 G0-A 至 G0-J 全部通过，才将 O01 标记为 `verified` 并进入 G1/O02。

当前不启动 BLM 正式实验；BLM 仍保持“拟实现研究方法”的状态边界。
