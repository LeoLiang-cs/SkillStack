# Week 3 — Adapter-Friction Ledger (Phase 2C additions)

Week-1 (F-01…F-05) and week-2 (F-06…F-14) entries remain in
[`../week1/phase6_pilot_audit.md`](../week1/phase6_pilot_audit.md) and
[`../week2/w2_friction_ledger.md`](../week2/w2_friction_ledger.md). The
week-3 ReAct executor swap adds the following.

| ID | Boundary | Observed evidence | Classification | Candidate information to test later | Status |
|---|---|---|---|---|---|
| F-15 | Executor ↔ backend (GLM) | `glm-4.7-flashx` repeatedly proposes commands outside the admissible list under the zero-shot prompt, including `go to drawer 3` where drawer 3 is a nested receptacle-object. Retry feedback alone does not always recover the episode. **D3 attribution (2-shot):** adding two worked examples raises GLM's first-try action-validity rate to 0.9796 (vs frequent invalids zero-shot) → this failure is **prompt coupling, not a model capability floor** (reclassified 2026-08-18). | Prompt/backend interaction; not a model capability limit | Few-shot examples as a portability aid; validity-floor contract as an alternative | Resolved by attribution: prompt coupling |
| F-16 | Executor ↔ backend (both) | Both providers' native thinking mode consumed the output budget before emitting content (4 `reasoning_tokens`, empty reply at `max_tokens=4`). Native thinking must be explicitly disabled; our own Thought format carries the reasoning. | Backend capability mismatch: native thinking ≠ ReAct thought | — | Resolved in config (`thinking: disabled`); recorded |
| F-17 | Executor ↔ environment | ALFWorld force-ends episodes at its internal 50-step cap with `dones=True, score=0`. The executor's `environment_done` stop reason therefore conflates goal completion with step-cap termination; success is still read from the score, but the stop-reason vocabulary loses the distinction. | Outcome-signal semantics | Distinct `environment_step_cap` stop reason | Recorded; stop-reason refinement is a candidate |
| F-18 | Skill → executor (strategy) | Pilot (deepseek, 50 steps): with the oracle skill injected, the light task still failed via premature `done`; heat/cool needed 30+ steps even with the correct skill, and the no-skill condition solved all five tasks in fewer mean steps (14.2) than oracle (26.3). Flat-text skill context provides no measurable strategy advantage at the success ceiling. | Prompt-level skill consumption is weaker than structured plan consumption (week 2's hard-coded skeletons) | Structured procedure fields (ordered steps) to guide the LLM executor | Confirmed by pilot; intervention candidate |
| F-19 | Prompt ↔ executor | Two prompt revisions during smoke testing: v1 (format rules only) died at step 2 on GLM; v1.1 (verbatim-copy emphasis + "not in list = not possible" + retry feedback repeats the admissible list) extended GLM runs to 12+ valid steps but did not eliminate invalid actions. The D3 2-shot variant then raised GLM first-try validity to 0.9796. | Prompt design is a real intervention; few-shot is the decisive lever for this backend | A prompt variant registry; the 2-shot prompt as the new portability default for GLM | Resolved: few-shot recovers validity |
| F-20 | Backend ↔ cost model | DeepSeek moved to peak/off-peak pricing effective 2026-08-16 UTC; list-price-based estimates in `configs/llm_backends.json` use the peak (ceiling) rates because the advisor chose "run anytime". GLM-4.7-FlashX has a free tier and a paid FlashX tier; our config records the paid tier. | Operational pricing volatility | — | Recorded; estimates are ceilings, not bills |
| F-21 | Executor ↔ sampling | Identical condition + prompt + task produced different trajectories across probe and pilot (e.g. deepseek light task: probe=8-step early `done`; pilot no-skill=10-step success). temperature=0 does not guarantee cross-call reproducibility on these providers. | Provider sampling nondeterminism | Per-run model version + request id in traces; seed-level reruns as the reproducibility unit | Observed; trace-level |

## Notes

- The retrieval→execution adapter remains structurally lossless (F-04 holds
  across week-3 runs): the friction is now in (a) the executor↔backend
  command-validity boundary and (b) prompt-level skill consumption.
- F-15 is the first observed case where a SkillStack component **does not
  port losslessly across backends** — reported as such, not hidden.
