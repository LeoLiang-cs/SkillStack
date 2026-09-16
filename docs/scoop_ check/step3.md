# Step 3 — Abstract-Level Triage

- **Timestamp:** 2026-09-08T20:53:41-07:00
- **Scoring rule:** overlap score counts plausible matches on problem framing, core mechanism, key insight, and application domain. It is triage, not the final verdict.

## Structured papers

1. **SkCC: Portable and Secure Skill Compilation for Cross-Framework LLM Agents**
   - Date: 2026-05
   - Problem framing: the same `SKILL.md` behaves differently across coding-agent frameworks and otherwise requires per-framework rewrites.
   - Core mechanism: parse to a strongly typed SKIR, apply compile-time security passes, then emit framework-native artifacts.
   - Key insight: an intermediate representation decouples skill semantics from framework-specific prompt syntax.
   - Application domain: reusable skills across Claude Code, Codex CLI, Gemini CLI, and Kimi CLI on SkillsBench.
   - Overlap score: **3/4** (problem, insight, domain; mechanism differs).
   - Source: https://arxiv.org/abs/2605.03353

2. **Evaluating Skills, Not Just Agents: Agentic Continuous Evaluation of Skills**
   - Date: 2026-08
   - Problem framing: determine whether a skill/package helps a live agent under a fixed model, sandbox, workspace, and scorer.
   - Core mechanism: ACES paired with-skill/without-skill trials, ATIF-normalized trajectories, six metrics, and Skill Lift.
   - Key insight: scan-only quality is not runtime value; marginal skill value is conditional on the declared harness and workspace.
   - Application domain: enterprise/public skills across multiple coding-agent harnesses.
   - Overlap score: **2/4** (evaluation framing and domain).
   - Source: https://arxiv.org/abs/2608.20614

3. **Understanding Multi-Agent LLM Frameworks: A Unified Benchmark and Experimental Analysis**
   - Date: 2026-02
   - Problem framing: isolate how architectural/framework choices affect performance when models and tasks are controlled.
   - Core mechanism: MAFBench taxonomy plus common interfaces and one-dimension-at-a-time studies of orchestration, memory, planning, specialization, and coordination.
   - Key insight: interfaces and execution semantics, not only model quality, drive agent behavior and cost.
   - Application domain: single- and multi-agent LLM frameworks, not skill libraries specifically.
   - Overlap score: **3/4** (framing, mechanism at a higher level, insight; domain differs).
   - Source: https://arxiv.org/abs/2602.03128

4. **Evidence-Calibrated Runtime Reconstruction for Agent Skills Across Heterogeneous Coding Agents**
   - Date: 2026-08
   - Problem framing: reconstruct skill lifecycle boundaries from incomplete, harness-specific telemetry without inventing observations.
   - Core mechanism: versioned adapters, immutable raw events, evidence graph, Run Panorama, four evidence grades, executable adapter qualification.
   - Key insight: event presence is not boundary fidelity; unsupported semantics must remain unknown and adapter capabilities must be measured.
   - Application domain: agent skills across Codex, OpenCode, and Qoder coding agents.
   - Overlap score: **3/4** (problem/insight/domain; mechanism is observability, not swaps).
   - Source: https://arxiv.org/abs/2608.08793

5. **Harnessing Agent Skills: Architectural Patterns and a Reference Architecture for Skill-Mediated LLM Agents**
   - Date: 2026-06
   - Problem framing: identify the responsibilities that turn a static skill artifact into bounded, attributable skill-in-use.
   - Core mechanism: multivocal review of 37 systems/51 papers, ten patterns, four-layer reference architecture, cross-instantiation on eight systems.
   - Key insight: skill behavior arises through mediation, execution control, and evidence/feedback rather than from the artifact alone.
   - Application domain: skill-mediated LLM agents.
   - Overlap score: **3/4** (framing, insight, domain; no executable swap/factorial mechanism in the available abstract).
   - Source: https://doi.org/10.2139/ssrn.6871959

6. **Does Memory Credit Travel? Paired Factorial Audits of LLM-Agent Memory**
   - Date: 2026-07
   - Problem framing: distinguish outcome after retrieval from a candidate memory's marginal contribution and test whether that contribution travels across banks/decoders.
   - Core mechanism: capability-first, outcome-hidden, six-cell factorial on ALFWorld with fixed source pairs and replay-bootstrap analysis.
   - Key insight: retrieved artifacts can receive passenger credit; context can change marginal effects without obvious sign inversions.
   - Application domain: external memories in ALFWorld LLM agents.
   - Overlap score: **3/4** (framing, factorial insight/mechanism, embodied-agent domain; not multi-slot skill architecture).
   - Source: https://doi.org/10.2139/ssrn.7160321

