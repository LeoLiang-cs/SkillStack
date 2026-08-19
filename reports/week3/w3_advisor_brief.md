# SkillStack Phase 2C — Third Advisor Update

**Status:** Executor-slot swap complete; DeepSeek pilot analyzed; GLM pilot
recorded as a portability control.
**Headline:** the swap itself succeeded — and exposed that the five frozen
tasks are already solved zero-shot by `deepseek-v4-flash`, so skill injection
showed no measurable benefit. Both findings are reported.

## 1. What changed since the second brief

The deterministic `SkillPlanExecutor` (week 2) was replaced by a
**zero-shot ReAct executor** backed by an external LLM, with zero changes to
the runner, adapter, retrievers, frozen tasks, or trace format — the first
real executor-slot swap (RQ2 boundary test).

- `src/skillstack/llm/client.py`: zero-dependency OpenAI-compatible client,
  retries, per-call usage/latency/cost accounting, native thinking disabled.
- `src/skillstack/execution/react.py`: strict Thought/Action loop, exact
  admissible-command validation, one retry with the admissible list repeated,
  full per-step rationale and token accounting.
- Backends: `glm-4.7-flashx` (z.ai) primary, `deepseek-v4-flash` secondary,
  configured in `configs/llm_backends.json`; keys via git-ignored `.env`.

A pre-pilot oracle probe (5 tasks, both backends) produced the amendment in
`plan_phase2c.md`: strict ReAct validity is met by DeepSeek (0 invalid
actions) but not by GLM (frequent invalid actions). The full four-condition
pilot therefore ran on DeepSeek as primary evidence, with GLM retained as a
recorded portability run.

## 2. Results (deepseek-v4-flash, 50-step budget)

| Condition | Success | Mean steps | LLM calls | Est. cost |
|---|---:|---:|---:|---:|
| no_skill | **5/5** | 14.2 | 71 | $0.016 |
| random_skill | **5/5** | 20.0 | 100 | $0.025 |
| lexical | **5/5** | 21.2 | 106 | $0.028 |
| oracle | **4/5** | 26.3 (successes) | 115 | $0.025 |

- Zero invalid actions across all 20 episodes (100% format validity).
- The one failure is the oracle-condition light task: the model declared
  `done` after 8 steps without satisfying both goal conditions.
- Per-task success is uniformly at ceiling; the differences are in
  **efficiency**, where the no-skill condition was unexpectedly the leanest.

## 3. Gates

- **G1 (format):** PASSED on DeepSeek (0 invalid actions); FAILED on GLM
  (frequent invalid-action deaths — see F-15).
- **G2 (skill channel):** **FAILED**. C-oracle (4/5) is not strictly better
  than C-no-skill (5/5) or C-random (5/5), and skill injection did not reduce
  steps. The plan anticipated this: the skill context is not meaningfully
  consumed when the backbone solves the tasks zero-shot within budget.
- **G3 (swap):** PASSED. The runner/adapter/retriever/trace stack required no
  changes; all traces carry the same shape plus LLM accounting.

## 4. What this means (honest reading)

1. **The executor slot is swappable in structure** — a prompt-based policy
   replaced a hand-coded one without touching neighboring components.
2. **The measurement regime is saturated**: five single-family tasks at 50
   steps are too easy for `deepseek-v4-flash`. Skill utility cannot be
   measured where the ceiling is reachable without skills. This is a
   negative result of the task set + budget, not of the skill idea.
3. **Backend portability is conditional**: the strict ReAct executor works
   with DeepSeek and fails on GLM's command validity. This is the first
   recorded case of a SkillStack component not porting losslessly (F-15).
4. **temperature=0 is not reproducible across providers** (F-21): identical
   conditions produced different trajectories between probe and pilot.

## 5. Friction ledger additions

F-15 … F-21 in [`w3_friction_ledger.md`](w3_friction_ledger.md): nested
receptacle-object vocabulary, native-thinking token capture, env step-cap
semantics, flat-text skill consumption vs structured plans, prompt-version
effects, pricing volatility, and sampling nondeterminism.

## 6. Claims we can now make

1. The executor slot is interchangeable at the structural level, with full
   token/cost/latency accounting in traces (35/35 unit tests; 20+ recorded
   episodes).
2. On this task set and budget, `deepseek-v4-flash` zero-shot ReAct saturates
   success, and flat skill context shows no measurable benefit — the first
   ceiling finding of the project.
3. The strict executor does not port losslessly across backends (GLM
   validity failure); prompt iteration helped but did not cure it.

## 7. Claims we still cannot make

1. Anything about skill utility in general — the ceiling masks it here.
2. That GLM-class models cannot do ReAct with a better prompt (few-shot is
   the next sanctioned variant, untested).
3. Statistical conclusions (5 tasks, raw counts).

## 8. Recommended next step

To make skill utility measurable again, hold the executor fixed and change
the **measurement regime**, in this order:

1. **Tighten the step budget** (e.g. 10 steps): where zero-shot ReAct
   struggles, does the oracle skill context recover episodes the no-skill
   condition cannot? This converts efficiency pressure into success
   differences.
2. **Add the harder tasks** the manifest deliberately excluded (the
   `pick_two_obj_and_place` family) plus a second instance per family.
3. Only then test **structured skill injection** (procedure steps, not flat
   text) as the skill-representation intervention — the week-2 F-06/F-07
   candidate made concrete.

## 9. Decisions requested

1. Adopt the tight-budget regime (e.g. 10 steps) for the next week, or keep
   50 and accept the ceiling as a published negative result?
2. GLM backend: keep it as a recorded portability failure, or add the
   few-shot prompt variant to attempt a rescue?
3. Expand the task set now (pick_two family + more instances), or wait until
   the regime question is settled?

## 10. Four-slide structure

1. **Swap**: prompt-based ReAct replaced the hand-coded executor, zero
   neighbor changes, full accounting.
2. **Evidence**: 5/5/5/4 success table; 0 invalid actions; step counts.
3. **Findings**: ceiling effect (G2 fail), GLM validity portability failure,
   temp-0 nondeterminism.
4. **Decision**: tighten budget / expand tasks / structured skills — which
   regime next?

## 11. Short spoken update

"Last week the deterministic executor showed skills change outcomes — but
only because the skills were the plan source. This week I swapped in a real
LLM ReAct executor, keeping everything else untouched: the swap itself
worked, with full token and cost accounting.

The result is a textbook ceiling effect: DeepSeek solves all five frozen
tasks zero-shot, even with no skill injected, and the no-skill condition was
actually the most efficient. The oracle condition was the only failure —
the model declared the task done too early. So the skill channel shows no
measurable benefit under this regime, and the gate I committed to failed
exactly as the plan anticipated.

The second finding is portability: the same strict executor fails on GLM,
which repeatedly proposes commands that are not admissible. That is our
first recorded case of a component not porting losslessly across backends.

My proposal for next week: keep the executor, but tighten the step budget so
zero-shot ReAct stops saturating success — then we can see whether the skill
context rescues episodes the no-skill condition cannot. And separately, add
the harder two-object tasks the manifest deliberately excluded."
