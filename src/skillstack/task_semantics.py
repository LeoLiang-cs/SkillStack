"""Shared task-semantics parsing for the six ALFWorld task families.

Single source of truth for extracting structured fields from a task record
and the environment's task sentence. Used by the deterministic skill-plan
executor (binding) and by the task-semantic retriever (R1). The extracted
fields are the raw evidence for Canonical Interface induction.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

TASK_LINE_PATTERN = re.compile(r"Your task is to:\s*(.+)")

FAMILY_OBJECT_PATTERNS: Dict[str, re.Pattern] = {
    "look_at_obj_in_light": re.compile(r"examine\s+(?:the\s+|a\s+|an\s+|some\s+)?([a-z]+)"),
    "pick_and_place_simple": re.compile(r"(?:put|place|move)\s+(?:the\s+|a\s+|an\s+|some\s+)?([a-z]+)"),
    "pick_clean_then_place_in_recep": re.compile(r"clean\s+(?:the\s+|a\s+|an\s+|some\s+)?([a-z]+)"),
    "pick_heat_then_place_in_recep": re.compile(r"heat\s+(?:the\s+|a\s+|an\s+|some\s+)?([a-z]+)"),
    "pick_cool_then_place_in_recep": re.compile(
        r"(?:put|cool)\s+(?:the\s+|a\s+|an\s+|some\s+)?(?:cool\s+|cold\s+)?([a-z]+)"
    ),
    "pick_two_obj_and_place": re.compile(
        r"(?:put|place|move|transfer)\s+(?:the\s+|a\s+|an\s+|some\s+)?(?:two\s+|both\s+)?([a-z]+)"
    ),
}
DEST_PATTERN = re.compile(r"(?:in|on|to|into)\s+(?:(?:the|a|an)\s+)?([a-z]+)")
APPLIANCE_PATTERN = re.compile(r"with\s+(?:the\s+)?([a-z]+)")
GENERIC_OBJECT_PATTERN = re.compile(r"(?:the\s+|a\s+|an\s+|some\s+)([a-z ]+?)\s+(?:in|on|with)\s")

ADJECTIVES = {
    "cold", "cooked", "cool", "clean", "dirty", "green", "hot", "red", "sliced",
    "washed", "warm",
}
NOUN_FILLERS = {"away", "back", "both", "it", "them", "there"}

# Fallback synonyms for human-instruction wording that differs from the
# environment's own vocabulary.
SYNONYMS: Dict[str, str] = {
    "clock": "alarmclock",
    "counter": "countertop",
    "lamp": "desklamp",
}

APPLIANCE_BY_SKILL: Dict[str, str] = {
    "skill_clean_then_place": "sinkbasin",
    "skill_heat_then_place": "microwave",
    "skill_cool_then_place": "fridge",
    "skill_light_inspection": "desklamp",
}

TRANSFORM_VERB_BY_SKILL: Dict[str, str] = {
    "skill_clean_then_place": "clean",
    "skill_heat_then_place": "heat",
    "skill_cool_then_place": "cool",
}

# Task-family → operation label used by the task-semantic retriever.
OPERATION_BY_FAMILY: Dict[str, str] = {
    "look_at_obj_in_light": "inspect",
    "pick_and_place_simple": "place",
    "pick_clean_then_place_in_recep": "clean_then_place",
    "pick_heat_then_place_in_recep": "heat_then_place",
    "pick_cool_then_place_in_recep": "cool_then_place",
    "pick_two_obj_and_place": "place_two",
}

# Task-family → transformation the skill must supply (None for pure place).
TRANSFORMATION_BY_FAMILY: Dict[str, Optional[str]] = {
    "look_at_obj_in_light": None,
    "pick_and_place_simple": None,
    "pick_clean_then_place_in_recep": "clean",
    "pick_heat_then_place_in_recep": "heat",
    "pick_cool_then_place_in_recep": "cool",
    "pick_two_obj_and_place": None,
}

# Task-family → required appliance for applicability checks.
APPLIANCE_BY_FAMILY: Dict[str, Optional[str]] = {
    "look_at_obj_in_light": "desklamp",
    "pick_and_place_simple": None,
    "pick_clean_then_place_in_recep": "sinkbasin",
    "pick_heat_then_place_in_recep": "microwave",
    "pick_cool_then_place_in_recep": "fridge",
    "pick_two_obj_and_place": None,
}


def parse_task_semantics(
    task_record: Dict[str, Any],
    initial_observation: str,
    task_instruction: Optional[str] = None,
) -> Dict[str, Any]:
    """Extract structured task semantics for one episode.

    Returns object, destination, appliance, goal_operation,
    required_transformation, the task line used, and warnings. ``object`` is
    a single noun (for pick_two this is the first named object; a fuller
    object list is future work).
    """

    warnings: list = []
    match = TASK_LINE_PATTERN.search(initial_observation)
    task_line = (
        match.group(1).strip().rstrip(".")
        if match
        else (task_instruction or task_record["task_instruction"])
    )
    task_line = task_line.strip().rstrip(".").lower()
    task_family = task_record["task_family"]

    object_name: Optional[str] = None
    destination: Optional[str] = None
    appliance: Optional[str] = None

    pattern = FAMILY_OBJECT_PATTERNS.get(task_family)
    if pattern:
        obj_match = pattern.search(task_line)
        if obj_match:
            object_name = _strip_fillers(obj_match.group(1))
    if object_name is None:
        object_name = _generic_object(task_line)

    dest_match = DEST_PATTERN.search(task_line)
    if dest_match:
        destination = dest_match.group(1)

    appliance_match = APPLIANCE_PATTERN.search(task_line)
    if appliance_match:
        appliance = appliance_match.group(1)
    elif task_family == "look_at_obj_in_light":
        appliance = APPLIANCE_BY_SKILL.get("skill_light_inspection")

    object_name = SYNONYMS.get(object_name, object_name)
    destination = SYNONYMS.get(destination, destination)
    appliance = SYNONYMS.get(appliance, appliance)

    if object_name is None:
        warnings.append("Could not bind an object name from the task text.")
    if task_family != "look_at_obj_in_light" and destination is None:
        warnings.append("Could not bind a destination name from the task text.")
    if task_family == "look_at_obj_in_light" and appliance is None:
        warnings.append("Could not bind an appliance name from the task text.")

    return {
        "object": object_name,
        "destination": destination,
        "appliance": appliance,
        "goal_operation": OPERATION_BY_FAMILY.get(task_family, "unknown"),
        "required_transformation": TRANSFORMATION_BY_FAMILY.get(task_family),
        "task_family": task_family,
        "task_line_used": task_line,
        "warnings": warnings,
    }


def required_appliance_for_family(task_family: str) -> Optional[str]:
    return APPLIANCE_BY_FAMILY.get(task_family)


def _strip_fillers(raw: str) -> Optional[str]:
    tokens = raw.split()
    meaningful = [token for token in tokens if token not in ADJECTIVES and token not in NOUN_FILLERS]
    candidate = meaningful[-1] if meaningful else (tokens[-1] if tokens else None)
    if candidate and candidate.endswith("s") and len(candidate) > 3 and not candidate.endswith("ss"):
        return candidate[:-1]
    return candidate


def _generic_object(task_line: str) -> Optional[str]:
    match = GENERIC_OBJECT_PATTERN.search(task_line)
    if not match:
        return None
    return _strip_fillers(match.group(1))
