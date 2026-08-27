# Algorithm Card — GRASP (Gated Regression-Aware Skill Proposer)

## A. Identity and evidence

- **Paper:** *GRASP: Gated Regression-Aware Skill Proposer for Self-Improving
  LLM Agents*
- **arXiv:** 2605.29668, latest verified v3, updated 2026-08-21
- **Authors/year:** Johannes Moll, Jean-Philippe Corbeil, Jiazhen Pan, Martin
  Hadamitzky, Daniel Rueckert, Lisa Adams, Keno Bressem (2026)
- **Paper:** <https://arxiv.org/abs/2605.29668>
- **Project:** <https://jomoll.github.io/grasp/>
- **Official repository:** <https://github.com/jomoll/GRASP>
- **Source snapshot:** commit `9d7d125a3e9b46ed591692475eb07aff4ae67d34`,
  inspected 2026-08-25
- **Evidence read:** complete Method §2, Experimental Setup §3, Results §4,
  Limitations, Algorithm 1 and Appendices B–E; repository method/task
  interfaces, cycle, updater, repository, injection and extension docs.
- **Released assets verified:** unified framework, benchmark adapters, prompts,
  learned/frozen libraries, per-seed outputs and method extension interface.
- **Evidence gaps:** full experiments were not rerun; some proprietary model
  endpoints may drift; clinical benchmark infrastructure is nontrivial.

## B. Claimed contribution

- **Problem:** failure-driven skill writers generate plausible edits that can
  regress already-solved tasks; monotonic memory growth accumulates noise.
- **Claimed unit:** a bounded-library self-improvement method combining grouped
  failure-driven proposals with held-out regression-aware acceptance.
- **New mechanism:** open-vocabulary mechanism classification, best-of-K
  ADD/MODIFY/REMOVE proposals, fresh baseline/candidate replay on a balanced
  probe, hard regression budget, optional contrastive revision.
- **Not claimed:** zero-cost learning, universal cross-model compatibility,
  clinical expertise, or superiority on every benchmark/split.

## C. Native pipeline context

- **Upstream:** executing agent, dev/validation/test task splits, exact
  evaluator, current bounded skill library, prior dev histories.
- **Downstream:** `SkillAwareAgent` injects learned Markdown skills; no model
  parameters are updated.
- **Persistent state:** read-only base skills/template; learned library and
  version history; per-episode traces/outcomes; failure vocabulary;
  effectiveness/provenance; per-epoch checkpoints and validation curve.
- **Offline/training:** repeated dev batches, proposal/gating, validation
  checkpointing, final best-checkpoint restore.
- **Online/test:** frozen best library is injected; no further editing.
- **Update clock:** one possible library edit per dev batch; one validation
  checkpoint per epoch.

## D. Algorithm anatomy

### Inputs

- Current library `S`, current dev batch `B`, prior dev run history `H`.
- Executing agent/skill writer, exact task evaluator and task family guidance.
- Batch size `B=48`, candidate count `K=4`, probe size `N=36`, invalid-action
  penalty `lambda=2`, capacity and epoch/seed settings in the default study.
- Passing/failing samples available before the current batch, including their
  outcome under the library active when originally run.

### State and intermediate artifacts

- Skill file: YAML name/description/tags/version/provenance plus Markdown body
  with trigger, rule, optional verification and contrastive example.
- Failed trace groups and open-vocabulary mechanism labels.
- Candidate edit `c ∈ {ADD, MODIFY, REMOVE}` and a forked candidate library.
- Balanced probe: previously failing and passing subsets.
- Fresh current-library baseline counts `F0`, `R0` and baseline-error set `E0`.
- Candidate fixes `F(c)`, regressions `R(c)`, invalid-action regressions and
  adjusted score.
- Winning/revised edit, applied provenance, archived parent version, library
  snapshot and best-validation checkpoint.

### Ordered mechanism / paper pseudocode

1. Run the current skill-aware agent on a dev batch and persist full outcomes.
2. Extract failed traces. Classify each into a mechanism-specific label,
   preferring labels already discovered and minting one only when necessary.
3. Cycle from largest to smaller failure groups and sample K candidate edits.
   Each proposal sees homogeneous failures, passing examples, current library
   summaries/statistics and other active failure labels.
4. Validate proposal schema and capacity. ADD is blocked at capacity unless a
   paired REMOVE frees a slot.
