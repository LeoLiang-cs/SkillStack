# Phase 2D (Week 3, continued) — Committed Plan: Harder Task Set + GLM few-shot attribution

**Status:** committed before runs. Continues `week3` per advisor decision.

## 0. Decisions recorded (2026-08-18)

1. Task scale: go all-in — add the `pick_two_obj_and_place` family (3 tasks)
   **and** one second instance per existing family (5 tasks) in one step.
2. D3 few-shot attribution: do it this week, with GLM runs capped at
   `max_steps = 12` to bound wall-clock time.
3. Reports stay under `reports/week3/`.
4. The in-flight full GLM pilot was killed; a lean few-shot probe replaces it.

## 1. Objective

Week 3 (Phase 2C) found a success ceiling: `deepseek-v4-flash` zero-shot
ReAct solves the five frozen tasks with or without skills, so skill utility
was unmeasurable (G2 failed), and the strict executor did not port to GLM
(F-15) — attributed either to a model capability floor or to prompt coupling.

Phase 2D has two objectives:

> **O1.** Re-test the skill channel on a harder task set where zero-shot
> ReAct is expected to fail, so that `oracle > no_skill/random` can be
> measured if it exists.
>
> **O2.** Attribute the GLM failure: is it prompt coupling (few-shot rescues
> validity) or a model capability floor (few-shot does not)?

## 2. D1 — Freeze and validate the harder task set

- Add `pick_two_obj_and_place` (3 tasks) and one second instance per the five
  existing families, selected from `valid_unseen` with a recorded rule.
- Freeze into `configs/p0_tasks_hard.json` using the same record shape as
  `configs/p0_tasks.json` (task_id, task_family, task_instruction,
  expected_skill_id, trajectory_file, game_file).
- Validate with a real ALFWorld reset per task (same checks as week-1
  `validate_p0_tasks.py`: task_type match, instruction match, solvable,
  accepted game file, non-empty admissible commands).
- **Gate D1:** every hard task resets with a non-empty admissible command
  list and passes the trajectory checks.

## 3. D2 — Hard set × 4 conditions (deepseek, 50 steps)

- Hold executor (`ReActExecutor`, frozen v1.1 prompt), backend
  (`deepseek-v4-flash`), library, adapter, runner, trace format, seed 42,
  `top_k=2`, `max_steps=50`.
- Four conditions: no_skill / random_skill / lexical / oracle over the 8-task
  hard set.
- **New gate G4:** on the hard set, `oracle` must strictly outperform
  `no_skill` and `random` on task success. (This is the regime where the
  skill channel can actually show.)
- Artifact: `w3_pilot_summary_deepseek_hard.json`.

## 4. D3 — GLM few-shot attribution probe (oracle only, 12-step cap)

- New frozen prompt `configs/p0_react_prompt_2shot.txt`: the v1.1 system
  prompt plus two short example trajectories (Thought/Action alternations
  with admissible commands) sourced from ALFWorld `train`, labelled as
  method-inspired (not a faithful ReAct reproduction).
- Run `zhipu_glm_flashx` + oracle + the 5 original tasks, `max_steps=12`.
- Metric: **action-validity rate** (fraction of steps with a valid action)
  and invalid-action retry rate — not task success.
- **Attribution decision:**
  - Validity recovers (≈ deepseek level) → prompt coupling (F-15/F-19
    reclassified).
  - Validity stays low → model capability floor → interface candidates
    (validity-floor contract or a fuzzy command-matching adapter).
- Artifact: `w3_glm_2shot_probe.json` + ledger update.

## 5. D4 — Structured skill injection (stretch, only if D2 shows no skill effect)

- If G4 fails because even oracle does not help, inject the selected skill as
  numbered procedure steps (not flat text) to test F-18 (flat-text vs
  structured skill consumption). One condition (oracle) × hard set ×
  deepseek.

## 6. Non-goals

- No prompt-engineering sweep beyond the single 2-shot variant.
- No model bake-off; GLM remains a portability/attribution target.
- No acquisition/governance, graph composition, Canonical Interface v1.

## 7. Artifacts

- `configs/p0_tasks_hard.json`, `configs/p0_react_prompt_2shot.txt`
- `scripts/validate_hard_tasks.py`
- `scripts/run_w3d_hard_pilot.py` (or reuse `run_w3_react_pilot.py` with a
  manifest override)
- `scripts/run_w3d_glm_2shot_probe.py`
- `reports/week3/` summary JSONs, ledger F-22+, fourth advisor brief (zh+en)

## 8. Risks

| Risk | Mitigation |
|---|---|
| Hard set still saturated by deepseek | G4 fails → report as ceiling finding; D4 structured-skill intervention |
| Few-shot prompt changes semantics vs v1.1 | New frozen prompt id; recorded as a prompt variant, not an in-place edit |
| GLM 12-step cap too tight to show validity | Report validity per step window; raise to 16 only with a recorded amendment |
