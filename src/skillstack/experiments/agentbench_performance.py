"""Pure helpers for the strict-disjoint AgentBench performance experiment."""

from __future__ import annotations

import json
import os
import re
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Mapping


def execution_budget(candidate_cap: int = 3, cell_count: int = 2) -> Dict[str, Any]:
    """Return task-episode counts without pretending episodes equal model calls."""

    if candidate_cap < 1 or cell_count < 1:
        raise ValueError("candidate_cap and cell_count must be positive")
    initial_history = 13
    initial_proposal = 13
    per_candidate = 13 + 13  # fresh unchanged baseline + candidate probe
    per_cell = candidate_cap * per_candidate
    return {
        "shared_initial_history_probe_episodes": initial_history,
        "shared_initial_proposal_episodes": initial_proposal,
        "shared_initial_total_episodes": initial_history + initial_proposal,
        "fresh_probe_episodes_per_candidate": per_candidate,
        "maximum_candidates_per_cell": candidate_cap,
        "maximum_probe_episodes_per_cell": per_cell,
        "cell_count": cell_count,
        "maximum_total_task_episodes": initial_history + initial_proposal + cell_count * per_cell,
        "model_call_count": "variable: every ALFWorld episode contains multiple agent turns",
        "proposal_calls": {
            "a0": "up to 3 stages: classify, diagnose, propose",
            "a1": "1 SkillRL prompt call",
        },
    }


def with_effectiveness_sensitivity(gate: Mapping[str, Any]) -> Dict[str, Any]:
    """Add the actual-fix sensitivity without changing the released gate result."""

    result = deepcopy(dict(gate))
    native_admitted = result.get("decision") == "accepted"
    actual_fixes = int(result.get("fixes", 0))
    result["native_admitted"] = native_admitted
    result["effectiveness_admitted"] = native_admitted and actual_fixes > 0
    result["effectiveness_rule"] = "native_admitted AND fixes > 0"
    if native_admitted and actual_fixes == 0:
        result["sensitivity_disagreement"] = "native_accepts_without_observed_fix"
    else:
        result["sensitivity_disagreement"] = None
    return result


def atomic_write_json(path: Path, payload: Any) -> None:
    """Atomically replace one checkpoint so interrupted runs remain resumable."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
    ) as handle:
        json.dump(json_safe(payload), handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def read_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def checkpoint_name(task_id: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_.-]+", "-", str(task_id)).strip("-.")
    return normalized or "task"


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item) for item in value]
    if hasattr(value, "value"):
        return json_safe(value.value)
    if hasattr(value, "model_dump"):
        return json_safe(value.model_dump(mode="json"))
    if hasattr(value, "dict"):
        return json_safe(value.dict())
    if hasattr(value, "__dict__"):
        return json_safe(vars(value))
    return repr(value)


def sanitize_tool_history(messages: list) -> tuple:
    """Drop only orphaned tool messages created by upstream history truncation."""

    sanitized = []
    events = []
    outstanding_tool_call_ids = set()
    for index, raw_message in enumerate(messages):
        message = json_safe(raw_message)
        role = message.get("role")
        if role == "assistant":
            outstanding_tool_call_ids = {
                str(call.get("id"))
                for call in message.get("tool_calls") or []
                if call.get("id")
            }
            sanitized.append(message)
            continue
        if role == "tool":
            tool_call_id = str(message.get("tool_call_id") or "")
            if tool_call_id and tool_call_id in outstanding_tool_call_ids:
                sanitized.append(message)
                outstanding_tool_call_ids.remove(tool_call_id)
            else:
                events.append({
                    "message_index": index,
                    "role": "tool",
                    "tool_call_id": tool_call_id or None,
                    "action": "dropped_orphan_tool_message",
                    "reason": "no_preceding_assistant_tool_call_in_visible_history",
                })
            continue
        outstanding_tool_call_ids = set()
        sanitized.append(message)
    return sanitized, events
