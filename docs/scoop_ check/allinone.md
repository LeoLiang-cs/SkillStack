# Paper Search — SkillStack Prior-Art Search

## Display ALL results that survived semantic filtering

**Queries:**

1. `LLM agent skill component interchangeability composability evaluation`
2. `modular LLM agent architecture benchmark component evaluation`
3. `cross-system agent skill interfaces adapters hidden coupling factorial`

**Window:** 2024–2026
**Accounting:** semantic_scholar=0, open_alex=0, arxiv=30 raw, openreview=0, crossref=30 raw, dblp=0 · **49 unique** after title deduplication · **38 filtered as irrelevant** · **11 retained**.
**Unfiltered structured recovery file:** `/tmp/skillstack_paper_search.json` (ephemeral).

**Connector errors:** Semantic Scholar returned `403 Client Error: Forbidden`; OpenAlex returned `401 Client Error: Unauthorized`; OpenReview reported `openreview not installed. pip install openreview-py`; DBLP returned `Expecting value: line 1 column 1 (char 0)`.

| # | Title | Date | Venue | Citations | Score | Sources |
|---:|---|---|---|---:|---:|---|
| 1 | [SkCC: Portable and Secure Skill Compilation for Cross-Framework LLM Agents](https://arxiv.org/abs/2605.03353) | 2026-05 | arXiv preprint | n/a | 3/4 | arXiv |
| 2 | [Evaluating Skills, Not Just Agents: Agentic Continuous Evaluation of Skills](https://arxiv.org/abs/2608.20614) | 2026-08 | arXiv preprint | n/a | 2/4 | arXiv |
| 3 | [Understanding Multi-Agent LLM Frameworks: A Unified Benchmark and Experimental Analysis](https://arxiv.org/abs/2602.03128) | 2026-02 | arXiv preprint | n/a | 3/4 | arXiv |
| 4 | [Evidence-Calibrated Runtime Reconstruction for Agent Skills Across Heterogeneous Coding Agents](https://arxiv.org/abs/2608.08793) | 2026-08 | arXiv preprint | n/a | 3/4 | arXiv |
| 5 | [Harnessing Agent Skills: Architectural Patterns and a Reference Architecture for Skill-Mediated LLM Agents](https://doi.org/10.2139/ssrn.6871959) | 2026-06 | SSRN posted content | n/a | 3/4 | Crossref/SSRN |
| 6 | [Does Memory Credit Travel? Paired Factorial Audits of LLM-Agent Memory](https://doi.org/10.2139/ssrn.7160321) | 2026-07 | SSRN posted content | n/a | 3/4 | Crossref/SSRN |
| 7 | [Toward User Comprehension Supports for LLM Agent Skill Specifications](https://arxiv.org/abs/2605.19362) | 2026-05 | arXiv preprint | n/a | 2/4 | arXiv |
| 8 | [Contractual Skills: A GovernSpec Design Framework for Enterprise AI Agents](https://arxiv.org/abs/2605.22634) | 2026-05 | arXiv preprint | n/a | 2/4 | arXiv |
| 9 | [Agentic Skill Discovery](https://arxiv.org/abs/2405.15019) | 2024-05 | arXiv preprint | n/a | 1/4 | arXiv |
| 10 | [Skill-SD: Skill-Conditioned Self-Distillation for Multi-turn LLM Agents](https://arxiv.org/abs/2604.10674) | 2026-04 | arXiv preprint | n/a | 1/4 | arXiv |
| 11 | [Progressive Agent Skill Generation via Reinforcement Learning](https://arxiv.org/abs/2608.01678) | 2026-08 | arXiv preprint | n/a | 1/4 | arXiv |

### User-provided framework/report corpus (10 papers)

| # | Title | Date | Role in search |
|---:|---|---|---|
| 12 | [SkillReranker](https://arxiv.org/abs/2607.06283) | 2026-07 | retrieval implementation |
| 13 | [GraSP](https://arxiv.org/abs/2604.17870) | 2026-04 | typed graph composition/execution |
| 14 | [SkillCAT](https://arxiv.org/abs/2606.13317) | 2026-06 | multi-stage skill evolution |
| 15 | [SkillRL](https://arxiv.org/abs/2602.08234) | 2026-02 | recursive skill/policy co-evolution |
| 16 | [GRASP](https://arxiv.org/abs/2605.29668) | 2026-05 | proposer plus regression gate |
| 17 | [SkillOps](https://arxiv.org/abs/2605.13716) | 2026-05 | drop-in maintenance/lifecycle component |
| 18 | [MUSE-Autoskill](https://arxiv.org/abs/2605.27366) | 2026-05 | integrated lifecycle system |
| 19 | [Dynamic Agent Skills](https://arxiv.org/abs/2607.10113) | 2026-07 | lifecycle survey/taxonomy (TMLR) |
| 20 | [SkillDAG](https://arxiv.org/abs/2606.03056) | 2026-06 | typed retrieval graph |
| 21 | [Graph of Skills](https://arxiv.org/abs/2604.05333) | 2026-04 | dependency-aware structural retrieval |

### Full-text related-work augmentation (7 papers)

| # | Title | Date | Role in search |
|---:|---|---|---|
| 22 | [SkillsBench](https://arxiv.org/abs/2602.12670) | 2026-02 | paired no-skill/with-skill evaluation |
| 23 | [SWE-Skills-Bench](https://arxiv.org/abs/2603.15401) | 2026-03 | deterministic marginal utility in repositories |
| 24 | [SkillTester](https://arxiv.org/abs/2603.28815) | 2026-03 | paired utility plus security probes |
| 25 | [AEVAL](https://arxiv.org/abs/2607.16345) | 2026-07 | deterministic CI evaluation contracts |
| 26 | [SkillAudit](https://arxiv.org/abs/2606.22613) | 2026-06 | arbitrary-skill, skill-centered assessment |
| 27 | [A Framework for Evaluating Agentic Skills at Scale](https://arxiv.org/abs/2606.17819) | 2026-06 | generated tasks/rubrics, 500 skills |
| 28 | [How Well Do Agentic Skills Work in the Wild](https://arxiv.org/abs/2604.04323) | 2026-04 | realistic 34k-skill retrieval/refinement |

### Model Knowledge (1 paper, verified against arXiv)

| # | Title | Year | Venue | Notes |
|---:|---|---:|---|---|
| 29 | [AgentSquare: Automatic LLM Agent Search in Modular Design Space](https://arxiv.org/abs/2410.06153) | 2024 | arXiv preprint | Found by model recall, then PDF-verified; closest modular recombination predecessor. |

## Summary of all searched results

### 1. Overview

The search covers 29 relevant papers after combining 11 retained live-search results, the 10-paper framework/report corpus, seven papers discovered through candidate full-text references, and one verified model-recall paper. The closest neighborhood divides into modular architecture/search, skill portability/reference architecture, skill evaluation, lifecycle maintenance, and individual slot algorithms.

### 2. Trends

- The field expanded sharply in 2026: most direct skill evaluation, portability, lifecycle, and governance papers are from 2026.
- Evaluation shifted from whole-agent scores toward paired marginal-effect designs, deterministic verifiers, CI gates, and per-skill assessment.
- Portability work increasingly uses explicit intermediate contracts/IRs or adapter qualification across frameworks.
- Modular agent work exists before SkillStack (notably AgentSquare), but usually optimizes combinations after standardizing interfaces rather than studying native cross-paper semantic compatibility.
- The most dangerous novelty collision is not one identical paper; it is the union of AgentSquare + MAFBench + SkCC + Harnessing Agent Skills + SkillOps + paired skill-evaluation work.

### 3. Key themes

1. **Modular architecture and controlled architecture effects:** AgentSquare, MAFBench.
2. **Cross-framework skill portability and interfaces:** SkCC, Skill Runtime Intelligence, Contractual Skills, Harnessing Agent Skills.
3. **Paired/marginal skill evaluation:** SkillsBench, SWE-Skills-Bench, SkillTester, ACES, SkillAudit, AEVAL, Tessl framework.
4. **Dynamic skill lifecycle and maintenance:** SkillOps, Dynamic Agent Skills, MUSE-Autoskill, GRASP.
5. **Slot-specific mechanisms:** SkillReranker, GraSP, SkillCAT, SkillRL, SkillDAG, Graph of Skills.
6. **Interaction and attribution:** Does Memory Credit Travel; SkillOps's method-conditional plug-in results; ACES's workspace-conditional Skill Lift.

### 4. Keywords frequency

Approximate title-level concept counts over the 29-paper retained corpus:

| Keyword | Count |
|---|---:|
| Skill / Skills | 25 |
| Agent / Agentic | 24 |
| Evaluation / Benchmark | 10 |
| Framework / Architecture | 7 |
| Retrieval / Graph / Composition | 6 |

### 5. Most cited by accepted paper

Citation counts were unavailable because the Semantic Scholar and OpenAlex connectors failed; no accepted-paper citation ranking is reported rather than inventing values.

### 6. Most cited by first author

Author-level citation totals were unavailable for the same reason; no ranking is reported.

### 7. Recommendations for reading

1. **AgentSquare** — establishes the prior modular recombination/search baseline.
2. **SkillOps** — shows a real drop-in skill-library component with downstream-method interactions.
3. **MAFBench** — strongest neighboring controlled architecture-evaluation methodology.
4. **SkCC** — strongest cross-framework skill-portability/IR collision.
5. **Harnessing Agent Skills** — strongest direct reference-architecture collision; full text should be obtained manually if a submission decision depends on it.
