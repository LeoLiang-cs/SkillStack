# Algorithm Card — SkillCAT

## A. Identity and evidence

- **Paper:** *SkillCAT: Contrastive, Assessment-Augmented and Topology-Aware
  Skill Self-Evolution for LLM Agents*
- **arXiv:** 2606.13317; v1 submitted 2026-06-11; latest verified v2 updated
  2026-07-29. This card uses v2.
- **Authors/year:** Kunfeng Chen, Qihuang Zhong, Juhua Liu, Bo Du (2026)
- **Paper:** <https://arxiv.org/abs/2606.13317>
- **Primary text read:** <https://huggingface.co/papers/2606.13317.md> and
  <https://arxiv.org/html/2606.13317v2>
- **Source snapshot date:** 2026-08-25
- **Evidence read:** complete Method, Algorithm 1, experimental setup, main
  results, ablations, additional analyses, and conclusion.
- **Official code status:** no repository/project link appears in the verified
  arXiv/Hugging Face metadata, and an exact-title/author search did not locate
  a verified official repository as of the snapshot date. This does not prove
  that code is unavailable elsewhere.
- **Reproduction assets verified:** paper/HTML and pseudocode. No official code,
  prompts, source-task clone implementation, evolved skill artifacts, routing
  topologies, or complete configs were verified.
- **Evidence gaps:** exact prompts and merge implementation; task sampling and
  retry details; WikiTQ evaluation population; model decoding parameters;
  topology compiler schema; routing dependencies; context-token accounting;
  and variance are not fully specified in the main text. The paper has no
  dedicated limitations section.

## B. Claimed contribution

- **Problem:** self-evolution from one trajectory creates biased evidence;
  unconditional merging admits harmful patches; loading the whole skill causes
  irrelevant/conflicting context.
- **Claimed unit:** a three-stage skill lifecycle: Contrastive Causal Extraction
  (CCE), Assessment-Augmented Evolution (AAE), and Topology-Aware Task
  Execution (TTE).
- **New mechanism:** same-task success/failure comparison around the divergence
  point; source-task replay scoring before merge; hierarchical score-guided
  merge; online routing over capability topology rather than whole-skill load.
- **Not claimed:** a single independently replaceable module, weight training,
  or a general skill-utility result. The object being evolved is external skill
  content, not the backbone model.

## C. Native pipeline context

- **Upstream:** base skill `S_0`, evolution tasks, official evaluator, tools,
  multiple stochastic agent trajectories, and test tasks.
- **Native host:** ReAct-style agents with filesystem and spreadsheet tools.
- **Skill author/user roles:** Qwen3.5-35B-A3B and Qwen3.5-122B-A10B serve as
  both authors and users; Gemma-4-31B-it and GPT-5.4-mini are unseen users in
  cross-model evaluation.
- **Persistent artifacts:** base skill, candidate experience records, patches,
  assessment scores, admitted patch set, evolved skill, core skill, capability
  node bodies, and compact topology summary.
- **Offline:** CCE and AAE, then compile evolved skill into topology.
- **Online:** route task-relevant nodes, assemble compact runtime skill, inject
  it, and execute the task.
- **Update clock:** batched over the evolution dataset; one routed assembly per
  test task.

## D. Algorithm anatomy

### Inputs

- Evolution tasks `X={x_1,...,x_N}` and test tasks `X*`.
- Base skill `S_0`.
- Agent/harness, tools, official evaluator, and multiple random seeds.
- LLM contrastive extractor `E`, skill editor, source-task replay evaluator,
  merge operator `mu`, topology compiler, router `R`, assembler `A`.
- Assessment threshold `theta=2.0`; route node budget `k=7` in experiments.

### State and intermediate artifacts

- Per task, successful trajectories `T_i+` and failed trajectories `T_i-`.
- Contrastive pair or a labelled non-contrastive fallback trace.
- Experience record `r_i`: local evidence, failure cause, skill-editable
  lesson.
- Candidate patch `p_i`, original outcome `y_i`, replay outcome `yhat_i`, and
  assessment score `a_i`.
- Retained patches partitioned into score tiers.
- Evolved skill `S*`.
- Topology `(S_c, V, G)`: core skill, capability nodes, node bodies `B_v`, and
  metadata/dependency summary.
- Per-test selected nodes `V_j` and assembled runtime skill `S_j`.

### Ordered mechanism

1. Run each evolution task multiple times with different random seeds; split
   traces into evaluator-labelled successes and failures.
2. If both outcome classes exist, sample one success and one failure for the
   same task. Otherwise enter the explicit single-trajectory/non-contrastive
   fallback path.
3. Ask the contrastive extractor to find where the two action sequences
   diverge and create a localized experience record with evidence, causal
   diagnosis, and editable lesson.