7. **Toward User Comprehension Supports for LLM Agent Skill Specifications**
   - Date: 2026-05
   - Problem framing: whether skill specifications support bounded user expectations about inputs, outputs, and scope.
   - Core mechanism: rule-based coding of 878 skill specs for four comprehension anchors.
   - Key insight: missing examples and boundary disclosures force consumers to inspect helper code to recover operational contracts.
   - Application domain: cybersecurity agent skills.
   - Overlap score: **2/4** (interface insight and skill domain).
   - Source: https://arxiv.org/abs/2605.19362

8. **Contractual Skills: A GovernSpec Design Framework for Enterprise AI Agents**
   - Date: 2026-05
   - Problem framing: make goals, inputs, permissions, evidence, outputs, verification, and handoffs explicit in skills.
   - Core mechanism: GovernSpec-inspired readable task contracts and offline A/B evaluations.
   - Key insight: a skill can serve as a governance contract, distinct from MCP/tool/runtime layers.
   - Application domain: enterprise `SKILL.md` artifacts.
   - Overlap score: **2/4** (interface/representation and domain).
   - Source: https://arxiv.org/abs/2605.22634

9. **Agentic Skill Discovery**
   - Date: 2024-05
   - Problem framing: acquire a diverse robotic skill library without a sufficient initial library.
   - Core mechanism: LLM-generated tasks/rewards plus RL skill learning and VLM verification.
   - Key insight: proposal-driven exploration can grow meaningful robotic behaviors from zero skills.
   - Application domain: language-conditioned robot control.
   - Overlap score: **1/4** (acquisition responsibility only).
   - Source: https://arxiv.org/abs/2405.15019

10. **Skill-SD: Skill-Conditioned Self-Distillation for Multi-turn LLM Agents**
    - Date: 2026-04
    - Problem framing: improve sample efficiency of RL for long-horizon agents.
    - Core mechanism: trajectory-to-skill summaries condition a privileged teacher with importance-weighted reverse-KL distillation.
    - Key insight: dynamic training-only skills give denser supervision without appearing in student inference prompts.
    - Application domain: AppWorld and Sokoban agents.
    - Overlap score: **1/4** (skill acquisition/evolution neighborhood).
    - Source: https://arxiv.org/abs/2604.10674

11. **Progressive Agent Skill Generation via Reinforcement Learning**
    - Date: 2026-08
    - Problem framing: generate useful skills when direct correctness supervision is unavailable.
    - Core mechanism: sequential skill edits with rollback reward based on downstream execution under original versus edited skills.
    - Key insight: individually evaluable edits provide a learning signal for skill construction.
    - Application domain: document-to-skill and experience-to-skill generation on CL-Bench and tau2-bench.
    - Overlap score: **1/4** (acquisition slot only).
    - Source: https://arxiv.org/abs/2608.01678

12. **Task Decomposition-Guided Reranking for Adaptive Agent Skill Retrieval (SkillReranker)**
    - Date: 2026-07
    - Problem framing: retrieve state-appropriate skills from a large library.
    - Core mechanism: task/skill parsing, task-state execution graph, adaptive stage-wise reranking.
    - Key insight: global text similarity misses state and subtask applicability.
    - Application domain: ALFWorld and ScienceWorld skill agents.
    - Overlap score: **1/4** (one Discovery/Selection implementation and domain).
    - Source: https://arxiv.org/abs/2607.06283

13. **GraSP: Graph-Structured Skill Compositions for LLM Agents**
    - Date: 2026-04
    - Problem framing: compose retrieved flat skills into executable long-horizon plans.
    - Core mechanism: memory-conditioned retrieval, typed DAG compilation, node verification, local repair.
    - Key insight: explicit preconditions/effects and localized repair can make skill composition reliable.
    - Application domain: ALFWorld, ScienceWorld, WebShop, and InterCode.
    - Overlap score: **2/4** (composition mechanism neighborhood and domain; not a swap harness).
    - Source: https://arxiv.org/abs/2604.17870

14. **SkillCAT: Contrastive, Assessment-Augmented and Topology-Aware Skill Self-Evolution for LLM Agents**
    - Date: 2026-06
    - Problem framing: evolve skills from successful/failed trajectories while controlling regressions and routing them for execution.
    - Core mechanism: contrastive causal extraction, assessment-gated evolution, topology-aware execution.
    - Key insight: acquisition, admission, and execution topology jointly shape skill improvement.
    - Application domain: SpreadsheetBench, WikiTableQuestions, and DocVQA.
    - Overlap score: **1/4** (composite source system mapped into several SkillStack responsibilities).
    - Source: https://arxiv.org/abs/2606.13317

