# SkillOps Maintenance 可插拔实验计划

**状态：** M1–M5 已完成；M6 held-out confirmation 尚未实现或启动。

**目标边界：** `GRASP/SkillRL-produced library → SkillOps maintenance → unchanged GRASP D/C host`

**SkillOps source：** `c80b05246369c0b9d82a293390ca5add675c516a`

**第一轮 fidelity：** released `MaintenanceEngine.sweep()` 的
`source_variant`，不是完整论文复现。

## 1. 研究问题

### RQ-M0：表示与往返

Week5 的 GRASP/SkillRL learned skills 能否通过显式、可审计 adapter 进入
SkillOps library，再无损返回 GRASP Markdown repository？

### RQ-M1：维护动作正确性

在只给 copied library 注入已知、字节等价 duplicate debt 时，released
SkillOps merge 能否只删除预期 clone，保留正确 survivor，并输出完整 ID map？

### RQ-M2：下游可用性

在 GRASP `SkillAwareAgent` 的检索、Top-3 选择、prompt injection、DeepSeek
backend、AgentBench environment 和 evaluator 全部不变时，raw stress library
与 maintained stress library 的任务成功、选择结果、上下文成本和错误有何差异？

RQ-M0/M1 是兼容性与正确性问题；RQ-M2 才是 performance 问题。即使 RQ-M2
没有收益，RQ-M0/M1 仍可独立成立。

## 2. 为什么第一轮只做 exact-duplicate merge

Week5 输出是自然语言行为建议：`name/description/content/tags/provenance`，没有
SkillOps 所需的完整语义 precondition、operation、artifact、validator 和
failure-mode contract。直接从文字猜这些字段会把 adapter inference 冒充论文
原生信息，还可能使 signature merge 误合并不同 skill。

第一轮采用 `opaque_fingerprint_v0`：

- 保留完整 native payload 和 provenance；
- 对 `description + content + tags` 计算稳定 fingerprint；
- SkillOps contract 只记录 host format、fingerprint 和 opaque injection action；
- 只有 fingerprint 完全相同的 controlled clones 共享 signature；
- export 时 survivor 的 Markdown bytes 不变化，只删除被合并 clone；
- `repair`、`retire`、`add_validator`、`add_adapter` 在第一真实性能 cell 中禁用。

这能忠实测试 released merge primitive 与跨论文 library boundary，但不能代表
论文的 semantic health diagnosis。fidelity 必须写成
`source_variant_opaque_contract`。

## 3. 输入 library

### L-clean：真实、无人工 debt 的 cross-paper library

只收录 Week5 通过 effectiveness sensitivity 的两个最佳候选：

- A0 `grasp-001 / infer_goal_from_task_instruction`
- A1 `skillrl-001 / use_valid_actions_only`

`skillrl-003` 虽被 native gate 接受，但 fixes=0，被 effectiveness 拒绝；
`skillrl-002` native no-op。二者保留在证据库，不进入 L-clean。

L-clean 的预期 maintenance 输出是 **no-op**。它用于检测 false merge，而不是
期待性能提升。

### L-stress：只在副本上注入 controlled duplicate debt

从 L-clean 生成确定性 clones；clone 只改变 ID/name/provenance 中的 synthetic
标记，行为 fingerprint 与 parent 完全相同。debt manifest 明确列出：

- 每个 clone 的 parent；
- 预期 survivor；
- 预期 removed ID；
- 注入前后 hashes；
- 不允许改变的原始 payload fields。

L-stress 用于 RQ-M1/M2。它测的是“明确 duplicate debt 下 maintenance 是否
工作”，不能外推到自然增长 library 的全部 technical debt。

## 4. 固定不变的下游边界

第一轮不导入 SkillOps planner。raw/maintained 两个 cell 必须共享：

1. GRASP `SkillAwareAgent` 原生选择逻辑与 `_MAX_SKILLS=3`；
2. 同一 DeepSeek Flash backend、temperature、max tokens、tool schema；
3. 同一 AgentBench controller/worker、ALFWorld task IDs 与顺序；
4. 同一 task prompt、action vocabulary、step/timeout/retry budget；
5. 同一 evaluator 与 success 定义；
6. 同一 provider history sanitizer，并单独统计清理事件；
7. 同一 repository base skeleton；唯一变化是 learned library bytes；
8. 每个 cell 使用隔离目录，禁止覆盖 Week5 run 或 source repository。

为了观察 maintenance 是否真的改变 downstream input，harness 要在不改变原生
排序结果的 wrapper 中记录每一步 selected skill IDs、scores、injected
characters/tokens。wrapper 必须先通过 parity test，证明它只记录、不改选择。

## 5. 数据 split

- **禁止**用 Week5 proposal 13 生成 maintenance 决策后再把它当独立评估集。
- Week5 dev 26 已参与 proposal 或 gate，只用于 adapter/debug，不作为新的
  confirmatory evidence。
