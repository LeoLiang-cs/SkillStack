# R1-03 BLM boundary-atom census 清单

- 状态：`PLANNED`（执行期间逐项改为 `VERIFIED`）
- 依赖：R1-02 exact first-handoff replay
- 固定 Consumer：`skill_plan_executor`

## 目标与排除

本阶段冻结 C1 中每个字段/组的 declared semantics、transport、真实读取类型和可干预性。轻量 wrapper 只记录 Python Consumer 的 mapping membership、field getitem、list index 事件；不声称观察模型内部读取，也不增加 Consumer read。

## 执行清单

### R1-03-00 census contract

- [ ] 固定 `skillstack-blm-atom-census-v1` schema。
- [ ] 每条记录包含 carrier path、read-map、静态表达式/digest、runtime sequence/count、read type、值域、group/intervenability、donor、trace exposure、evidence class 和 claim boundary。

### R1-03-01 默认关闭 read tracker

- [ ] 在 `blm.py` 增加 v2 sidecar `consumer_reads`，保留 v1 行为。
- [ ] input hash 在包装前计算；dict/list wrapper 保持值、顺序、控制流和类型契约。
- [ ] 只在 opt-in v2 请求下追踪，default-off 无 sidecar。

### R1-03-02 冻结 census

- [ ] 记录 identity semantic read、top-rank group、score validation-only、native opaque unread、flat derived unread。
- [ ] local registry 记录为 `static_verified_runtime_indirect`，不伪造 runtime event。
- [ ] task/observation/admissible commands 标记为 environment state，不是 D→C payload。
- [ ] 生成 `configs/blm/r1_03_atom_census.json` 与研究文档。

### R1-03-03 测试

- [ ] 四字段均出现 validation membership；只有 `selected_skill_ids[0]` 出现 semantic index read。
- [ ] 3× sequence exact；top-k>1 只读 index 0；空 list 不伪造 index。
- [ ] wrapper、default-off 和完整行为投影 exact。
- [ ] 未知/重复 atom、缺 read-map 或动态/静态冲突 fail-closed 为 `blocked_atom_census_mismatch`。

### R1-03-04 证据与出口

- [ ] 生成 atom census evidence、completion record 和 local gate JSON。
- [ ] 未执行项目写 `not run`。

## Exit Gate

每个候选信息都可追溯到真实读取或明确不可观察边界；no-op instrumentation exact；unread probe 与 census 一致；未增加 Consumer read；local gate、credential scan、push 和 hosted CI 有实际记录。失败状态：`blocked_atom_census_mismatch`。
