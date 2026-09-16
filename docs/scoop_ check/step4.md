# Step 4 — Identify High-Potential Candidates

- **Timestamp:** 2026-09-08T20:53:41-07:00
- **Candidate cap:** 7

## Selected candidates

1. **AgentSquare** — score 3; directly defines cross-paper/cross-codebase modular recombination with standardized I/O and evaluates combinations on ALFWorld and other agent benchmarks. This is the closest conceptual predecessor to SkillStack's modular harness.
2. **Understanding Multi-Agent LLM Frameworks / MAFBench** — score 3; introduces an architectural taxonomy and controlled evaluation pipeline that isolates framework-level design dimensions under fixed models/tasks. It threatens the “architecture-level controlled comparison” part of the claim.
3. **SkCC** — score 3; directly targets skill portability across frameworks using an IR and emitters. It threatens the “cross-system skill interface/adapter” part of the claim, although its schema-first compiler is technically opposite to SkillStack's empirical schema-later route.
4. **SkillOps** — score 3; treats maintenance as a drop-in library transformation, compares raw/maintained libraries across seven downstream agents, and reports method-conditional effects. It is the closest prior art inside the exact skill-library domain for one replaceable slot.
5. **Harnessing Agent Skills** — score 3; derives a skill-specific reference architecture and architectural patterns across systems. It threatens the “reference architecture” contribution, but the available abstract describes cross-instantiation rather than executable swaps.
6. **Evidence-Calibrated Runtime Reconstruction for Agent Skills** — score 3; qualifies versioned adapters across heterogeneous coding agents and makes hidden lifecycle/telemetry boundaries explicit. It threatens the “adapter friction/interface leakage” framing, but is an observability system rather than a component-composition experiment.
7. **Does Memory Credit Travel?** — score 3; uses ALFWorld paired factorial experiments to test whether the marginal value of a retrieved external artifact changes across banks and decoders. It threatens the factorial/interaction methodology, but studies one memory-credit question rather than a multi-slot skill architecture.

## Why score-2 papers were not promoted

ACES, SkillsBench, SWE-Skills-Bench, SkillTester, AEVAL, SkillAudit, and the Tessl framework are important evaluation neighbors, but they primarily compare the presence/absence or quality of a skill artifact. They do not swap one implementation for another inside a fixed skill-agent responsibility, nor do they derive a shared interface from adapter losses. Dynamic Agent Skills is a major taxonomy/reference source, but it explicitly remains a survey and does not execute cross-implementation composition tests.