4. Combine the record with the unchanged base skill `S_0` to generate one
   isolated candidate patch `p_i`.
5. Build a temporary skill containing the patch and rerun its associated
   source-task clone.
6. Score the outcome transition: failure→success `3`, success→success `2`,
   failure→failure `1`, success→failure `0`.
7. Admit patches with `a_i >= 2`; retain both improvement and non-regression,
   reject unresolved failures and regressions.
8. Group admitted patches by score tier and merge from low to high, so stronger
   patches are applied later. The procedure reuses Trace2Skill's edit approach
   to abstract recurring principles rather than instance fixes.
9. Compile evolved skill `S*` into a core skill and capability nodes. Preserve
   each original node body separately; expose only title, keywords, summary,
   and dependencies in the compact routing graph.
10. For each test task, let an LLM router select at most `k` nodes from the
    topology summary; let an LLM assembler combine the core and selected node
    bodies into runtime skill `S_j`.
11. Inject `S_j` into the ReAct-style user and execute the task.

### Outputs and failure behavior

- **Offline output:** admitted/rejected patches with scores and the evolved
  skill `S*`.
- **Deployment artifact:** core skill, capability topology, node bodies, and
  routing metadata.
- **Online output:** selected node IDs and compact task-specific runtime skill
  `S_j`, followed by the host's task outcome.
- **Failure/fallback:** CCE uses a non-contrastive fallback when success/failure
  pairing is impossible. AAE rejects low-score patches. The paper does not
  define typed failures for extractor, replay, merge, compile, route, or
  assembly failures.
- **Evidence:** trajectory labels/pairs and local record support a patch;
  source-task transition score supports admission; routing selection supports
  online context. These three evidence types must remain distinct.

### Invariants

- Contrastive pairs must share the same task, tools, and evaluator.
- Original and replay outcome labels must remain attached to patch/source-task
  identity; a score without its transition loses admission provenance.
- Candidate patches are evaluated in isolation before global merge.
- Rejected patches and regressions must not be silently merged or discarded
  from the audit log.
- Merge order is low-score tier to high-score tier.
- The topology summary and full node bodies are separate; routing reads the
  compact summary and assembly retrieves only selected bodies plus core.
- Evolution and held-out/test tasks remain separated.

## E. Candidate plug-in boundary

- **SkillStack responsibilities:** Acquisition/Evolution (`A`), Lifecycle
  admission (`L`), and online Discovery/Composition (`D/C`). Representation
  (`R`) must carry versioned patches, evidence, hierarchy, and topology.
- **Method type:** **composite evolution/deployment system**. The three stages
  are observable and separately ablated, but their independent portability is
  not established by the paper.
- **Smallest paper-faithful swap:** the whole `CCE→AAE→TTE` pipeline with its
  native base skill, task partitions, authors/users, tools, and evaluator.
- **Candidate internal ports to test later:**
  1. `CCE`: labelled same-task trajectories + base skill → evidence record +
     candidate patch;
  2. `AAE`: isolated patch + source-task clone/evaluator → score, admission
     decision, merged evolved skill;
  3. `TTE`: evolved hierarchical skill + test task → selected node set and
     assembled runtime skill.
- These ports are cross-paper abstractions proposed by SkillStack; they are not
  automatically paper-validated plug-ins.
- **Required adapter input:** exact trajectory/action/outcome records; cloning
  and replay authority; official evaluator; patch/base-skill format;
  hierarchical node bodies and dependencies; task context.
- **Required adapter output:** raw candidate record/patch; replay outcomes and
  score; admitted/rejected decision; evolved version; topology; routed node
  provenance; assembled skill text.
- **Neighbors fixed:** evolution/test split, source-task clone semantics,
  evaluator, author/user model, base skill, tools, seed count, threshold,
  route budget, and host injection path.
- **`paper_inspired` conditions:** single-trace summarization presented as CCE;
  validation by LLM opinion instead of replay; merging all patches; testing a
  patch only after global merge; flat text chunk retrieval instead of compiled
  capability topology; or loading selected summaries without original bodies.

## F. Native experimental design

**Paper provenance:** populations, roles, controls, and implementation settings
come from Experimental Setup; main transfer results from Table 1/Figure 3;
module controls from Table 2; trajectory, admission, and routing axes from
Figure 4 and More Analyses.

### Evaluation grid

- **SpreadsheetBench-Verified:** 400 samples, split 200 evolution / 200 held-out
  test. Correct only when all output cells match the gold workbook.
- **WikiTableQuestions:** OOD table QA using official denotation accuracy;
  exact population is not specified in the main text.
- **DocVQA validation:** 5,349 pairs; first 2,700 evolution, remaining 2,649
  evaluation; ANLS and accuracy at `ANLS >= 0.5`.
