# Step 5 — Full-Paper Deep Dive on Candidates

- **Timestamp:** 2026-09-08T20:53:41-07:00
- **Retrieval note:** The bundled `fetch_paper.sh` downloaded valid PDFs but its configured `pdftotext/pdfplumber/pymupdf` extractors were unavailable. Text was therefore extracted locally with the installed `pdf2txt.py` fallback. SSRN blocked both paper pages with Cloudflare HTTP 403; those two records are explicitly abstract-only and are not represented as full-paper reads.

## 1. AgentSquare

- **Problem framing (verified):** Automatically reuse/recombine agent modules from different published systems rather than manually build a task-specific agent. Inputs are pools of Planning/Reasoning/Tool Use/Memory modules; output is an optimized agent; evaluated on six web, embodied, tool-use, and game benchmarks including ALFWorld.
- **Core mechanism (verified):** A predefined four-module design space with uniform callable I/O; module recombination replaces modules from the pool, module evolution writes new code-level modules, and a performance predictor skips unpromising combinations.
- **Key insight (verified):** A standardized modular design space makes cross-codebase recombination searchable and can exploit prior successful components.
- **Application domain (verified):** General single-agent architecture search across WebShop, ALFWorld, ScienceWorld, M3Tool and games.
- **Venue (verified):** arXiv preprint 2410.06153; the PDF says it was under review as an ICLR 2025 conference paper, so no acceptance is claimed here.
- **Assumptions & scope:** Interfaces are fixed before search; modules are normalized into four coarse categories; success is optimization performance, not semantic fidelity to native artifacts. It does not maintain an adapter-loss ledger or test whether a paper-native method retains meaning after translation.
- **Closest-passage evidence:** Abstract and §2 state that Planning, Reasoning, Tool Use, and Memory use a uniform I/O interface; §3.4–3.5 defines recombination/evolution; evaluation reports six benchmarks.
- **Refined overlap:** problem framing **match**; core mechanism **partial**; key insight **match**; application domain **partial/match**. **3 axes counted as matching.**

## 2. Understanding Multi-Agent LLM Frameworks / MAFBench

- **Problem framing (verified):** Determine how framework architecture changes performance/cost while controlling models, tasks, prompts, and data.
- **Core mechanism (verified):** A taxonomy over control flow, agent abstraction, communication, memory, and execution semantics; a common interface integrates existing benchmarks; experiments vary one architectural dimension at a time.
- **Key insight (verified):** Framework execution semantics and interfaces can dominate model quality and task difficulty.
- **Application domain (verified):** Multi-agent frameworks (LangGraph, AutoGen, CrewAI, OpenAI SDK, Agno, OpenAgents, Concordia, etc.), spanning memory, planning, specialization, coordination, and overhead.
- **Venue (verified):** arXiv preprint 2602.03128.
- **Assumptions & scope:** It compares framework-level instantiations and dimension-specific benchmark conditions. It does not preserve native skill artifacts, perform cross-paper single-slot swaps, or derive a skill interface from semantic translation failures.
- **Closest-passage evidence:** Introduction/Contributions defines the taxonomy and standardized pipeline; §4 says each study varies one framework-level dimension while holding models/prompts/data constant; §5 Principle 6 attributes behavior to system interfaces.
- **Refined overlap:** problem framing **match**; core mechanism **partial**; key insight **match**; application domain **differ/adjacent**. **3 axes counted as matching.**

## 3. SkCC

- **Problem framing (verified):** The same skill can vary substantially across coding-agent frameworks because prompt formats differ, forcing per-framework rewrites.
- **Core mechanism (verified):** Four phases: Syntax Parser, SKIR Builder, Security Optimizer, and polymorphic Target Emitters. A single canonical source is lowered into a typed IR, then emitted to framework-native formats.
- **Key insight (verified):** Compiler-style IR reduces the skill×framework adaptation problem from pairwise rewrites to shared frontends/backends and enables format-independent security checks.
- **Application domain (verified):** `SKILL.md` skills on Claude Code, Codex CLI, Gemini CLI, and Kimi CLI; 89 SkillsBench tasks plus 225 skills for engineering measures.
- **Venue (verified):** arXiv preprint 2605.03353, explicitly described in the PDF as under review.
- **Assumptions & scope:** Starts from one canonical `SKILL.md`, normalizes semantics into SKIR, and evaluates whole-skill compilation. It does not compare native acquisition/retrieval/composition/governance implementations or infer interface fields from observed cross-component failures. Limitations restrict evaluation to four frameworks, 89 programming/data tasks, and whole-file compilation.
- **Closest-passage evidence:** §3.1 defines a strongly typed semantic IR; §3.3 defines per-framework emitters; §4 compares the same skill baseline versus compiled output; Appendix E states framework/benchmark/granularity limits.
- **Refined overlap:** problem framing **match**; core mechanism **differ**; key insight **match**; application domain **match**. **3 axes matching.**

## 4. SkillOps