- 第一 performance pilot 使用此前未被 A-slot 生成/gate 使用的 **val 24**。
- 只有协议、adapter 和指标全部冻结后，才允许一次性使用 **test 20** 做最终
  held-out confirmation。
- maintenance 不能读取 val/test outcome；L-stress debt manifest 在任务运行前
  由字节等价关系确定。

## 6. 分阶段实施

### M0：官方 source smoke（已在本次核查验证）

- 固定官方 commit `c80b052`。
- 13/13 tests 通过；无网络 demo 通过。
- 只说明 released API 可运行，不说明论文结果可复现。

### M1：adapter 与 no-op round trip（已完成，不调用模型）

已实现：

1. `GRASP Markdown → opaque SkillOps contract` adapter；
2. `SkillOps contract → GRASP Markdown` exporter；
3. field-level `copy/rename/construct/synthesize/drop` ledger；
4. native ID ↔ SkillOps ID ↔ output ID map；
5. source/input/output directory hash 和 immutable manifest。

实测 L-clean 包含 2 个技能；identity round trip 与 sweep 后的每个 Markdown
bytes 均完全一致，required field loss=0，released sweep 为 0 merge、0 retire、
0 repair、0 validator、0 adapter。

### M2：controlled-debt primitive test（已完成，不调用模型）

在 L-stress copy 上运行 released sweep，仅允许 exact-duplicate merge。实测 4→2
skills，只删除两个 manifest 中的 clone；merge precision=1.0、recall=1.0，两个
non-synthetic parents 都是预期 survivor，survivor bytes 不变。

### M3：unchanged-host parity（已完成，不调用模型）

- 验证 raw/maintained 使用同一 D/C source hashes 和 config。
- 验证 selection recorder 与原生 `_select_skills` 输出逐项一致。
- 验证 base skeleton、task IDs、provider config 和 evaluator hash 相同。
- 任一 required field 需要猜测或下游逻辑需要 SkillOps 特判时停止，标记
  `adjacent_rewrite_required`，不进入性能运行。

实测在 24 个 val task descriptions 上，raw/maintained 两个 library 的 recorder
与原生 `_select_skills` 均逐项一致。SkillOps planner 未导入，GRASP host 中没有
SkillOps-specific branch。selector、repository、ALFWorld evaluator/environment、
base skeleton、val split 和 provider config hashes 已冻结。

### M4：val 24 单次 pilot（已完成，由用户运行）

只跑 `raw_stress` 与 `maintained_stress` 两个 cell，replicate seed 42。检查运行
完整性、成本、选择变化和是否出现明显负作用。pilot 结果只标“初步”。

实测 48/48 episodes、0 error；raw 21/24，maintained 22/24，1 fix、0
regression。该结果是单次初步信号，不单独形成方向性结论。

### M5：val 24 三次重复 comparison（已完成，由用户运行）

若 M4 无 infra/adapter 异常，再补 seeds 7、123。报告每 seed 原始分数、
task×seed paired difference、bootstrap 95% CI、选择变化、prompt tokens、模型
调用、成本和 maintenance amortization。

实测累计 144/144 episodes、0 error；raw 63/72，maintained 64/72，3 fixes、
2 regressions。task×replicate bootstrap 95% CI 为 [−4.17, +8.33] 个百分点，
包含 0。这里的 seed 只控制任务顺序，没有设置 provider seed。

### M6：test 20 held-out confirmation（可选长任务）

只有 M0–M5 全部通过、分析口径预先冻结后才运行。不得根据 test 结果修改
adapter、debt manifest、维护规则或报告主指标。

## 7. M1–M5 已实现文件

```text
src/skillstack/adapters/grasp_to_skillops.py
src/skillstack/adapters/skillops_to_grasp.py
src/skillstack/experiments/skillops_maintenance.py
src/skillstack/experiments/skillops_performance.py
scripts/run_w6_skillops_maintenance.py
tests/test_skillops_adapters.py
tests/test_skillops_maintenance.py
tests/test_skillops_performance.py
runs/week6/w6_skillops_m1_m3/  # git-ignored 机器可读证据
runs/week6/w6_skillops_val_pilot/  # git-ignored 机器可读证据
```

SkillOps 作为 pinned external dependency 使用，不复制或改写其源码。所有操作
只针对 run directory 下的 library copy。

## 8. 由你亲手运行的长耗时命令

M1–M5 harness 已存在。下面 M4/M5 命令作为已完成运行的复现与 resume 接口
保留；不要在没有需要恢复的 checkpoint 时重复产生费用。M6 runner 尚未实现，
因此旧的 `--split test` 目标命令目前不可执行。

### 先做零成本 preflight