5. Build an out-of-sample balanced probe from earlier dev runs/previous epoch;
   validation and test never enter proposal or gating.
6. Re-run the unchanged current library on the probe to establish fresh causal
   baseline counts and baseline execution errors.
7. For each unique candidate, fork the library, apply the edit, run the same
   probe and compute fixes, regressions and invalid-action penalty.
8. Admit only candidates with positive net improvement and no regression-count
   increase: `(F-F0)-(R-R0)>0` and `R<=R0`.
9. Select the highest-scoring eligible candidate; if none qualifies, leave the
   library unchanged.
10. If the winner causes any regression within the allowed baseline budget,
    ask the writer for a narrower contrastive revision; replace the winner only
    if the revision scores strictly higher and still respects the budget.
11. Apply at most the winning edit to the real repository with provenance and
    version history.
12. Evaluate silently on validation after every epoch, checkpoint improvements,
    and restore the best-validation library for one-time test/OOD evaluation.

### Outputs and failure behavior

- **Primary output:** frozen best-validation learned skill library.
- **Per-batch output:** applied edit or explicit no-op/rejection, candidate
  scores, probe transitions and raw proposals.
- **Auxiliary:** failure taxonomy, trace logs, skill histories, validation
  curve, frozen transfer libraries and test/OOD metrics.
- **Failure/no-op:** no failures, no valid proposal, missing probe, no candidate
  clears gate, revision rejected, or dev-collapse recovery removes a harmful
  recent skill.
- **Evidence:** every learned version carries epoch/update cycle, probe score,
  fixes and regressions; source archives modified parents.

### Invariants

- Probe samples must be out-of-sample relative to the proposal-generating batch.
- The current library and every candidate must be rerun on the identical probe.
- Baseline execution errors are excluded consistently; new candidate execution
  errors count as regressions.
- Validation/test are never used for proposals or per-batch admission.
- A committed candidate must have positive adjusted score and satisfy the hard
  unweighted regression budget.
- At most one candidate edit is committed per batch; rejection/no-op is a valid
  output and must be retained.
- Base/template skills are read-only; learned modifications retain version and
  parent provenance.

## E. Released-source audit

- `Method.run()` is an explicit self-improvement-method plug-in contract taking
  config, run directory and `Task`; GRASP itself is `SkillLearningMethod`.
- `Task` centralizes split access, rollout and evaluation, letting different
  methods share benchmark/agent controls.
- `SkillUpdater` exposes classify, diagnose, propose, validate, revise and apply;
  `SkillRepository` exposes fork, add/modify/delete, snapshot and history.
- The regression gate itself is orchestrated inside `SkillCycleRunner`, not a
  single standalone `Gate` interface. A narrower gate swap would need a new
  adapter/specification even though its data flow is visible.
- **Paper/source mismatch:** `_build_probe_set()` uses the current batch itself
  at epoch 0, batch 0 when no earlier entries exist, even though the surrounding
  source text and paper describe an out-of-sample probe. The released
  AgentBench ALFWorld config uses one full 26-record dev batch, so this fallback
  is reachable. A paper-faithful gate test must skip that update or pre-freeze a
  disjoint earlier probe; exact-source behavior receives a separate label.
- Source preserves raw proposals, update events, skill provenance, validation
  curves and final checkpoint—stronger evidence support than the other five
  Day 1–3 papers.

## F. Candidate plug-in boundary

- **Responsibilities:** Acquisition (`A`: failure diagnosis/proposal) and
  Lifecycle (`L`: assess/admit/version/rollback), with Representation (`R`)
  carrying structured skills/evidence.
- **Method type:** **proposer–gate composite**, but it is a real component at
  the released `Method` boundary.
- **Smallest demonstrated swappable unit:** complete self-improvement method
  implementing `Method.run()` against a fixed `Task` and agent/evaluator.
- **Promising narrower ports:**
  1. failure classifier/diagnoser;
  2. proposal generator;
  3. replay evaluator + admission gate;
  4. versioned repository/rollback.
- These are code-visible but not independently registered source plug-ins.
- **Required adapter input:** standard trace/outcome schema, exact sample ID,
  dev history, task evaluator/rollout authority, current library with fork
  semantics and a clean split contract.
- **Required output:** raw candidates, per-candidate probe transitions,
  accepted/rejected/no-op status, applied version and provenance.
