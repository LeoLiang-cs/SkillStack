# Algorithm Card — GraSP

## A. Identity and evidence

- **Paper:** *GraSP: Graph-Structured Skill Compositions for LLM Agents*
- **arXiv:** 2604.17870, v1, submitted 2026-04-20
- **Authors/year:** Tianle Xia, Lingxiang Hu, Yiding Sun, Ming Xu, Lan Xu,
  Siying Wang, Wei Xu, Jie Jiang (2026)
- **Paper:** <https://arxiv.org/abs/2604.17870>
- **Primary text read:** <https://huggingface.co/papers/2604.17870.md> and
  <https://arxiv.org/html/2604.17870v1>
- **Source snapshot date:** 2026-08-25
- **Evidence read:** complete architecture §2, experiments §3,
  limitations §6, formal definitions Appendix A, Algorithms 1–4 and ablation
  protocol Appendices B–C.
- **Official code status:** neither the arXiv/Hugging Face metadata nor an
  exact-title/author search identified a verified official repository as of
  the snapshot date. This does not prove that code is unavailable elsewhere.
- **Reproduction assets verified:** paper/HTML and printed pseudocode. No code,
  prompts, skill libraries, episodic memories, verifier implementations, or
  complete configs were verified.
- **Evidence gaps:** accessible paper tables do not fully expose the default
  hyperparameter values; skill-library construction, memory generation,
  verifier prompts, compiler prompts, confidence calibration data, and exact
  environment versions remain unavailable.

## B. Claimed contribution

- **Problem:** retrieval produces a flat list but does not express how skills
  depend on each other, how to execute them, or how to localize repair.
- **Claimed algorithmic unit:** an executable graph architecture and runtime
  with a compilation layer between retrieval and execution.
- **New mechanism:** memory-conditioned retrieval; typed DAG compilation;
  node-level pre/postcondition verification; five bounded local graph-repair
  operators; confidence-based fallback to ReAct.
- **Not claimed:** acquisition/evolution of skills or a single isolated
  composer independent of its retriever, verifier, executor, and fallback.

## C. Native pipeline context

- **Upstream:** task `q`, initial environment state `x_0`, goal parse, typed
  skill library `L`, and episodic experience memory `M`.
- **Downstream/native host:** GraSP owns execution through environment actions;
  ReAct is its reactive fallback.
- **Persistent state:** typed library; successful trajectory memory; historical
  success rate for confidence bins.
- **External machinery:** semantic retrieval, LLM memory summarization, LLM
  node proposal/compilation, skill implementations, node verifiers, reactive
  agent, and environment state predicates.
- **Offline/maintenance:** build and type the skill library, collect episodic
  memory, calibrate confidence/history, and define verifiers.
- **Online:** retrieve, route, compile, execute/verify, repair/replan/fallback.
- **Update clock:** retrieval and compilation can repeat after a failed repair
  on the residual task; node state changes after every execution.

## D. Algorithm anatomy

### Inputs

- Task `q`, parsed goal `g`, and current state `x`.
- Typed skill library `L`; a skill must expose schema, implementation,
  preconditions, effects, input/output bindings, and verifier.
- Episodic memory `M` containing successful trajectories and skill-use history.
- Retrieval mixture/calibration parameters, confidence thresholds, candidate
  count `M`, repair locality/size budgets, node repair limit, and global replan
  limit.

### State and artifacts

- Retrieved successful memories `R`, distilled summary `Gamma`, direct and
  memory-induced skill distributions, selected candidate skills, and calibrated
  retrieval confidence `c_ret`.
- Executable graph `G=(V,E)` with source, sink, and instantiated skill nodes.
- Edge types: hard `state`, hard `data`, and soft `order`.
- Node record
  `<schema, arguments, precondition, effect, verifier, status, confidence,
  repair_budget>`.
- Failure event
  `<node, type, structured_message, current_state>`, where type is
  precondition, execution, postcondition, or timeout.
- Verified-node set, residual task, repair counts, and replan count.

### Ordered mechanism

1. Parse the task goal and initialize environment/replan state.
2. Retrieve Top-k similar successful memories and summarize them.
3. Fuse the direct semantic skill distribution with a memory-induced prior
   derived from successful trajectories; select Top-M skills.
4. Compute retrieval confidence from mean memory similarity, direct/memory
   agreement, top-skill margin, goal coverage, and historical calibration.
5. If confidence is below `tau_low`, return ReAct fallback. Medium confidence
   receives a larger repair budget; high confidence uses full GraSP.
