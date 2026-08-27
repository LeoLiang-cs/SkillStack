# Algorithm Card — SkillReranker

## A. Identity and evidence

- **Paper:** *Task Decomposition-Guided Reranking for Adaptive Agent Skill Retrieval*
- **Method name:** SkillReranker
- **arXiv:** 2607.06283, v1, submitted 2026-07-07
- **Authors/year:** Yanping Chen, Weijie Shi, Wen Yang, Jiajie Xu (2026)
- **Paper:** <https://arxiv.org/abs/2607.06283>
- **Primary text read:** <https://arxiv.org/html/2607.06283v1>
- **Source snapshot date:** 2026-08-25
- **Evidence read:** abstract, problem formulation, complete Method §4,
  Experiments §5, Limitations §7, prompt appendix headings.
- **Official code status:** no repository is linked from the arXiv record, and
  an exact-title/author search did not identify a verified official repository
  as of the snapshot date. This is a search result, not proof that code does
  not exist.
- **Reproduction assets verified:** paper and HTML; prompt templates are printed
  in Appendix B. No code, configs, exact agent prompt, or packaged 67,884-skill
  snapshot was verified.
- **Evidence gaps:** initial sentence-encoder model and some implementation
  details are not named in the main text; number of repeated runs/uncertainty
  reporting is not specified; the precise skill-pool snapshot and baseline
  implementations are unavailable.

## B. Claimed contribution

- **Problem:** fixed semantic Top-k retrieval cannot distinguish generic but
  semantically similar skills or adapt the number of skills to task structure.
- **Claimed algorithmic unit:** an inference-time, task-decomposition-guided
  reranking framework that returns an adaptively sized skill set.
- **New mechanism:** parse tasks and skills into state transitions; align
  candidate skills to a task-state execution graph; detect stage boundaries;
  select and deduplicate one best skill per stage.
- **Not claimed:** skill acquisition/evolution, skill execution, verification,
  repair, or a general proof that skills are useful. The paper evaluates a
  selector inside a frozen downstream agent.

## C. Native pipeline context

- **Upstream:** a natural-language task and a large skill library with name,
  short description, and full skill document.
- **Downstream:** a LangChain skill-using agent receives the selected skills.
- **Persistent library:** 67,884 skills collected from skillsmp.com.
- **External models:** a sentence encoder for coarse recall; DeepSeek-v4-Flash
  for semantic decomposition; Qwen3-Reranker-0.6B as cross-encoder.
- **Offline:** parse every skill into precondition and completion states and
  cache the results with its metadata.
- **Online:** recall candidates, parse the task, construct the execution graph,
  split it into stages, rerank, and return skills.
- **Update clock:** skill parsing changes when the library changes; task parsing
  and selection run once per task before downstream execution.

## D. Algorithm anatomy

### Inputs

- Task instruction `q`.
- Skill library `S={s_1,...,s_N}`; each skill has metadata `m_k`, full text
  `c_k`, and cached parsed precondition `p_k` and completion state `e_k`.
- Recall size `K=30` in the reported experiments.
- Expert task parser, sentence encoder, and cross-encoder relevance function
  `r(·,·)`.

### State and intermediate artifacts

- Ordered subtasks `T=(t_0,...,t_{m-1})`.
- Ordered task states `S_q=(s_0,...,s_m)`, where subtask `t_i` moves the task
  from `s_i` to `s_{i+1}`.
- Candidate set `C` from coarse recall.
- For candidate `k`, a source state `src_k`, later target state `tgt_k`, global
  task relevance `rho_k=r(q,c_k)`, and graph-edge weight.
- Stage boundaries and ordered stage intervals.
- No persistent mutation occurs online; the only persistent derived state is
  the offline skill parse/cache.

### Ordered mechanism

1. **Offline skill normalization.** Parse each skill document into `p_k` and
   `e_k`; use `None` when no precondition is required; cache the result.
2. **Online task normalization.** Decompose `q` into ordered subtasks and derive
   the corresponding initial/intermediate/goal states.
3. **Coarse recall.** Embed the task and skill metadata; keep the Top-30
   candidates by cosine similarity.
