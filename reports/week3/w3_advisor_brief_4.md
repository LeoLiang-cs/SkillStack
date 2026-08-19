# SkillStack Phase 2C/2D — Fourth Advisor Update

**Status:** Executor swap (2C) complete; harder-regime experiments (2D) complete.
**Headline:** three findings — a robust ceiling, a budget-pressure skill
signal, and a resolved portability attribution.

## 1. Recap of the week

- **2C:** swapped the deterministic executor for a zero-shot LLM ReAct
  executor (zero neighbor changes). DeepSeek saturated the five frozen tasks
  (no-skill 5/5), so G2 failed; GLM failed on action validity (F-15).
- **2D:** froze an 8-task harder set (`pick_two` + second instances), tested
  skill utility under a tight budget, and ran a few-shot attribution probe
  for GLM.

## 2. Findings

### F1 — The ceiling is robust (not a task-selection artifact)

The 8-task harder set at 50 steps was also fully solved with **no skill**
(no-skill 8/8 = oracle 8/8). `deepseek-v4-flash` zero-shot ReAct saturates
ALFWorld `valid_unseen` text tasks across all six families. This is a
negative result of the environment + backbone pairing, not of the skill idea.

### F2 — Skill context helps under budget pressure (first positive signal)

On the `pick_two` family, oracle solved the three tasks in **47 total steps
vs 88 for no-skill** — nearly 2× efficiency, even at the success ceiling
(one no-skill episode took 48 of 50 steps).

Capping the budget at 20 steps converts efficiency into success:

| Condition | Success (3 pick_two tasks, 20 steps) |
|---|---:|
| no_skill | **1/3** |
| random_skill | 2/3 |
| lexical | 2/3 |
| oracle | 2/3 |

The no-skill condition is strictly below every skill-bearing condition. The
skill channel measurably helps when the budget binds.

### F3 — GLM failure was prompt coupling, not capability (attribution resolved)

Adding two worked examples raises GLM's first-try action-validity rate from
frequent failures (zero-shot) to **97.96%** across the five tasks. F-15 is
reclassified: the executor *does* port to GLM once the prompt carries
few-shot examples. GLM-4.7-FlashX is a viable, cheaper backend for the
executor with the 2-shot prompt.

## 3. Gates

| Gate | Result |
|---|---|
| G1 format (deepseek) | PASS (0 invalid actions) |
| G1 format (GLM zero-shot) | FAIL → **resolved** by 2-shot (97.96% valid) |
| G2 skill channel (5 tasks, 50 steps) | FAIL (ceiling: 5/5 = 5/5) |
| G4 skill channel (hard set, 50 steps) | FAIL (ceiling: 8/8 = 8/8) |
| G4' skill channel (pick_two, 20 steps) | PARTIAL (no_skill 1/3 < skill conditions 2/3, but oracle does not beat random) |

## 4. Claims we can now make

1. The executor slot is structurally interchangeable with full token/cost
   accounting (RQ2 boundary).
2. `deepseek-v4-flash` zero-shot ReAct saturates ALFWorld `valid_unseen` at
   50 steps — a reproducible ceiling finding across two task sets.
3. Under a binding budget, skill context measurably helps (no-skill 1/3 vs
   skill-bearing 2/3 on pick_two).
4. The strict ReAct executor ports to GLM with a 2-shot prompt (validity
   97.96%); the zero-shot failure was prompt coupling, not a capability floor.

## 5. Claims we still cannot make

1. That the *correct* skill specifically matters more than *any* skill text:
   oracle did not separate from random on pick_two (both 2/3).
2. Statistical conclusions (n=3 pick_two tasks).
3. General skill-utility conclusions beyond this regime.

## 6. Recommended next step

The discriminating regime is now identified: `pick_two` + a binding budget.
To turn F2 into a specific-skill result, in order:

1. **Expand pick_two instances** (n=3 → 9+) to power the oracle-vs-random
   comparison at the 20-step budget.
2. **Structured skill injection** (D4): inject numbered procedure steps
   rather than flat prose, so the *content* of the correct skill more
   strongly shapes the plan — the concrete test of week-2's F-06/F-07.
3. Keep efficiency (steps/tokens) as a co-primary metric alongside success.

## 7. Decisions requested

1. Expand pick_two instances and re-run the 4-condition tight-budget pilot,
   or first run D4 (structured skills) on the current 3 tasks?
2. Is "any skill text helps under budget" acceptable as a finding, or must we
   demonstrate correct-skill specificity before proceeding?
3. Backend: keep DeepSeek as primary, or switch to GLM-4.7-FlashX with the
   2-shot prompt (cheaper, now validated at 97.96% validity)?

## 8. Four-slide structure

1. **Swap + ceiling**: executor swap succeeded; deepseek saturates ALFWorld
   (8/8 no-skill).
2. **Skill signal**: pick_two efficiency (47 vs 88 steps) and the 20-step
   success split (1/3 vs 2/3).
3. **Portability resolved**: GLM 2-shot → 97.96% validity = prompt coupling.
4. **Decision**: expand pick_two / structured skills / backend choice.

## 9. Short spoken update

"This week I swapped in the LLM ReAct executor and hit a hard ceiling:
DeepSeek solves ALFWorld even with no skills — on both the original five
tasks and an eight-task harder set, no-skill reached 8/8. So at 50 steps,
skill utility is unmeasurable.

But the harder two-object tasks gave the first real signal: the oracle skill
solved them in 47 steps versus 88 for no-skill, and when I capped the budget
at 20 steps, no-skill dropped to 1/3 while every skill-bearing condition
reached 2/3. Skills do help when the budget binds; we just can't yet show the
correct skill beats a random one.

Separately, the GLM failure turned out to be prompt coupling, not a model
limit: with two examples, its action validity jumped to 98%, so GLM is a
viable cheap backend for this executor.

Next I want to expand the two-object tasks to about nine and re-run the
tight-budget comparison — that is where a specific-skill result can come
from. And in parallel, test injecting skills as numbered steps instead of
flat prose."