- **Neighbors fixed:** agent, benchmark sample set, evaluator, prompt injection
  point, decoding, batch/probe/candidate budgets and skill capacity.
- **`paper_inspired` conditions:** accepting by writer judgement; evaluating only
  failures; no fresh baseline replay; using validation/test as the probe;
  allowing silent regressions; or losing rejected candidates.

## G. Native experimental design

**Paper provenance:** benchmarks/models/baselines/protocol from §3 and Table 1;
eight ablations from §3.5/Table 4; transfer Tables 2–3/5/13; compute/context
Table 6; sensitivity/gate/statistics Tables 9–14.

- **Benchmarks:** MedAgentBench, MedAgentBench-v2, FHIR-AgentBench; exploratory
  DBBench, OS Interaction, ALFWorld, WebShop.
- **Splits:** disjoint dev/validation/test; OOD held-out task types for two
  MedAgentBench variants. WebShop uses 100/50/50 from instances 0–199.
- **Models:** gpt-oss-120b, DeepSeek V4 Flash, Gemini 3.1 Flash Lite, GPT-4.1,
  GPT-5.4 low reasoning. Same model is native writer and executor.
- **Training:** five dev epochs, batch 48, probe 36, four candidates; best-val
  checkpoint; test/OOD once.
- **Decoding:** executor temperature 0/top-p 1; writer temperature 0.7/top-p 1;
  output cap 32,768.
- **Runs/statistics:** five seeds for open-source main cells, three for
  proprietary/ablations/transfer; mean±SD, 10,000-resample bootstrap CI,
  permutation tests and Cohen's d with stated small-n limits.
- **Baselines:** no skills, Sequential Memory, Batch Memory, ExpeL,
  Evo-MedAgent, SkillX; common injection point.
- **Key ablations:** no failure grouping; no regression budget; fixes-only;
  append-only; no gate K=4/K=1; two matched-compute selections discarding gate
  scores; sensitivity over batch/probe/candidate/invalid penalty.
- **Transfer axes:** writer×executor frozen-library matrix; cross-benchmark;
  cross-domain structured versus open-ended environments; OOD task types.
- **Efficiency/reliability:** training calls, inference tokens/library size,
  accepted/rejected rate, fixes/regressions/invalid actions, action-budget
  exhaustion and learning stability.

## H. Paper-reported findings

- On MedAgentBench the paper reports GRASP strongest across all five models;
  gpt-oss reaches 88.8%, 21.0 points over the strongest baseline.
- MedAgentBench-v2 is mixed: GRASP leads some in-domain cells, is within noise
  on others, and does not lead v2 OOD overall. The paper explicitly makes no
  v2-OOD superiority claim.
- No-gate drops 25.3 points; matched-compute variants remain near no-gate,
  attributing the difference to the admission decision rather than probe calls.
- Across five seeds, an edit is applied in 64% of batches; 16% of candidates
  are admitted; 36% of batches reject all four.
- Strong-writer→weak-executor transfer helps, but reverse transfer does not;
  the library is not fully model-agnostic.
- Probe validation dominates training compute—roughly 440 agent calls/batch.

These results are paper-reported; the public artifacts were inspected but not
rerun.

## I. SkillStack architecture and integration verdict

- GRASP strongly supports splitting `A` into
  `Diagnose/Evidence → Propose/Transform` and `L` into
  `Assess → Admit/Reject → Version/Checkpoint/Rollback`.
- Rejection/no-op is a first-class lifecycle outcome, not an exception.
- `R` must carry version lineage, writer, source failure group, candidate raw
  output, probe set IDs, transition counts and applied checkpoint.
- The source proves a useful high-level component contract (`Method`), while
  demonstrating that narrower internal ports still require explicit work.
- **Architecture verdict:** keep `R-A-D-C-L`; refine `A` and `L`; add a
  cross-cutting evaluation authority contract rather than a new top-level slot.
- **Fidelity status:** `paper_faithful_possible` only with a strictly disjoint
  proposal/probe split. The exact released first-batch fallback is a
  `source_variant`. GRASP remains the strongest released native reference, but
  the primary SkillStack result must be a slot-level swap.
- **First safe smoke test:** run the quickstart method interface and one small
  dev batch, verifying rejected candidates and fork isolation.
- **First matrix candidate:** native GRASP method versus an alternate proposer
  under the same gate, then native proposer under an alternate admission gate;
  keep task/agent/probe/evaluator fixed.
