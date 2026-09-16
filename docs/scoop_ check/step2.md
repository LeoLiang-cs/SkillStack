# Step 2 — Search and Deduplicate

- **Timestamp:** 2026-09-08T20:53:41-07:00
- **Window:** 2024–2026
- **Query 1 — Original-Problem:** `LLM agent skill component interchangeability composability evaluation`
- **Query 2 — Broad-Domain:** `modular LLM agent architecture benchmark component evaluation`
- **Query 3 — Method-Signature:** `cross-system agent skill interfaces adapters hidden coupling factorial`

## Live search accounting

- Raw connector records: 60 (`arxiv=30`, `crossref=30`; all other connectors returned 0).
- Title-normalized unique records: 49 (`arxiv=22`, `crossref=27`; there was no cross-source title collision).
- Semantically retained from the three-query live search: 11.
- Filtered as irrelevant to the user's novelty claim: 38. Typical noise included unrelated materials science “coupling agents,” domain-specific multi-agent applications, safety-only attacks, and generic agent benchmarks without a skill/component boundary.
- Unfiltered structured output used for audit: `/tmp/skillstack_paper_search.json` (ephemeral local file).

## Connector errors (verbatim)

- Semantic Scholar: `403 Client Error: Forbidden` for all three queries.
- OpenAlex: `401 Client Error: Unauthorized` for all three queries.
- OpenReview: `openreview not installed. pip install openreview-py` for all three queries.
- DBLP: `Expecting value: line 1 column 1 (char 0)` for all three queries.

## Deduplicated retained set

### A. Live-search papers

1. SkCC: Portable and Secure Skill Compilation for Cross-Framework LLM Agents (arXiv:2605.03353).
2. Evaluating Skills, Not Just Agents: Agentic Continuous Evaluation of Skills (arXiv:2608.20614).
3. Understanding Multi-Agent LLM Frameworks: A Unified Benchmark and Experimental Analysis (arXiv:2602.03128).
4. Evidence-Calibrated Runtime Reconstruction for Agent Skills Across Heterogeneous Coding Agents (arXiv:2608.08793).
5. Harnessing Agent Skills: Architectural Patterns and a Reference Architecture for Skill-Mediated LLM Agents (SSRN 6871959).
6. Does Memory Credit Travel? Paired Factorial Audits of LLM-Agent Memory (SSRN 7160321).
7. Toward User Comprehension Supports for LLM Agent Skill Specifications (arXiv:2605.19362).
8. Contractual Skills: A GovernSpec Design Framework for Enterprise AI Agents (arXiv:2605.22634).
9. Agentic Skill Discovery (arXiv:2405.15019).
10. Skill-SD: Skill-Conditioned Self-Distillation for Multi-turn LLM Agents (arXiv:2604.10674).
11. Progressive Agent Skill Generation via Reinforcement Learning (arXiv:2608.01678).

### B. User-provided framework/report literature

12. SkillReranker (arXiv:2607.06283).
13. GraSP (arXiv:2604.17870).
14. SkillCAT (arXiv:2606.13317).
15. SkillRL (arXiv:2602.08234).
16. GRASP (arXiv:2605.29668).
17. SkillOps (arXiv:2605.13716).
18. MUSE-Autoskill (arXiv:2605.27366).
19. Dynamic Agent Skills (arXiv:2607.10113; TMLR 07/2026).
20. SkillDAG (arXiv:2606.03056).
21. Graph of Skills (arXiv:2604.05333).

### C. Papers added from candidate full-text related work

22. SkillsBench (arXiv:2602.12670).
23. SWE-Skills-Bench (arXiv:2603.15401).
24. SkillTester (arXiv:2603.28815).
25. AEVAL (arXiv:2607.16345).
26. SkillAudit (arXiv:2606.22613).
27. A Framework for Evaluating Agentic Skills at Scale (arXiv:2606.17819).
28. How Well Do Agentic Skills Work in the Wild (arXiv:2604.04323).

### D. Model-recall augmentation, subsequently verified

29. AgentSquare: Automatic LLM Agent Search in Modular Design Space (arXiv:2410.06153). This was not in the live results. The recalled title and identifier were verified by downloading and reading the paper; provenance remains `model-recall + verified-arXiv`.

No other model-recalled paper was added because the 29-paper pool already covers the closest reference-architecture, modular-search, portability, evaluation, lifecycle, and skill-method neighborhoods.
