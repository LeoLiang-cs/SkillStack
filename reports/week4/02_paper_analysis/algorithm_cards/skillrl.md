# Algorithm Card — SkillRL

## A. Identity and evidence

- **Paper:** *SkillRL: Evolving Agents via Recursive Skill-Augmented
  Reinforcement Learning*
- **arXiv:** 2602.08234, v1, submitted 2026-02-09
- **Authors/year:** Peng Xia, Jianwen Chen, Hanyang Wang, Jiaqi Liu, Kaide Zeng,
  Yu Wang, Siwei Han, Yiyang Zhou, Xujiang Zhao, Haifeng Chen, Zeyu Zheng,
  Cihang Xie, Huaxiu Yao (2026)
- **Paper:** <https://arxiv.org/abs/2602.08234>
- **Official repository:** <https://github.com/aiming-lab/SkillRL>
- **Source snapshot:** commit `8e66726ed866a4e0a7f053586a41022798192e6c`,
  inspected 2026-08-25
- **Evidence read:** Method §3, Algorithm 1, Experiments §4, appendices;
  repository README, skill generation, skill-only retrieval, dynamic updater,
  environment manager, and RL trainer update hooks.
- **Released assets verified:** training/environment code, SFT dataset and model
  links, skill JSON format, template/embedding retrieval, dynamic-update code.
- **Evidence gaps:** exact initial rollout set and reported run artifacts were
  not independently reconstructed; the paper has no dedicated limitations
  section; some current-repository behavior is newer or narrower than the
  paper description.

## B. Claimed contribution

- **Problem:** raw trajectory memory is verbose/noisy and a static memory or
  skill bank cannot adapt as the policy visits new states.
- **Claimed unit:** a composite training pipeline that co-evolves a hierarchical
  SkillBank and the agent policy.
- **New mechanism:** differential success/failure distillation; general versus
  task-specific skill hierarchy; cold-start SFT for skill use; GRPO conditioned
  on retrieved skills; validation-failure-triggered library evolution.
- **Not claimed:** a training-free component, a frozen-host plug-in, or a
  standalone skill updater whose effect is independent of SFT/RL.

## C. Native pipeline context

- **Upstream:** base Qwen2.5-7B-Instruct policy, target environment/tasks,
  binary outcome evaluator, rollout trajectories, OpenAI o3 teacher.
- **Downstream:** the output policy is trained to consume the SkillBank inside
  its prompt during every rollout.
- **Persistent state:** initial/evolved SkillBank, SFT dataset/model, current RL
  policy, reference policy, failed trajectory pool, saved evolved snapshots.
- **Offline phases:** initial experience collection/distillation, hierarchical
  library construction, synthetic SFT-data generation, cold-start SFT.
- **Online training:** task-conditioned retrieval, grouped rollouts, GRPO
  updates, periodic validation/failure analysis, additive skill updates.
- **Update clock:** initial batch construction, every policy-training step, and
  periodically at validation or training checkpoints depending on source
  configuration.

## D. Algorithm anatomy

### Inputs

- Base policy `pi_base`, teacher `M_T`, environment `E` and task descriptions.
- Outcome-labelled trajectories `T+` and `T-`.
- Task-category mapping and hierarchical skill schema.
- Retrieval threshold/budget; paper reports task-specific Top-6.
- Skill-augmented SFT examples.
- GRPO learning rate, batch/group settings, reward function and KL reference.
- Validation category threshold `delta` and failure sampling policy.

### State and intermediate artifacts

- Success strategic patterns `s+` and counterfactual failure lessons `s-`.
- General skills `S_g`; task-specific sets `S_k`; complete SkillBank.
- Each skill: ID, concise name/title, principle, and `when_to_apply`; released
  JSON also stores common mistakes.
- Synthetic SFT triples `(task, retrieved skills, target trajectory)`.
- SFT policy/reference policy; current GRPO policy and rollout groups.
- Per-category success rates, selected failed trajectories, proposed additions,
  and versioned saved skill-bank files.

### Ordered mechanism / paper pseudocode

1. Roll out `pi_base` in the target environment and retain both successful and
   failed episodes.
