# Step 1 — Decompose the Novelty

- **Timestamp:** 2026-09-08T20:53:41-07:00
- **Research problem:** 现有 Skill Agent 多以端到端系统呈现，skill representation、state abstraction、failure signal、update semantics 和执行环境相互绑定；因此难以在控制其他因素时判断跨论文组件能否替换、组合，以及组合失败究竟来自组件本身还是隐藏接口假设。
- **Inferred novelty:** SkillStack 提出一个 skill-specific reference architecture 与 modular experimental harness；保留论文原生 artifact，通过显式 adapter 做跨论文、单槽位 controlled swap 和 pairwise factorial，再从可复现的 adapter friction、semantic loss 与 interface leakage 中归纳最小 Canonical Skill Interface。

## Four atomic axes

- **Problem framing:** 输入是来自不同 Skill Agent 系统的原生组件/artifact 与固定 benchmark/host；输出是 compatibility class、performance portability、cross-module interaction、failure attribution 和候选共享接口字段；主要评价在 ALFWorld 上采用 matched controls、one-at-a-time swaps 与 hypothesis-driven pairwise factorial。
- **Core mechanism:** R-A-D-C-L 五类职责 + 四个实验槽位；native payload 保留；显式 hard-coded adapter 与 transformation/loss ledger；固定邻居的跨论文单槽位替换；交互项与失败分类；最后才冻结 Canonical Skill Interface。
- **Key insight:** “形式可接”不等于“语义可组合”。只有让不同论文实现真实接线并执行，hidden coupling、evidence authority、state/applicability semantics 和 adapter information loss 才会暴露；共享接口应由这些失败证据归纳，而不是预先想象。
- **Application domain:** 外部 procedural skill library 驱动的 LLM agents，当前实证域为 text-only ALFWorld；后续可扩展到 ScienceWorld、WebShop、coding agents 或其他 agent-skill harness。
