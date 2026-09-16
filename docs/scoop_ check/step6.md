# Step 6 — Compare Against the Proposed Novelty

- **Timestamp:** 2026-09-08T20:53:41-07:00

- **Proposed work**
  - Title: SkillStack: A Reference Architecture and Experimental Framework for Composable Skill Agents
  - Date: —
  - Source: `SkillStack_Draft_Framework.md` and Week-4/5 reports
  - Problem framing: Under fixed tasks, library, host, evaluator, budget, and neighboring components, can implementations from different skill-agent systems replace and compose with one another, and what hidden semantics explain failures?
  - Core mechanism: R-A-D-C-L responsibilities; four replaceable slots; native artifacts plus explicit adapters; cross-paper one-slot swaps; pairwise factorial interactions; friction/loss ledger; empirically derived canonical interface.
  - Key insight: syntactic compatibility is not semantic composability; executable crossings reveal hidden state, authority, applicability, and evidence assumptions that should determine the minimum shared interface.
  - Application domain: procedural-skill LLM agents, initially text-only ALFWorld, with later cross-environment extension.

- **Prior work A**
  - Title: AgentSquare: Automatic LLM Agent Search in Modular Design Space
  - Date: 2024-10
  - Source: https://arxiv.org/abs/2410.06153
  - Problem framing: recombine modules from existing agent systems to optimize new agents.
  - Core mechanism: predefined Planning/Reasoning/Tool/Memory I/O, module evolution/recombination, predictor-guided search.
  - Key insight: standardized modules enable cross-codebase recombination and architecture search.
  - Application domain: broad agents across ALFWorld, WebShop, ScienceWorld, tools, and games.
  - Axes matching: **3/4** (problem, modular mechanism/insight, broad agent domain; empirical skill-interface induction differs).
  - Level: **Level 2 — High Overlap (one axis differs).**

- **Prior work B**
  - Title: Understanding Multi-Agent LLM Frameworks: A Unified Benchmark and Experimental Analysis
  - Date: 2026-02
  - Source: https://arxiv.org/abs/2602.03128
  - Problem framing: isolate architecture effects across heterogeneous frameworks under controlled conditions.
  - Core mechanism: architecture taxonomy, common benchmark pipeline, one-dimension-at-a-time studies.
  - Key insight: interfaces/execution semantics can dominate model quality.
  - Application domain: multi-agent frameworks, not external skill libraries.
  - Axes matching: **3/4** (problem, controlled modular evaluation, insight; domain differs).
  - Level: **Level 2 — High Overlap (one axis differs).**

- **Prior work C**
  - Title: SkCC: Portable and Secure Skill Compilation for Cross-Framework LLM Agents
  - Date: 2026-05
  - Source: https://arxiv.org/abs/2605.03353
  - Problem framing: make one skill portable across frameworks with different prompt-format preferences.
  - Core mechanism: schema-first SKIR compiler, security optimizer, and target emitters.
  - Key insight: an IR decouples semantics from target syntax.
  - Application domain: `SKILL.md` artifacts across coding-agent frameworks.
  - Axes matching: **3/4** (problem/insight/domain; core mechanism differs).
  - Level: **Level 2 — High Overlap (one axis differs).**

- **Prior work D**
  - Title: SkillOps: Managing LLM Agent Skill Libraries as Self-Maintaining Software Ecosystems
  - Date: 2026-05
  - Source: https://arxiv.org/abs/2605.13716
  - Problem framing: maintain a growing library and apply maintenance as a drop-in transformation across downstream consumers.
  - Core mechanism: typed contracts, ecosystem graph, health diagnosis, maintenance actions, raw/maintained comparisons.
  - Key insight: component benefit is conditional on the downstream method and may conflict with self-repair.
  - Application domain: ALFWorld skill libraries and several downstream agents.
  - Axes matching: **3/4** (problem/insight/domain; one maintenance method rather than a multi-slot harness).
  - Level: **Level 2 — High Overlap (one axis differs).**

- **Prior work E**
  - Title: Harnessing Agent Skills: Architectural Patterns and a Reference Architecture for Skill-Mediated LLM Agents
  - Date: 2026-06
  - Source: https://doi.org/10.2139/ssrn.6871959
  - Problem framing: identify responsibilities between static skill artifacts and run-specific skill-in-use.
  - Core mechanism: multivocal review, ten patterns, four-layer reference architecture, cross-instantiation.
  - Key insight: mediation, control, and evidence responsibilities determine operational skill meaning.
  - Application domain: skill-mediated LLM agents.
  - Axes matching: **3/4** (problem/insight/domain; no executable cross-component swap mechanism in available evidence).
  - Level: **Level 2 — High Overlap (one axis differs).**

- **Prior work F**
  - Title: Evidence-Calibrated Runtime Reconstruction for Agent Skills Across Heterogeneous Coding Agents
  - Date: 2026-08
  - Source: https://arxiv.org/abs/2608.08793
  - Problem framing: recover lifecycle boundaries from heterogeneous harness evidence and qualify adapter semantics.
  - Core mechanism: passive versioned adapters, evidence graph, Panorama, evidence grades.
  - Key insight: event presence and schema-valid output do not prove boundary fidelity; unsupported meaning must remain unknown.
  - Application domain: skills across three coding agents and six repository profiles.
  - Axes matching: **3/4** (problem/insight/domain; observability rather than component swaps).
  - Level: **Level 2 — High Overlap (one axis differs).**

- **Prior work G**
  - Title: Does Memory Credit Travel? Paired Factorial Audits of LLM-Agent Memory
  - Date: 2026-07
  - Source: https://doi.org/10.2139/ssrn.7160321
  - Problem framing: determine whether an external artifact's marginal contribution transports across banks and decoders.
  - Core mechanism: capability-first six-cell ALFWorld factorial with matched effects and interaction-style quantities.
  - Key insight: success after retrieval can be passenger credit; context changes marginal contribution.
  - Application domain: external memory in ALFWorld LLM agents.
  - Axes matching: **3/4** (problem/factorial insight/mechanism; not multi-slot skill architecture).
  - Level: **Level 2 — High Overlap (one axis differs).**

## Overall mapping

The minimum level across candidates is **Level 2 — High Overlap**. No candidate matches all four axes, but several match three; therefore the contribution is not safely publishable as a broad claim such as “the first modular/reference architecture for composable agent skills.”