```bash
cd /Users/leo/Project/Research/USC/FORTIS/SkillStack
PYTHONPATH=src uv run python scripts/run_w6_skillops_maintenance.py \
  --phase preflight \
  --skillops-root /Users/leo/Project/Research/USC/FORTIS/_external/week6/SkillOps \
  --grasp-root /Users/leo/Project/Research/USC/FORTIS/_external/week5/GRASP \
  --source-run runs/week5/w5_a_slot_seed2_deepseek_flash \
  --preflight-only
```

M1–M3 preflight 实测输出 `ready=true`、两个 source commit 匹配、输入结果与 val
split 完整、`model_calls_made=false`。短阶段不需要 5060/5061、Docker 或 API key；
这些服务检查只属于未来 M4+ performance preflight。

### M4：val 24 单-seed pilot

实际完成 48 episodes、737 次模型调用、估算成本 **$0.45639**。以下命令带
`--resume`，只用于恢复中断运行。

```bash
cd /Users/leo/Project/Research/USC/FORTIS/SkillStack
PYTHONPATH=src uv run python scripts/run_w6_skillops_maintenance.py \
  --phase evaluate \
  --split val \
  --cells raw_stress,maintained_stress \
  --replicate-seeds 42 \
  --backend deepseek_v4_flash \
  --run-name w6_skillops_val_pilot \
  --resume
```

### M5：补齐三 seed

实际新增 96 episodes、1,487 次模型调用、估算成本 **$0.83576**；与 M4 合计
144 episodes、2,224 次模型调用、估算成本 **$1.29214**。

```bash
cd /Users/leo/Project/Research/USC/FORTIS/SkillStack
PYTHONPATH=src uv run python scripts/run_w6_skillops_maintenance.py \
  --phase evaluate \
  --split val \
  --cells raw_stress,maintained_stress \
  --replicate-seeds 7,123 \
  --backend deepseek_v4_flash \
  --run-name w6_skillops_val_pilot \
  --resume

PYTHONPATH=src uv run python scripts/run_w6_skillops_maintenance.py \
  --phase compare \
  --run-name w6_skillops_val_pilot
```

### M6：可选 held-out test

尚未实现，也没有可执行命令。只有在组会冻结 M6 的研究问题、主指标、停止条件
和独立输出目录后，才实现 test-only runner；不得直接复用 val 分析后调整的口径。

## 9. 验收条件

### G0：来源与隔离

- SkillOps/GRASP commits 与 manifest 一致；原 source 与 Week5 run hashes 不变。
- 所有 mutation 只发生在新 run 的 copied library。

### G1：往返安全

- L-clean identity round trip 的每个原始 Markdown SHA-256 完全一致。
- ID map 双射；0 个 required field 丢失；所有 constructed fields 有 ledger。
- L-clean sweep 为 no-op；任何 false merge 都阻止后续运行。

### G2：maintenance correctness

- 对 controlled exact clones：merge precision=1.0、recall=1.0。
- survivor 是预先指定的 non-synthetic parent。
- 只删除 debt manifest 中的 clone IDs；所有 survivor bytes 不变。
- action report 补充 released report 缺少的 identity-level old→new mapping。

### G3：单槽位边界

- raw/maintained 的 D/C source、selection、prompt template、backend、task、
  evaluator 和 budgets 哈希一致。
- recorder 与原生选择逐项 parity。
- 不引入 SkillOps planner 或 host 内 SkillOps-specific branch。

### G4：运行完整性

- 每个声明 cell 的 task×seed checkpoint 完整，0 正式 episode error。
- raw request/response、selected IDs、usage、cost、stop status、tool-history
  sanitizer events 和失败均保留；summary 可由 raw records 重建。

### G5：结果解释

- compatibility、fidelity、maintenance correctness、task performance 和成本
  分开报告。
- 完整运行即为实验验收；负结果或零结果不能被删除。
- 只有 paired 95% CI 排除 0 时才写“在该 stress setting 下有方向明确的性能
  差异”；否则写“不确定/无可分辨差异”。
- 即使性能改善，也只能归因于 controlled exact-duplicate maintenance under
  unchanged GRASP host，不能声称复现完整 SkillOps 或证明一般 maintenance 优势。

## 10. 停止条件

出现以下任一情况立即停止长跑并保留状态：

1. adapter 必须猜测 semantic P/O/A/V/F 才能继续；
2. L-clean 出现非预期 merge 或 byte drift；
3. 需要修改 GRASP selector/executor/evaluator 才能消费 maintained library；
4. val/test outcome 泄漏到 maintenance decision；
5. source commit、task split、backend 或预算与 manifest 不符；
6. 原始输出或 ID mapping 无法保留；
7. 预计成本超过阶段上限，或正式 episode error 非零。

## 11. 后续扩展边界

只有 exact-duplicate merge 跑通后，才考虑 `semantic_contract_v1`：利用
SkillStack canonical interface 明确表示 `goal_operation`、
`required_transformation` 和 `procedure`，逐项检验 add-validator、repair 和
adapter。那将是新的实验轴，需要新的 fidelity 标签与单独批准，不能静默加入
第一轮。