6. Ask the compiler LLM to propose instantiated nodes from the task, goal,
   state, retrieved skills, and memory summary; validate schemas and bindings.
7. Add `state` edges for effect–precondition matches, `data` edges for
   output–input bindings, and `order` edges from memory precedence/resource
   conflicts. Remove low-confidence soft edges to resolve cycles; attach
   verifiers and repair budgets.
8. Reject invalid graphs and fall back to ReAct. A valid GraSP must be acyclic,
   source-to-sink reachable, goal-complete, and executable.
9. Traverse ready nodes in topological order. Check precondition, execute the
   skill with bound arguments, then run the postcondition verifier.
10. Mark successful nodes verified and preserve the resulting state.
11. On failure, create a typed failure event and rank five local repair
    operators: `Rebind`, `InsertPrereq`, `Substitute`, `Rewire`, `Bypass`.
12. Accept only a graph-valid patch within the h-hop and node/edge budgets;
    reset the affected subgraph while preserving unaffected verified nodes.
13. If local repair fails, recompile the residual task within a global replan
    budget; otherwise fall back to ReAct on the residual goal.

### Outputs and failure behavior

- **Primary output:** environment success/failure plus a verified execution
  trace; internally, the compiler emits a typed executable DAG.
- **Auxiliary output required for SkillStack:** candidate distributions,
  memory evidence, confidence/features, compiled graph, node status,
  verification results, failure events, repair patches, fallback reason, and
  residual task.
- **Failure output:** invalid retrieval confidence, compile failure, typed node
  failure, invalid/exhausted local repair, exhausted global replan, or ReAct
  fallback result.
- **Confidence:** calibrated retrieval confidence controls execution mode; node
  confidence and repair budgets are graph attributes.

### Invariants

- The graph remains acyclic, source-to-sink reachable, goal-complete, and each
  node remains bound and verifiable.
- Hard state/data edges cannot be removed without proof they are obsolete;
  order edges may be rewired locally.
- New repair nodes must refer to library skills and all arguments must
  type-check.
- Unaffected verified ancestors and their observed progress cannot be changed
  by local repair.
- Local repair must stay within node, edge, hop, and retry budgets.
- Repair/fallback/replan events must remain observable; replacing them with one
  generic execution failure destroys the paper's main mechanism.

## E. Candidate plug-in boundary

- **SkillStack responsibilities:** Discovery/Selection (`D`) plus
  Composition/Execution (`C`), with Representation (`R`) supplying typed
  contracts.
- **Internal primitives:**
  `Retrieve → Confidence Route → Compile → Execute → Verify → Local Repair →
  Replan/Fallback`.
- **Method type:** **composite orchestrator**. The paper ablates internal stages,
  but the claimed GraSP method owns the full runtime.
- **Smallest faithful whole-method swap:** candidate retrieval through verified
  execution/fallback, with the typed library/memory treated as required inputs.
- **Most promising narrower port:** `DAG compiler + verified graph executor +
  local repair`, taking a matched candidate set and memory evidence. This is a
  proposed SkillStack boundary, not a paper-demonstrated independent plug-in;
  it must first match native GraSP with retrieval fixed.
- **Required adapter input:** typed skills, actual environment state/predicate
  access, executable implementations, argument schemas, verifiers, candidate
  scores, memory evidence, task/goal, and budgets.
- **Required output:** executable graph and complete trace/failure/repair
  provenance, or a typed fallback request carrying the residual goal/state.
- **Neighbors fixed in a compiler swap:** retriever/memory, task set, skill
  library, verifier semantics, executor, fallback, model, and budgets.
- **`paper_inspired` conditions:** a prompt that merely writes a flat plan;
  skills without pre/effect/data contracts; no executable typed DAG; no
  node-level verification; global retry instead of five local repair operators;
  or no confidence-triggered fallback.

## F. Native experimental design

**Paper provenance:** benchmark/model/control settings and Table 1 come from
§3.1–§3.2; component and recovery axes from §3.3/Table 2/Figures 2–3;
quantity/quality stress from §3.4/Figures 4–5; protocols and sensitivity axes
from Appendix C.

### Evaluation grid

- ALFWorld seen/unseen; ScienceWorld with 30 task types; WebShop 500 sessions;
  InterCode NL2Bash.
- Average reward for ALFWorld, ScienceWorld, and WebShop; success rate for
  InterCode; average environment steps for all.