15. **SkillRL: Evolving Agents via Recursive Skill-Augmented Reinforcement Learning**
    - Date: 2026-02
    - Problem framing: co-evolve agent policy and reusable external skills from experience.
    - Core mechanism: experience distillation, hierarchical SkillBank, SFT/GRPO, recursive library-policy evolution.
    - Key insight: external skill state and parametric policy can improve together.
    - Application domain: interactive/search agent tasks.
    - Overlap score: **1/4** (Acquisition/Representation/Discovery source method, not interoperability study).
    - Source: https://arxiv.org/abs/2602.08234

16. **GRASP: Gated Regression-Aware Skill Proposer for Self-Improving LLM Agents**
    - Date: 2026-05
    - Problem framing: edit a skill library from failure evidence without regressing prior successes.
    - Core mechanism: failure grouping, best-of-K proposals, held-out regression gate, versioned admission.
    - Key insight: proposal and regression-aware admission are distinct responsibilities.
    - Application domain: ALFWorld skill agents.
    - Overlap score: **2/4** (responsibility split and domain; one native proposer-gate system).
    - Source: https://arxiv.org/abs/2605.29668

17. **SkillOps: Managing LLM Agent Skill Libraries as Self-Maintaining Software Ecosystems**
    - Date: 2026-05
    - Problem framing: maintain growing skill libraries and test a maintenance layer as a drop-in transformation across downstream agents.
    - Core mechanism: typed contracts, hierarchical ecosystem graph, health diagnosis, maintenance actions, raw-versus-maintained host comparisons.
    - Key insight: maintenance benefits are method-conditional and may conflict with task-time self-repair.
    - Application domain: ALFWorld skill libraries and multiple downstream retrieval/planning baselines.
    - Overlap score: **3/4** (interchangeability framing, interaction insight, domain; mechanism is one maintenance method).
    - Source: https://arxiv.org/abs/2605.13716

18. **MUSE-Autoskill: Self-Evolving Agents via Skill Creation, Memory, Management, and Evaluation**
    - Date: 2026-05
    - Problem framing: provide an end-to-end lifecycle for creating, storing, managing, evaluating, and refining skills.
    - Core mechanism: integrated AutoSkill lifecycle with skill-specific memory/evaluation.
    - Key insight: lifecycle coordination supports continuing self-evolution and transfer.
    - Application domain: self-evolving LLM agents.
    - Overlap score: **2/4** (lifecycle framing/domain; no cross-implementation swap study).
    - Source: https://arxiv.org/abs/2605.27366

19. **Dynamic Agent Skills: A Lifecycle Survey and Taxonomy of Evolving Skill Libraries**
    - Date: 2026-07
    - Problem framing: make heterogeneous dynamic-skill systems comparable over time.
    - Core mechanism: six-sense skill taxonomy, eight-stage lifecycle, lightweight record schema, ten update operators, 124-paper audit.
    - Key insight: skill libraries are evolving learning systems; taxonomy must separate artifact kind, lifecycle stage, and evidence strength.
    - Application domain: dynamic skill libraries across agent domains.
    - Overlap score: **2/4** (reference framing and domain; survey vocabulary, not executable interface evaluation).
    - Source: https://arxiv.org/abs/2607.10113

20. **SkillDAG: Self-Evolving Typed Skill Graphs for LLM Skill Selection at Scale**
    - Date: 2026-06
    - Problem framing: retrieve/select skills at scale while evolving graph structure.
    - Core mechanism: typed-edge DAG retrieval and edit transfer with intrinsic retrieval metrics.
    - Key insight: dependency structure can improve scalable selection beyond flat retrieval.
    - Application domain: large skill libraries for LLM agents.
    - Overlap score: **1/4** (Discovery/Selection implementation and domain).
    - Source: https://arxiv.org/abs/2606.03056

21. **Graph of Skills: Dependency-Aware Structural Retrieval for Massive Agent Skills**
    - Date: 2026-04
    - Problem framing: retrieve relevant skill subgraphs from massive libraries.
    - Core mechanism: dependency-aware structural retrieval over a graph of skills.
    - Key insight: structural dependencies add signal missing from independent semantic Top-k retrieval.
    - Application domain: large LLM-agent skill repositories.
    - Overlap score: **1/4** (Discovery/Selection implementation and domain).
    - Source: https://arxiv.org/abs/2604.05333

22. **SkillsBench: Benchmarking How Well Agent Skills Work Across Diverse Tasks**
    - Date: 2026-02
    - Problem framing: measure whether curated skills improve task success across model-harness configurations.
    - Core mechanism: 87-task, eight-domain matched no-skill/curated-skill benchmark with deterministic verifiers.
    - Key insight: skill effects vary by model/harness and focused bundles can outperform larger bundles.
    - Application domain: inference-time agent skills across 18 model-harness configurations.
    - Overlap score: **2/4** (controlled skill evaluation and domain; no component swaps).
    - Source: https://arxiv.org/abs/2602.12670