- Results averaged over three random seeds.
- Initial-skill settings: No-Skill; Human-Written (Anthropic official xlsx
  skill); LLM-Gen by the corresponding author model.
- Authors/users: two Qwen3.5 variants; unseen users Gemma-4-31B-it and
  GPT-5.4-mini. DocVQA uses Qwen-authored skills with two Qwen users.
- ReAct-style harness with filesystem/spreadsheet tools.
- CCE uses five trajectory seeds per evolution task; AAE threshold 2.0; TTE
  graph router Top-7.

### Baselines and controls

- Trace2Skill, EvoSkill, SkillOpt, plus No-Skill and unevolved initial skills.
- Full three-module system; leave-one-out for each module; each module alone.
- CCE trajectory-count sweep: 1, 5, 7, 9.
- AAE equal-size score buckets for F→S, S→S, F→F, S→F.
- TTE LLM graph router and Qwen3-Embedding-0.6B router over Top-k/context
  budgets; full-skill reference.

### Metrics and transfer axes

- Spreadsheet held-out exact accuracy; WikiTQ accuracy; DocVQA ANLS and
  thresholded accuracy.
- CCE inference time; routing context/token reduction; task accuracy across
  route budgets.
- Admission transition buckets provide a regression signal, but patch-level
  confidence intervals, false-admission rate, merge conflicts, and rollback
  behavior are not reported.
- Cross-domain/OOD, multimodal, writer-by-user/cross-family transfer, base-skill
  initialization, trajectory count, patch quality, and routing budget are
  all useful axes for the SkillStack matrix.

## G. Paper-reported findings

- **Table 1:** full SkillCAT has the highest aggregate result across all four
  Qwen user/initialization combinations. Under 35B user + Human-Written, its
  reported aggregate is 59.04 versus EvoSkill 42.21; individual tasks do not
  uniformly win in every setting.
- **Cross-model:** evolved skills improve the average of both unseen users, but
  one Gemma/WikiTQ condition is 1.62 points below the Human-Written baseline.
  This negative cell must be retained in any portability report.
- **Table 2:** full pipeline 55.00; without CCE 32.50; without AAE 26.00;
  without TTE 46.50. Only TTE scores 27.50, below Trace2Skill 29.67, showing
  routing cannot repair poor content.
- **Figure 4:** five trajectories outperform one, seven, and nine while cost
  rises sharply; F→S/S→S patches perform better than lower-score buckets;
  topology routing usually reduces context while remaining above the
  full-skill reference.
- **Limitations inferred from evidence, not a paper limitation section:** high
  offline sampling/replay cost; sensitivity to trajectory composition and
  evaluator correctness; one-source-task non-regression does not establish
  global non-regression; routing/merge details are not reproducible from code.

All numerical findings above are paper-reported and unverified by SkillStack.

## H. SkillStack architecture test

- `A` currently needs distinguishable **Evidence → Proposal/Transform** ports;
  otherwise CCE extraction and patch generation are conflated.
- `L` needs **Assess → Admit/Reject → Merge/Version** rather than one generic
  governance call. Source-task replay evidence is part of the admission
  contract, not optional logging.
- TTE is partly `D` (node routing) and partly `C` (runtime skill assembly), but
  does not execute a GraSP-like action graph.
- `R` must represent base/evolved versions, patches, evidence provenance,
  hierarchical node bodies, topology metadata, and dependencies.
- Current static-library `A/L` placeholders cannot host CCE/AAE faithfully;
  current flat/structured ReAct injection cannot be labelled TTE without the
  topology compiler and router/assembler.
- **Provisional verdict:** keep the five top-level responsibilities; refine
  internal primitives and add multi-port composite declarations. Decide on
  top-level boundary changes only after Day 3 cross-paper comparison.

## I. Reproduction and integration verdict

- **Fidelity status:** `blocked` for exact native reproduction due to absent
  verified code/prompts/artifacts/configs.
- **Native reproduction requirement:** recreate native task splits, base-skill
  settings, five-seed trajectories, official evaluation, isolated replay,
  score-tier merge, topology compiler, Top-7 router/assembler, and Qwen
  author/user matrix before cross-host swapping.
- **First safe smoke test:** two source tasks—one containing both success and
  failure traces, one single-class fallback—then verify isolated scores for all
  four outcome transitions and preservation of rejected patches.
- **First controlled portability test:** hold CCE and base skill fixed, swap AAE
  admission implementations with identical replay inputs; separately hold the
  evolved skill fixed and swap TTE into another ReAct host.
- **Expected friction:** trajectory schema, task cloning, evaluator access,
  model-specific skill editing, mutable skill versions, merge conflicts,
  topology schema, and host-specific context injection.
- **Open question:** whether CCE, AAE, and TTE remain useful and semantically
  valid when independently swapped is precisely a compatibility question; the
  paper's ablations alone do not answer it.
