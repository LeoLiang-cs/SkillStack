# R1-05 BLM bounded verdict calibration 清单

- 状态：`VERIFIED`
- 执行 SHA：`5cd55912aa14acefe6ec07f60ea9da989fed183e`
- 依赖：R1-02 replay、R1-03 census、R1-04 controls
- 研究边界：确定性校准，不是自然案例或正式模型实验

## 目标与排除

本阶段把已执行的 deterministic calibration 记录映射为有限范围的 `falsified`、`not_falsified` 或 `abstained`。不生成 `supported`，不产生一般充分性结论，不运行网络、模型、训练、ALFWorld benchmark 或统计显著性分析。

## 执行清单

### R1-05-00 verdict record

- [x] 实现纯函数 `evaluate_calibration_case(case_record)`，输出 `skillstack-blm-verdict-v1`。
- [x] 分开保存 `measurement_status` 与 `contract_verdict`；invalid/abstained 永不产生 falsified。
- [x] 无显式、可证伪且有限 scope 的 claim 时只能 abstain。
- [x] 一般 C1 没有充分性主张；falsified 只允许 test-only synthetic claim。

### R1-05-01 固定案例

- [x] 生成 `configs/blm/r1_05_verdict_calibration.yaml`。
- [x] 覆盖 identity、unread、adapter deletion、opaque carrier、synthetic joint-only、invalid donor/type/group、replay drift、no-op drift、中断和 budget exhausted。

### R1-05-02 可恢复运行

- [x] `scripts/run_blm_calibration.py` 提供 run/resume/summarize。
- [x] 复用 manifest identity、append-only JSONL、确定性 episode ID 和 duplicate rejection。
- [x] resume 跳过完整 episode；manifest 漂移拒绝；summary 从 raw 重算且不覆盖 raw。

### R1-05-03 测试与报告

- [x] 新增 `tests/test_blm_r1_05_verdicts.py`，逐案断言预期结果。
- [x] raw → summary → verdict 可独立重算；缺 arm、不完整或中断不能算完成。
- [x] 输出不含 `supported`，synthetic 与 C1 evidence 严格分离。

### R1-05-04 R1 总出口

- [x] 生成 `report/week7/r1_05_calibration_run/` 下 manifest、episodes、summary、verdicts。
- [x] 生成 completion record 和 local gate JSON；未执行项目写 `not run`。
- [x] master plan、`docs/plan/README.md` 更新为 `complete_calibration_only`、R2 next。

## Exit Gate

R1-02～R1-04 全部 verified；预定义案例得到预期 bounded verdict；raw evidence 可重算；完整本地质量/credential gate、正常 push 和 hosted CI 全部实际通过。出口状态只能是 `complete_calibration_only`，不得写成 BLM 已有效、具有 novelty 或发现普遍隐藏依赖。