23. **SWE-Skills-Bench: Do Agent Skills Actually Help in Real-World Software Engineering?**
    - Date: 2026-03
    - Problem framing: isolate marginal utility of skills in real repositories.
    - Core mechanism: 49 skills, pinned repositories, requirement-driven tasks, deterministic paired with/without-skill tests.
    - Key insight: utility is narrow and depends on domain fit, abstraction, and contextual compatibility; stale guidance can hurt.
    - Application domain: software-engineering agent skills.
    - Overlap score: **2/4** (controlled skill evaluation/domain; not component interaction).
    - Source: https://arxiv.org/abs/2603.15401

24. **SkillTester: Benchmarking Utility and Security of Agent Skills**
    - Date: 2026-03
    - Problem framing: evaluate whether installed skills are useful and secure.
    - Core mechanism: paired baseline/with-skill execution plus separate security probes and normalized utility/security scores.
    - Key insight: comparative utility and security require different evidence channels.
    - Application domain: public agent skills.
    - Overlap score: **2/4** (paired evaluation and domain).
    - Source: https://arxiv.org/abs/2603.28815

25. **AEVAL: From Anecdotal to Deterministic Testing for Agentic Skill Workflows**
    - Date: 2026-07
    - Problem framing: replace anecdotal skill demos with reproducible, change-triggered quality gates.
    - Core mechanism: per-skill eval contracts, automated executor, separate first-attempt grader, artifact schema, CI routing.
    - Key insight: executor self-correction can hide first-attempt failures unless execution and grading are separated.
    - Application domain: production agentic skill workflows across runtime-agnostic interfaces.
    - Overlap score: **2/4** (evaluation boundary/domain; not multi-slot composition).
    - Source: https://arxiv.org/abs/2607.16345

26. **SkillAudit: From Fixed-Suite Benchmarking to Skill-Centered Assessment**
    - Date: 2026-06
    - Problem framing: evaluate arbitrary skills outside fixed benchmark suites without conflating backbone strength and scope fit.
    - Core mechanism: capability-aligned generated tasks, isolated sandboxes, baseline comparison, static plus dynamic safety checks.
    - Key insight: assessment should be centered on the skill artifact and its intended capability.
    - Application domain: marketplace skills across occupational categories.
    - Overlap score: **2/4** (evaluation framing/domain; not component interchangeability).
    - Source: https://arxiv.org/abs/2606.22613

27. **A Framework for Evaluating Agentic Skills at Scale**
    - Date: 2026-06
    - Problem framing: let authors evaluate an arbitrary skill and study skill effects across agent-model configurations.
    - Core mechanism: synthesize skill-relevant tasks/rubrics; compare with/without-skill conditions; evaluate 500 skills and 19 configurations.
    - Key insight: instruction following, goal completion, and behavioral change are separable skill properties.
    - Application domain: real-world coding/workflow skills across proprietary and open models.
    - Overlap score: **2/4** (controlled skill evaluation/domain).
    - Source: https://arxiv.org/abs/2606.17819

28. **How Well Do Agentic Skills Work in the Wild: Benchmarking LLM Skill Usage in Realistic Settings**
    - Date: 2026-04
    - Problem framing: evaluate skill utility when agents must retrieve from a 34k-skill corpus and no hand-curated skill may exist.
    - Core mechanism: progressively realistic retrieval conditions plus query-specific/query-agnostic refinement.
    - Key insight: skill gains are fragile under retrieval noise and can approach no-skill baselines.
    - Application domain: realistic agent-skill retrieval and Terminal-Bench 2.0.
    - Overlap score: **2/4** (coupling/portability insight and domain; no cross-component harness).
    - Source: https://arxiv.org/abs/2604.04323

29. **AgentSquare: Automatic LLM Agent Search in Modular Design Space**
    - Date: 2024-10
    - Problem framing: reuse and recombine modules from different agent systems rather than manually designing task-specific agents.
    - Core mechanism: four-module standardized-I/O design space (Planning, Reasoning, Tool Use, Memory), module recombination/evolution, performance predictor, search over combinations.
    - Key insight: module-level standardization allows cross-codebase reuse and exposes architecture-performance effects.
    - Application domain: broad LLM agents on WebShop, ALFWorld, ScienceWorld, M3Tool, and games.
    - Overlap score: **3/4** (problem, modular mechanism/insight, broad agent domain; differs on skill-specific empirical interface induction).
    - Source: https://arxiv.org/abs/2410.06153 (`model-recall + verified-arXiv`).