2. Let the teacher extract critical decisions/generalizable patterns from each
   success.
3. Let the teacher turn each failure into a concise lesson containing failure
   point, flawed action/reasoning, counterfactual action, and prevention rule.
4. Consolidate distilled records into always-injected general skills and
   category-specific skills.
5. Ask the teacher to generate demonstrations showing how to retrieve,
   interpret, and apply SkillBank content; SFT the base model on them.
6. Use the SFT policy as the initial RL policy and fixed KL reference.
7. For each task during RL, retrieve general plus semantically relevant
   task-specific skills and condition the policy on them.
8. Sample a group of complete trajectories, score them with binary task
   success, normalize group advantages, and update the policy with GRPO.
9. At an evolution checkpoint, identify categories below the success threshold.
10. Stratify failed trajectories by category and failure severity, maintaining
    category diversity; ask the teacher to identify uncovered gaps and propose
    new/refined skills.
11. Update the SkillBank and continue policy training; return the trained policy
    and evolved SkillBank.

### Outputs and failure behavior

- **Primary:** trained policy `pi_theta*` and evolved `SkillBank*`.
- **Auxiliary:** distilled records, SFT data/checkpoint, retrieved skill sets,
  validation metrics, skill-update history and saved bank snapshots.
- **Failure behavior:** empty/no failed trajectories skip an update; teacher/API
  or JSON-parse errors return no new skills in released source; duplicate IDs
  are skipped; no explicit rollback or regression gate exists.
- **Score/evidence:** outcome label supports initial distillation; category
  success threshold triggers evolution; GRPO reward trains the policy. The
  source updater does not attach per-skill validation evidence.

### Invariants

- Successful and failed trajectories must remain distinguishable and retained.
- Evolution/test/validation provenance must be explicit; a generated skill must
  record which failure checkpoint caused it.
- General and task-specific hierarchy must not collapse into one flat bank in a
  paper-faithful condition.
- Policy and library checkpoints are coupled; evaluating one with an unrelated
  policy is a transfer experiment, not the native condition.
- Skill-injection format and retrieval budget must remain fixed when comparing
  policy or updater variants.
- No proposed skill should be silently lost on API/parse/duplicate failure.

## E. Released-source audit

- `SkillsOnlyMemory.retrieve()` exposes template and embedding modes. Template
  mode detects task type by keyword and returns dynamic general skills plus
  category skills; embedding mode uses Qwen3-Embedding-0.6B across categories.
- `SkillUpdater.analyze_failures()` consumes at most five displayed failures,
  returns at most three new JSON skills, forces unique `dyn_NNN` IDs, and
  catches API/parse errors by returning an empty list.
- Trainer hooks can update from validation or training batches; new skills are
  written only into training environments and saved as JSON snapshots.
- **Paper/source mismatch:** the paper says the teacher may add new skills or
  refine ineffective ones. The inspected updater only generates and appends new
  general skills; no modify/admission/rollback path is implemented there.
- **Paper/source mismatch:** paper Algorithm 1 says evolution after validation
  epochs. The repository also offers training-batch updates; this must be a
  separately labelled source variant.
- Dynamic updates default to disabled in the generic configuration but are
  enabled in released task training scripts.

## F. Candidate plug-in boundary

- **Responsibilities:** Acquisition/Evolution (`A`), Representation (`R`),
  Discovery (`D`), and policy/lifecycle training (`L`); task execution remains
  inside the learned policy.
- **Method type:** **composite learning system**.
- **Smallest faithful initial swap:** full initial distillation → SkillBank →
  cold-start SFT → skill-conditioned GRPO → recursive evolution pipeline.
- **Candidate internal ports:**
  1. trajectory distiller: labelled trajectories → structured skill records;
  2. hierarchical retriever: task + SkillBank → general/task-specific context;
  3. recursive updater: failure pool + current bank → proposed bank delta.
- These internal ports are technically visible in source, but their independent
  behavioral portability is not established by the paper.
- **Required adapter inputs:** typed outcome-labelled traces, task category,
  current bank/version, teacher endpoint, task success metrics, training policy
  and environment.
