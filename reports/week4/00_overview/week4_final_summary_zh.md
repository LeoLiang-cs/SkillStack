# Week 4 最终总结：跨论文 A-slot 可插拔实验

**日期：** 2026-08-27  
**本周主目标：** 固定其他责任，只替换 Acquisition/Evolution 中的 proposer，
验证 GRASP proposer 与 SkillRL updater 能否进入同一个 GRASP gate。

## 一句话结论

目前已经证明“工程上可以插”：GRASP 和 SkillRL 两个不同论文组件，都能通过
明确 adapter 接入同一个 repository 和 gate，而且不需要改写相邻 L-slot。
但还没有证明“哪个效果更好”，因为严格13/13 ALFWorld性能运行被
AgentBench/Docker环境阻塞。

## Gate完成情况

| Gate | 状态 | 当前证据 |
|---|---|---|
| I0 Source | 通过 | 两个仓库commit和原生文件已固定 |
| I1 Split | 通过 | 真实26 dev按GRASP epoch-0规则分成13/13，无重叠 |
| I2 Native gate | 通过 | 五类场景与released GRASP逐字段一致 |
| I3 SkillRL source | blocked | Azure o3 key/endpoint缺失；prompt与记录层已完成 |
| I3 substituted flow | 通过 | DeepSeek/GLM真实输出均能到达GRASP gate |
| I4 A0 GRASP | 兼容性通过 | DeepSeek下产生1个合法ADD并到达固定gate |
| I5 A1 SkillRL | 兼容性通过 | DeepSeek下产生3个合法ADD并到达固定gate |
| I6 paired compatibility | 通过 | 相同证据、library、cap和gate完成配对 |
| I6 task performance | blocked | 5060/5061服务和Docker daemon不可用 |

## 本周主要成果

1. 从论文算法中抽象出 R-A-D-C-L 五类稳定责任，并把第一轮主实验固定在
   A-slot，而不是迁移整个agent。
2. 建立 proposal envelope，只作为跨组件实验边界，不升级成统一 Skill
   Schema。
3. 实现 SkillRL→GRASP 和 GRASP→proposal 两个显式 adapter，保留原始输出、
   transform kind、loss severity和不支持语义。
4. 真实接通 GRASP `validate → fork → apply → cleanup`，继续使用 SkillStack
   原有 manifest/JSONL/summary 记录链路。
5. 完成 GRASP gate parity，发现 baseline既有error可能让0-fix候选得到
   `adjusted_score=+1` 的源码边界问题。
6. 用相同历史failure和DeepSeek完成A0/A1配对兼容性实验。
7. 比较GLM与DeepSeek替代writer：DeepSeek从105.965秒降到3.144秒，后续
   provider-substituted实验固定优先DeepSeek。

## A0/A1结构差异

A0 GRASP流程更长：分类失败、诊断、分组、写proposal。本次使用3次模型调用、
3,297 prompt tokens和约$0.00327，产生1个合法ADD。

A1 SkillRL直接把失败轨迹交给一个writer。本次使用1次调用、532 prompt
tokens和约$0.00060，产生3个合法ADD。

共同结构可以抽象为：

```text
failure evidence → optional diagnose/distill → candidate proposal → adapter → fixed gate
```

GRASP显式保留failure label和diagnosis；SkillRL把这些过程压在一次writer
调用里。

## 当前架构判断

当前结构总体合理：A-slot替换后repository和L-slot gate不需要单独改写；
native payload完整保留；失败、空输出、重名、容量满、no-op和环境阻塞都没有
被丢弃。

现在不应该扩大公共schema。真正公共的字段只有action、name、description、
content、tags、evidence IDs和provenance，已经足够支持第一轮交换。

需要修正的是实验解释：GRASP原生gate的baseline-error处理可能接受0-fix
候选。以后必须同时报告原生admission、raw fixes/errors，以及要求
`actual_fixes > 0`的单独sensitivity结果。

## 能说和不能说的结论

可以说：SkillRL ADD输出能够进入GRASP repository/gate；替换没有迫使L-slot
重写；两种A-slot算法的调用结构、成本和adapter friction明显不同。

不能说：SkillRL比GRASP效果更好；DeepSeek比GLM产生的skill质量更好；当前
结果复现了完整论文；no-change gate的no-op等于真实ALFWorld无收益。

## 按规范关闭的外部阻塞

1. Source-faithful SkillRL/o3缺少Azure key和endpoint，保留为
   `blocked_credentials`。
2. 严格13/13 task performance因AgentBench服务和Docker不可用，保留为
   `blocked_environment`。

本周其余可在当前环境内完成的代码、compatibility实验、矩阵和证据记录均已
完成。