- Eight backbones: DeepSeek V3.2 (primary), GPT-4.1, Claude-4-Sonnet, GLM-5,
  Gemini 2.5 Pro, o4 Mini, Qwen3-235B, Kimi-K2.5.
- Official APIs at temperature 0; results averaged over three runs.
- Same skill library and episodic memory for ExpeL, ReAct+Skills, and GraSP.
- Exact task counts beyond WebShop, library sizes, step budgets, and the default
  values in Table 3 require source/config recovery before reproduction.

### Baselines and controls

- ReAct, Reflexion, ExpeL, and flat `ReAct + Skills`.
- Component sequence on DeepSeek V3.2: ReAct/no skills; monolithic/all skills;
  flat skills; + experience memory; + DAG compilation; + local repair; +
  confidence routing (full GraSP).
- Destructive ablations: `w/o DAG`, `w/o Local Repair`, `w/o Confidence
  Routing`; local repair replaced by equal-budget global replanning.
- Stress axes: task complexity, retrieved skill quantity, skill quality,
  failure type, confidence thresholds, and repair budget.

### Metrics and transfer axes

- Task reward/score/success and average environment steps.
- Failure recovery rate by failure class and fallback/repair behavior.
- Quantity and quality robustness; task-complexity advantage.
- Eight-backbone host robustness is reported, but a component-by-host swap with
  independently implemented hosts is not.
- Token count, wall time/cost, compile validity rate, verifier false decisions,
  and adapter friction are not reported as primary matrix metrics and should be
  added for SkillStack portability testing.

## G. Paper-reported findings

- **Table 1:** the paper reports that GraSP wins all 48 model/split cells,
  averages +6.9 points over the strongest per-cell baseline, and uses roughly
  24% fewer steps than ReAct and 10% fewer than ReAct+Skills.
- **Table 2:** every staged component contributes; the authors identify DAG
  compilation as most critical. Local repair beats equal-budget global replan.
- **Figures 2–5:** reported advantage grows from about 6% on short tasks to 18%
  on long tasks; precondition-failure recovery is 84.2%; flat execution peaks
  around three skills then degrades, while GraSP remains robust up to eight;
  low-quality skills reduce GraSP by about 5% versus about 9% for flat use.
- **Limitations §6:** a DAG cannot naturally express cyclic/iterative control;
  experiments cover text-based interactive environments only. Claims about
  multimodal, APIs, and multi-agent settings are proposed extensions, not
  demonstrated results.

These are paper-reported findings, not SkillStack reproduction results.

## H. SkillStack architecture test

- High-level `R-A-D-C-L` still covers the method, but current `C` conflates at
  least `Compile/Plan`, `Execute`, `Verify`, and `Repair`.
- GraSP's retrieval/memory stage belongs in `D`; confidence routing crosses the
  `D→C` boundary and therefore needs an explicit control-plane port.
- Current Markdown/native payloads do not guarantee schemas, bound arguments,
  preconditions, effects, data outputs, verifiers, or state predicates.
- Current structured ReAct is not GraSP: it has no typed executable DAG,
  graph-validity gate, node verification, or locality-bounded repair algebra.
- Graph meaning must remain typed: a SkillReranker state-alignment graph and a
  GraSP executable skill-invocation DAG are different artifacts.
- **Provisional verdict:** keep the five responsibilities, refine `C` into
  internal primitives, and treat `R` as a cross-cutting typed artifact
  contract. Whether Verify/Repair deserve top-level slots remains open until
  the remaining cards are read.

## I. Reproduction and integration verdict

- **Fidelity status:** `blocked` for exact native reproduction because code,
  libraries, memories, prompts/verifiers, and full configs are not verified.
- **Native reproduction requirement:** reconstruct the typed skill contract,
  matched memories, retrieval/confidence, compiler, graph validator, executor,
  five repairs, replan, and ReAct fallback before a cross-host claim.
- **First safe smoke test:** compile and execute one deterministic ALFWorld task
  with two or three typed skills; inject one known precondition failure and
  verify preservation of completed ancestors plus bounded `InsertPrereq` or
  `Rebind` repair.
- **First controlled portability test:** hold GraSP retrieval/library/verifiers
  fixed and swap only the host action adapter; then hold the host fixed and
  compare native compiler with a flat composer.
- **Expected friction:** absent typed predicates and verifiers, environment
  state translation, executable argument binding, fallback ownership, memory
  schema, and incomplete hyperparameters.
- **Open question:** whether the compiler+executor can be independently swapped
  without changing the confidence router is an experimental question; do not
  pre-label it plug-and-play.