4. **Precondition alignment.** For every candidate, use the cross-encoder to
   map `p_k` to the best task-state source node; `None` maps to the initial
   state.
5. **Effect alignment.** Map `e_k` to the best later task state. Discard a
   candidate when no later landing point exists, because it cannot advance the
   parsed task sequence.
6. **Graph construction.** Treat task states as nodes and aligned candidate
   skills as directed edges. Retain global task–skill relevance `rho_k`.
7. **Stage splitting.** Compute weighted incoming, outgoing, and cross-boundary
   edge strengths. Mark a node as a boundary when strong skills end before it
   and begin after it while few strong skills cross it.
8. **Stage-wise reranking.** Concatenate the subtasks in each stage. Score
   candidate skills using both global task relevance and local stage
   relevance; select the best eligible skill for each stage.
9. **Output assembly.** Preserve stage order and deduplicate repeated skills.
   The final count is adaptive and cannot exceed the number of stages.

### Outputs and failure behavior

- **Primary output:** an ordered, deduplicated, variable-size selected skill
  set for the downstream agent.
- **Auxiliary output required for auditing:** task parse, cached skill parse,
  candidate recall scores, aligned graph edges, split points, per-stage scores,
  and discarded-candidate reasons.
- **Failure behavior in paper:** parsing/alignment can be wrong; a candidate
  without a valid later target is discarded. No explicit selector-level
  fallback or typed failure object is defined.
- **Confidence:** cross-encoder scores are used for alignment and selection,
  but the paper does not expose a calibrated final confidence contract.

### Invariants

- Task states and subtasks must preserve logical execution order.
- A retained edge must advance forward: `tgt_k > src_k`; the graph is a DAG.
- Skill precondition/effect parses must remain paired with their original skill
  document and library version.
- The stage order must be preserved after deduplication.
- Global relevance, local stage relevance, and graph alignment cannot be
  silently replaced by a single task–skill similarity score.
- Parse failures, discarded edges, and empty-stage selection must be retained
  in a SkillStack trace even though the paper does not define all of them.

## E. Candidate plug-in boundary

- **Primary SkillStack responsibility:** Discovery/Selection (`D`).
- **Internal primitives exposed by the paper:**
  `Recall → Parse/Normalize → Align/Graph → Split → Rerank/Route`.
- **Method type:** **composite selector**, not a single reranker call. Its
  reported result depends jointly on offline skill parsing, online task
  decomposition, graph alignment, and adaptive stage selection.
- **Smallest faithful swappable unit now:** the entire selector pipeline from
  task/library input to ordered selected-skill output, including its offline
  cache builder.
- **Possible later ports:** the initial recall stage and cross-encoder model can
  become configurable only if the graph, splitting, and scoring semantics stay
  unchanged and a native reference configuration is retained.
- **Required adapter input:** task instruction; versioned skill metadata/full
  text; parsed precondition/effect cache or authority to build it.
- **Required adapter output:** ordered skill IDs plus selection provenance;
  downstream host must accept a variable-size ordered set.
- **Neighbors fixed in a valid swap:** same task split, library, host executor,
  backbone, decoding, step budget, and skill injection semantics.
- **`paper_inspired` conditions:** using only SkillStack's current
  `task_semantic` retriever; replacing state parsing with current canonical
  fields; using a flat Top-k; omitting graph alignment/splitting; or returning
  an unordered set.

## F. Native experimental design

**Paper provenance:** benchmark/model/control/metric settings come from §5.1;
main performance and efficiency axes from §5.2 and Appendix A; component
ablations from §5.3.

### Evaluation grid

- **ALFWorld:** seen 140 tasks; unseen 134 tasks.
- **ScienceWorld:** validation renamed seen, 194 tasks; test renamed unseen,
  211 tasks; 30 task types.
- **Library:** 67,884 skills from skillsmp.com; snapshot/quality labels not
  released in the verified materials.
- **Host backbones:** DeepSeek-v4-Flash, GPT-5.4-Mini, Qwen3.6-27B.
- **Supporting models:** DeepSeek-v4-Flash parser;
  Qwen3-Reranker-0.6B cross-encoder; Mimo-v2.5-Pro only for the
  LLM-as-selector baseline.