- **Required outputs:** selected skills with provenance; raw update candidates;
  updated bank/version; policy checkpoint association.
- **`paper_inspired` conditions:** using a frozen current SkillStack host;
  omitting cold-start SFT or GRPO; using only the released additive updater while
  claiming paper-level refine behavior; or flattening the hierarchy.

## G. Native experimental design

**Paper provenance:** setup from §4.1; main results Tables 1–2; component
ablations Table 3; library/convergence/context analyses Figures 3–6; training
hyperparameters and compute from Appendix B.

- **Benchmarks:** ALFWorld, WebShop, and seven search-augmented QA datasets:
  NQ, TriviaQA, PopQA, HotpotQA, 2Wiki, MuSiQue, Bamboogle.
- **Search transfer:** trained on NQ and HotpotQA; remaining datasets provide
  in/out-of-domain axes as marked in Table 2.
- **Base/teacher:** Qwen2.5-7B-Instruct and OpenAI o3.
- **RL:** GRPO, learning rate `1e-6`, batch 16, group 8, four gradient
  accumulation steps; task-specific retrieval `K=6`; update threshold `0.4`.
- **Baselines:** GPT-4o, Gemini-2.5-Pro; ReAct/Reflexion; Mem0, ExpeL, MemP;
  PPO/RLOO/GRPO; EvolveR, MemRL, Mem0+GRPO, SimpleMem+GRPO; search-RL methods.
- **Metrics:** ALFWorld success overall/per task type; WebShop average score and
  success; QA accuracy/score; prompt length; library size; validation
  convergence/training step.
- **Key ablations:** no hierarchy/task-specific-only; raw trajectories instead
  of SkillBank; no cold-start SFT; no dynamic evolution.
- **Transfer/stress:** task type, environment, search OOD, library growth,
  context efficiency and convergence. Cross-user frozen-library transfer is
  not the main paper design.
- **Uncertainty gap:** main text does not consistently state seeds/variance for
  every table; preserve raw run counts when reproducing.

## H. Paper-reported findings

- Table 1 reports 89.9% ALFWorld success and 72.7% WebShop success for SkillRL.
- Table 2 reports 47.1 average across search QA versus 43.1 for EvolveR and 38.5
  for Search-R1.
- Table 3 reports drops of 13.1/11.3 points without hierarchy, up to 25 points
  when replacing skills with raw trajectories, about 20 points without SFT,
  and a 5.5-point contribution from dynamic evolution.
- The library reportedly grows from 55 to 100 skills by training step 150;
  context length is about 10.3% below the raw-memory comparison; recursive
  evolution reaches 80% validation success earlier.
- **Limits:** the result entangles better external artifacts with policy
  training; the updater has no regression gate; teacher/model/training cost is
  substantial; paper/source refinement semantics differ; no dedicated paper
  limitations section addresses these issues.

These findings are paper-reported and not reproduced in SkillStack.

## I. SkillStack architecture and integration verdict

- `A` must separate evidence collection, outcome-conditioned distillation, and
  proposal/update.
- `D` must expose hierarchy-aware retrieval and preserve general versus
  task-specific provenance.
- `L` must associate bank versions with policy checkpoints and training stage;
  it currently lacks admission/rollback protection for generated skills.
- `R` must carry skill type, category, trigger, origin trajectory, writer,
  bank version and policy-checkpoint compatibility.
- **Architecture verdict:** keep the five responsibilities, refine `A/D/L`, and
  model policy-training coupling explicitly in configuration/provenance rather
  than create a new top-level responsibility yet.
- **Fidelity status:** `paper_faithful_possible` for the released composite with
  substantial compute and declared paper/source variants; a small frozen-host
  port is `paper_inspired_only`.
- **First smoke test:** run the released skill-only memory and additive updater
  on retained ALFWorld trajectories without RL; validate schemas/failure logs
  and label it source-component smoke, not SkillRL reproduction.
- **First faithful baseline:** released SFT checkpoint + template SkillBank +
  GRPO configuration with dynamic update and frozen task splits.
- **Open blocker:** decide whether the matrix tests the paper algorithm or the
  narrower released additive updater; they cannot share one fidelity label.
