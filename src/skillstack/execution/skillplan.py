"""Deterministic multi-step executor that consumes selected skill context.

SkillStack-authored, hand-coded policy for Phase 2A. It is NOT a reproduction
of ReAct or any paper method, and it makes no generality claim beyond the
frozen ALFWorld task set. Its purpose is to close the causal chain between
selected skills and task outcomes:

- The plan skeleton comes from the selected skill's ``Procedure`` (keyed by
  skill id in a hard-coded, explicitly reported mapping).
- Task-specific names (object, destination, appliance) are bound from the
  environment's own ``Your task is to:`` sentence in the initial observation.
- Every executed action records a rationale: plan step, skill id, and the
  reason the command was chosen.
- With no selected skill, a generic explore-take-place plan is used that
  performs no transformations; this is the honest no-skill baseline.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

from skillstack.task_semantics import (
    APPLIANCE_BY_SKILL,
    SYNONYMS,
    TRANSFORM_VERB_BY_SKILL,
    parse_task_semantics,
)

# Plan skeletons keyed by the six static library skill ids. Step names are
# executor-internal and correspond to the human-readable Procedure steps of
# the matching native artifact. This mapping is executor-side hard-coded
# knowledge and is reported in every executor report.
PLAN_STEPS_BY_SKILL: Dict[str, Tuple[str, ...]] = {
    "skill_pick_and_place": (
        "find_and_take_object",
        "goto_destination",
        "prepare_receptacle",
        "place_object",
    ),
    "skill_light_inspection": (
        "find_and_take_object",
        "find_and_use_appliance",
    ),
    "skill_clean_then_place": (
        "find_and_take_object",
        "goto_appliance",
        "transform_object",
        "goto_destination",
        "prepare_receptacle",
        "place_object",
    ),
    "skill_heat_then_place": (
        "find_and_take_object",
        "goto_appliance",
        "transform_object",
        "goto_destination",
        "prepare_receptacle",
        "place_object",
    ),
    "skill_cool_then_place": (
        "find_and_take_object",
        "goto_appliance",
        "transform_object",
        "goto_destination",
        "prepare_receptacle",
        "place_object",
    ),
    # Not exercised by the frozen five tasks; kept inert with a warning.
    "skill_pick_two_then_place": (
        "find_and_take_object",
        "goto_destination",
        "prepare_receptacle",
        "place_object",
    ),
}

GENERIC_NO_SKILL_PLAN: Tuple[str, ...] = (
    "find_and_take_object",
    "goto_destination",
    "prepare_receptacle",
    "place_object",
)

# Exploration priority for object search: ALFWorld objects are most often on
# open surfaces, then on appliance tops, then inside containers. Hand-coded
# heuristic; reported as executor knowledge.
RECEPTACLE_TYPE_ORDER = (
    "countertop", "shelf", "desk", "sidetable", "dresser", "bed", "sofa",
    "armchair", "ottoman", "coffeetable", "diningtable", "bathtubbasin",
    "toilet", "cart", "table",
    "fridge", "microwave", "sinkbasin", "stoveburner", "toaster",
    "coffeemachine", "garbagecan", "drawer", "cabinet", "safe",
    "laundryhamper",
)


def _receptacle_priority(command: str) -> int:
    """Lower is better. Unknown types rank last but before nothing."""

    if not command.startswith("go to "):
        return 1000
    target = command[len("go to "):]
    for index, type_name in enumerate(RECEPTACLE_TYPE_ORDER):
        if target.startswith(f"{type_name} "):
            return index
    return 900


class SkillPlanExecutor:
    """Execute a skill-derived plan one admissible ALFWorld action at a time."""

    name = "skill_plan_executor"

    def __init__(self, step_budget_per_plan_step: int = 24) -> None:
        self.step_budget_per_plan_step = step_budget_per_plan_step

    def execute(
        self,
        env: Any,
        initial_observation: str,
        initial_info: Dict[str, Any],
        execution_input: Dict[str, Any],
        recorded_actions: Optional[Iterable[str]] = None,
        task_record: Optional[Dict[str, Any]] = None,
        max_steps: Optional[int] = None,
    ) -> Dict[str, Any]:
        _validate_execution_input(execution_input)
        if task_record is None:
            raise ValueError("SkillPlanExecutor requires the episode task record.")
        max_steps = max_steps if max_steps is not None else 50

        warnings: List[str] = []
        skill_ids = execution_input["selected_skill_ids"]
        top_skill_id = skill_ids[0] if skill_ids else None
        if top_skill_id is None:
            plan = list(GENERIC_NO_SKILL_PLAN)
        elif top_skill_id in PLAN_STEPS_BY_SKILL:
            plan = list(PLAN_STEPS_BY_SKILL[top_skill_id])
        else:
            plan = list(GENERIC_NO_SKILL_PLAN)
            warnings.append(f"Unknown selected skill {top_skill_id!r}; using generic plan.")

        if top_skill_id == "skill_pick_two_then_place":
            warnings.append(
                "pick_two plan skeleton is not implemented; executor runs the first-object path only."
            )

        binding = parse_task_semantics(task_record, initial_observation)
        warnings.extend(binding.pop("warnings"))

        current_info = initial_info
        observations = [initial_observation]
        actions: List[str] = []
        rationales: List[Dict[str, Any]] = []
        rewards: List[float] = []
        success = False
        stop_reason = "max_steps_exhausted"
        plan_pointer = 0
        steps_since_advance = 0
        visited: List[str] = []
        at_receptacle: Optional[str] = None
        last_action: Optional[str] = None
        holding = False
        placed = False

        while len(actions) < max_steps and plan_pointer < len(plan):
            step_name = plan[plan_pointer]
            admissible = list(current_info.get("admissible_commands", []))
            action, reason, advance = _choose_action(
                step_name=step_name,
                admissible=admissible,
                binding=binding,
                top_skill_id=top_skill_id,
                visited=visited,
                at_receptacle=at_receptacle,
                last_action=last_action,
            )

            if action is None and advance:
                rationales.append(
                    {
                        "step_index": len(actions),
                        "plan_step": step_name,
                        "skill_id": top_skill_id,
                        "chosen_action": None,
                        "reason": reason,
                        "advance": True,
                    }
                )
                plan_pointer += 1
                steps_since_advance = 0
                visited = []
                continue

            if action is None:
                stop_reason = "plan_step_unavailable"
                warnings.append(
                    f"Plan step {step_name!r} found no admissible command "
                    f"(steps_since_advance={steps_since_advance}, reason={reason!r})."
                )
                break

            if action.startswith("go to "):
                visited.append(action[len("go to "):])
                at_receptacle = action[len("go to "):]

            next_observations, scores, dones, next_infos = env.step([action])
            actions.append(action)
            observations.append(next_observations[0])
            rewards.append(float(scores[0]))
            current_info = _unbatch_info(next_infos)
            last_action = action
            feedback = next_observations[0]
            holding = holding or bool(re.search(r"You pick up the", feedback))
            if re.search(r"You move the", feedback):
                placed = True
                holding = False
            if re.search(r"You (heat|clean|cool) the", feedback):
                holding = True

            rationales.append(
                {
                    "step_index": len(actions),
                    "plan_step": step_name,
                    "skill_id": top_skill_id,
                    "chosen_action": action,
                    "reason": reason,
                    "advance": advance,
                }
            )

            if advance:
                plan_pointer += 1
                steps_since_advance = 0
                # Exploration state is scoped to one plan step: a later step
                # (e.g. appliance search) must be allowed to revisit
                # receptacles seen during object search.
                visited = []
            else:
                steps_since_advance += 1
                if steps_since_advance > self.step_budget_per_plan_step:
                    stop_reason = "plan_step_budget_exhausted"
                    warnings.append(
                        f"Plan step {step_name!r} exceeded {self.step_budget_per_plan_step} actions."
                    )
                    break

            if dones[0]:
                success = bool(scores[0] > 0)
                stop_reason = "environment_done"
                break

        if plan_pointer >= len(plan) and stop_reason == "max_steps_exhausted":
            stop_reason = "plan_completed_without_success"

        return {
            "executor_name": self.name,
            "action_source": "skill_derived_plan",
            "executor_notes": (
                "Plan skeletons are hard-coded per static skill id. Appliance names are "
                "hard-coded per skill id. Object/destination names are bound from the "
                "environment's own task sentence in the initial observation."
            ),
            "plan_skill_id": top_skill_id,
            "plan_steps": plan,
            "task_binding": binding,
            "actions": actions,
            "observations": observations,
            "action_rationales": rationales,
            "rewards": rewards,
            "success": success,
            "stop_reason": stop_reason,
            "warnings": warnings,
        }


def _choose_action(
    step_name: str,
    admissible: List[str],
    binding: Dict[str, Any],
    top_skill_id: Optional[str],
    visited: List[str],
    at_receptacle: Optional[str],
    last_action: Optional[str],
) -> Tuple[Optional[str], str, bool]:
    """Choose one admissible command that advances the current plan step."""

    object_name = binding["object"]
    destination = binding["destination"]
    appliance = binding["appliance"] or APPLIANCE_BY_SKILL.get(top_skill_id or "")

    if step_name == "find_and_take_object":
        take = _first(admissible, lambda c: c.startswith(f"take {object_name} "))
        if take:
            return take, "object visible at current receptacle", True
        open_cmd = _first(admissible, lambda c: c.startswith("open "))
        if open_cmd:
            return open_cmd, "current receptacle is closed; open it to look inside", False
        go = _next_unvisited(admissible, visited)
        if go:
            return go, "explore an unvisited receptacle for the object", False
        if last_action != "look" and "look" in admissible:
            return "look", "re-observe the current location", False
        return None, "no unexplored receptacle and look already used", False

    if step_name == "goto_appliance":
        target = appliance
        if not target:
            return None, "no appliance bound for this skill", False
        if at_receptacle and at_receptacle.startswith(f"{target} "):
            return None, f"already at appliance receptacle {target!r}", True
        go = _first(admissible, lambda c: c.startswith(f"go to {target} "))
        if go:
            return go, f"navigate to appliance receptacle {target!r}", True
        return None, f"no admissible navigation to appliance {target!r}", False

    if step_name == "goto_destination":
        target = destination
        if not target:
            return None, "no destination bound from the task", False
        if at_receptacle and at_receptacle.startswith(f"{target} "):
            return None, f"already at destination receptacle {target!r}", True
        go = _first(admissible, lambda c: c.startswith(f"go to {target} "))
        if go:
            return go, f"navigate to destination receptacle {target!r}", True
        return None, f"no admissible navigation to destination {target!r}", False

    if step_name == "prepare_receptacle":
        if not destination:
            return None, "no destination bound from the task", False
        open_cmd = _first(admissible, lambda c: c.startswith(f"open {destination} "))
        if open_cmd:
            return open_cmd, "destination receptacle is closed; open it before placing", False
        return None, "destination needs no preparation", True

    if step_name == "place_object":
        move = _first(
            admissible,
            lambda c: c.startswith(f"move {object_name} ") and f" to {destination} " in c,
        )
        if move:
            return move, "destination reachable; place the object", True
        if last_action != "look" and "look" in admissible:
            return "look", "waiting for the place command to become admissible", False
        return None, "no admissible place command", False

    if step_name == "transform_object":
        if not appliance:
            return None, "no appliance bound for transformation", False
        verb = TRANSFORM_VERB_BY_SKILL.get(top_skill_id or "", "")
        transform = _first(
            admissible,
            lambda c: c.startswith(f"{verb} {object_name} ") and f" with {appliance} " in c,
        )
        if transform:
            return transform, f"apply {verb!r} transformation using {appliance!r}", True
        if last_action != "look" and "look" in admissible:
            return "look", "waiting for the transformation command to become admissible", False
        return None, "no admissible transformation command", False

    if step_name == "find_and_use_appliance":
        use = _first(admissible, lambda c: c.startswith(f"use {appliance} "))
        if use:
            return use, f"use the bound appliance {appliance!r}", True
        open_cmd = _first(admissible, lambda c: c.startswith("open "))
        if open_cmd:
            return open_cmd, "open a closed container while looking for the appliance", False
        go = _next_unvisited(admissible, visited)
        if go:
            return go, "explore an unvisited receptacle for the appliance", False
        if last_action != "look" and "look" in admissible:
            return "look", "re-observe the current location", False
        return None, "no appliance reachable", False

    return None, f"unknown plan step {step_name!r}", False


def _first(commands: List[str], predicate) -> Optional[str]:
    for command in commands:
        if predicate(command):
            return command
    return None


def _next_unvisited(admissible: List[str], visited: List[str]) -> Optional[str]:
    candidates = [
        command
        for command in admissible
        if command.startswith("go to ") and command[len("go to "):] not in visited
    ]
    if not candidates:
        return None
    return min(candidates, key=_receptacle_priority)


def _unbatch_info(infos: Dict[str, Any]) -> Dict[str, Any]:
    return {
        key: value[0] if isinstance(value, list) and len(value) == 1 else value
        for key, value in infos.items()
    }


def _validate_execution_input(execution_input: Dict[str, Any]) -> None:
    required = (
        "selected_skill_ids",
        "selected_scores",
        "selected_native_skills",
        "flat_skill_context",
    )
    missing = [field for field in required if field not in execution_input]
    if missing:
        raise ValueError(f"Execution input is missing fields: {', '.join(missing)}")