- **Problem framing (verified):** Growing skill libraries accrue redundancy, stale entries, missing validators, interface incompatibilities, and other technical debt; a maintenance layer should work across downstream agents.
- **Core mechanism (verified):** Typed P/O/A/V/F contracts, hierarchical ecosystem graph, task-time dependency/compatibility planning, library-time health diagnosis, typed maintenance actions, and a declared pure transformation `L' = run_maintenance(L)`.
- **Key insight (verified):** Library maintenance is a separate responsibility whose benefit depends on the downstream consumer; retrieval-heavy agents benefit more, while self-repair can conflict.
- **Application domain (verified):** ALFWorld with libraries from 200 to 2,000 skills; seven downstream retrieval/planning/self-repair baselines for the drop-in comparison.
- **Venue (verified):** arXiv preprint 2605.13716.
- **Assumptions & scope:** Requires structured contracts and sometimes gold PDDL-style arguments; library is half-synthetic and ALFWorld-centric; the paper tests one maintenance implementation, not multiple implementations per responsibility. SkillStack's Week-4 source audit further treats released primitives/full-loop fidelity separately.
- **Closest-passage evidence:** §3.4 declares a downstream-agnostic pure library transformation; §5.2 compares raw versus maintained libraries while keeping downstream code unchanged; §6 reports method-conditional effects; §7 lists structured/gold and half-synthetic limits.
- **Refined overlap:** problem framing **match**; core mechanism **partial/differ**; key insight **match**; application domain **match**. **3 axes matching.**

## 5. Harnessing Agent Skills

- **Problem framing (abstract verified):** Identify architectural responsibilities governing the transition from a static skill artifact to run-specific skill-in-use, including context/authority binding, execution consequences, and evidence for attribution/repair/evolution.
- **Core mechanism (abstract verified):** Multivocal review of 37 systems and 51 papers; ten architectural patterns; four layers—Supply Chain, Mediation, Execution Control, Evidence & Feedback; cross-instantiation on eight systems.
- **Key insight (abstract verified):** A skill's operational meaning arises through harness responsibilities around selection, binding, interpretation, and evidence—not from the artifact alone.
- **Application domain (abstract verified):** Skill-mediated LLM agents.
- **Venue (verified metadata):** SSRN posted content, DOI 10.2139/ssrn.6871959; Crossref creation date 2026-06-10. No peer-reviewed venue identified.
- **Assumptions & scope:** The available abstract presents a vocabulary/diagnostic architecture, not an executable component-swap harness or measured factorial interaction. Full text could not be retrieved because SSRN returned Cloudflare HTTP 403; no browser challenge was bypassed.
- **Closest-passage evidence:** Crossref abstract states the 37-system/51-paper review, ten patterns, four layers, and eight-system cross-instantiation.
- **Refined overlap:** problem framing **match**; core mechanism **differ**; key insight **match**; application domain **match**. **3 axes matching, abstract-only confidence.**

## 6. Evidence-Calibrated Runtime Reconstruction for Agent Skills

- **Problem framing (verified):** Reconstruct supported skill lifecycle boundaries from heterogeneous/incomplete harness telemetry while keeping unsupported stages unknown.
- **Core mechanism (verified):** Passive collectors, versioned adapters, immutable raw records, normalized event envelopes, deterministic evidence graph, Run Panorama, and Observed/Derived/Inferred/Experimental grades.
- **Key insight (verified):** Adapter outputs are measurement instruments: event presence, lifecycle attribution, boundary fidelity, and causal effectiveness are distinct claims.
- **Application domain (verified):** Six repository profiles × three coding agents × seven clean/fault conditions (126 cells), plus diagnostic studies.
- **Venue (verified):** arXiv preprint 2608.08793.
- **Assumptions & scope:** Passive observability only; does not own the agent loop, repair components, estimate causal skill effectiveness, or study natural incident prevalence. One run per external-validity cell limits variance inference.
- **Closest-passage evidence:** §2.2 R4/R6 requires versioned capability and causal restraint; §3 defines the evidence architecture; §4.2 crosses 6×3×7 conditions; §8 explicitly limits causal/generalization claims.
- **Refined overlap:** problem framing **match**; core mechanism **differ**; key insight **match**; application domain **match**. **3 axes matching.**

## 7. Does Memory Credit Travel?

- **Problem framing (abstract verified):** Test whether a retrieved external memory's marginal contribution changes with the containing bank and decoder, rather than attributing all post-retrieval success to the memory.
- **Core mechanism (abstract verified):** Capability qualification, outcome-hidden six-cell factorial on ALFWorld, fixed source pairs, 576 episodes, replay-bootstrap interval, and passenger-credit diagnostics.
- **Key insight (abstract verified):** Outcome after retrieval is not marginal contribution; background context can change a candidate's effect and hide harm.
- **Application domain (abstract verified):** LLM-agent external memory in ALFWorld using Qwen3-32B and Mistral Small 3.1-24B.
- **Venue (verified metadata):** SSRN posted content, DOI 10.2139/ssrn.7160321; Crossref creation date 2026-07-27. No peer-reviewed venue identified.
- **Assumptions & scope:** One memory candidate/bank/decoder interaction, not a multi-responsibility skill architecture; abstract explicitly does not establish controller efficacy or general non-transportability. Full text was blocked by SSRN HTTP 403; no challenge bypass attempted.
- **Closest-passage evidence:** Crossref abstract defines three executable quantities, the six-cell factorial, ALFWorld population, and the distinction among outcome, fixed-entry contribution, and credit transport.
- **Refined overlap:** problem framing **match**; core mechanism **match**; key insight **match**; application domain **partial**. **3 axes matching, abstract-only confidence.**