- **Decoding:** temperature 0; Qwen3.6-27B served locally with vLLM.
- **Budget:** maximum 30 environment steps; candidate pool `K=30`.
- **Runs/seeds:** not stated in the verified paper text; no variance or
  confidence interval is reported in the main table.

### Baselines and controls

- LLM-as-selector, SkillRouter, and Graph of Skills.
- All methods use the same frozen agent and same skill pool.
- Because SkillReranker returns about 1–2 skills, baseline results average the
  Top-1 and Top-2 settings. This is paper-native but is not a direct fixed-k
  cell; a SkillStack matrix should retain separate Top-1 and Top-2 raw cells.
- Ablations on DeepSeek-v4-Flash and Qwen3.6-27B: `w/o Parsing`,
  `w/o Graph Edge`, `w/o Split`.
- No-skill is not a required control for our plug-and-play question; the native
  paper also centers matched selectors rather than skill utility.

### Metrics and transfer axes

- Average reward/success score, average environment steps, average execution
  tokens.
- The paper reports selected-skill count but no intrinsic retrieval labels,
  selection recall, calibration, or graph-validity rate.
- Cross-model: three downstream backbones.
- Cross-domain: ALFWorld versus ScienceWorld and seen/unseen splits.
- Scale stress, library-quality stress, and cross-host component swaps are not
  evaluated.

## G. Paper-reported findings

- **Main table (§5.2):** the paper reports the best reward in 11 of 12
  model/split settings and the fewest steps in 11 of 12 settings.
- **Efficiency (§5.2):** average selected count is roughly 1.28–1.30 across the
  four benchmark splits; the paper reports the lowest tokens in its displayed
  model settings.
- **Ablation (§5.3):** the full method wins most cells; removing parsing is
  generally most damaging; one exception is ScienceWorld-unseen under
  Qwen3.6-27B, where `w/o Split` has slightly higher reward.
- **Limitations (§7):** LLM parsing errors and incomplete skill descriptions
  can corrupt the graph; cross-encoder scoring adds inference overhead;
  evaluation is limited to text-based interactive environments.

These are paper-reported results and have not been reproduced in SkillStack.

## H. SkillStack architecture test

- The high-level `D` responsibility remains adequate, but one current selector
  slot hides at least five method-distinct primitives.
- The current `R` contract lacks paper-required precondition/effect fields and
  library-versioned parse provenance.
- The current `D` output should preserve order, variable cardinality, scores,
  split points, and discard reasons rather than only skill IDs.
- The graph is a **selection-time alignment artifact**, not a GraSP-style
  executable plan; it should not be assigned to `C` merely because it is a DAG.
- **Provisional verdict:** keep `R-A-D-C-L` at the responsibility level; refine
  `D` internally and enrich the `R→D` artifact contract. No architecture change
  is authorized until all six paper cards are compared.

## I. Reproduction and integration verdict

- **Fidelity status:** `blocked` for exact native reproduction because no
  official code/library snapshot was verified; `paper_faithful_possible` only
  after reconstructing prompts/algorithms and documenting the remaining gaps.
- **Native reproduction requirement:** rebuild the 67,884-skill snapshot or a
  declared subset, offline parses, Top-30 recall, cross-encoder graph, adaptive
  split/rerank, and frozen LangChain host before testing a host swap.
- **First safe smoke test:** one ALFWorld task with a small retained library;
  verify forward edges, stage boundaries, variable-cardinality ordered output,
  and complete trace artifacts without claiming benchmark reproduction.
- **Candidate host matrix:** native/frozen paper-like host first, then current
  SkillStack `react` host with only a declared output adapter.
- **Expected friction:** skill schema mismatch, missing parser cache, variable
  output cardinality/order, extra model calls, and unknown failure semantics.
- **Open question:** whether the downstream paper host consumes selected skills
  in exactly the returned order is not fully specified; preserve the order and
  test both ordered and order-insensitive injection only as separately labelled
  conditions.
