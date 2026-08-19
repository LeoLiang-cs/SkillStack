"""Prompt-based ReAct executor: full Thought/Action alternation via an LLM.

Phase 2C executor-slot swap. This is SkillStack's own zero-shot ReAct
implementation (prompt frozen in `configs/p0_react_prompt.txt`), not a
faithful reproduction of the ReAct paper's few-shot setup. It consumes the
same execution_input shape as the deterministic executors, so the runner,
adapter, retrievers, and trace format are unchanged.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from skillstack.llm import BackendConfig, LlmClient, LlmError

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PROMPT_PATH = REPOSITORY_ROOT / "configs" / "p0_react_prompt.txt"

ACTION_PATTERN = re.compile(r"^\s*Action:\s*(.+?)\s*$", re.MULTILINE)
THOUGHT_PATTERN = re.compile(r"^\s*Thought:\s*(.+?)\s*$", re.MULTILINE)
DONE_ACTION = "done"


def parse_reasoning_action(content: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract the final Thought and Action lines from a model reply."""

    thoughts = THOUGHT_PATTERN.findall(content)
    actions = ACTION_PATTERN.findall(content)
    thought = thoughts[-1].strip() if thoughts else None
    action = actions[-1].strip() if actions else None
    return thought, action


class ReActExecutor:
    """Run a full ReAct loop against the LLM backend for one episode."""

    name = "react_executor"

    def __init__(
        self,
        client: LlmClient,
        prompt_path: Optional[Path] = None,
        max_tokens_per_step: Optional[int] = None,
        structured_skills: bool = False,
    ) -> None:
        self.client = client
        self.prompt_path = (prompt_path or DEFAULT_PROMPT_PATH).resolve()
        self.prompt_template = self.prompt_path.read_text(encoding="utf-8")
        self.max_tokens_per_step = max_tokens_per_step
        self.structured_skills = structured_skills

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
        if task_record is None:
            raise ValueError("ReActExecutor requires the episode task record.")
        max_steps = max_steps if max_steps is not None else 50
        skill_context = execution_input.get("flat_skill_context") or "(none provided)"
        system_message = self.prompt_template.replace("{skill_context}", skill_context)
        system_message = (
            f"Task: {task_record['task_instruction']}\n\n" + system_message
        )

        grounded_steps: List[str] = []
        if self.structured_skills:
            grounded_steps = extract_procedure_steps(execution_input)
            if grounded_steps:
                steps_block = "\n".join(
                    f"{index}. {step}" for index, step in enumerate(grounded_steps, start=1)
                )
                system_message += (
                    "\n\nThe selected skill lists numbered steps; follow them in order:\n"
                    + steps_block
                )

        messages: List[Dict[str, str]] = [{"role": "system", "content": system_message}]
        current_info = initial_info
        observations = [initial_observation]
        actions: List[str] = []
        rationales: List[Dict[str, Any]] = []
        llm_calls: List[Dict[str, Any]] = []
        rewards: List[float] = []
        warnings: List[str] = []
        success = False
        stop_reason = "max_steps_exhausted"

        messages.append(
            {
                "role": "user",
                "content": _observation_message(initial_observation, current_info),
            }
        )

        while len(actions) < max_steps:
            admissible = list(current_info.get("admissible_commands", []))
            action: Optional[str] = None
            thought: Optional[str] = None

            for attempt in (1, 2):
                try:
                    response = self.client.chat(
                        messages, max_tokens=self.max_tokens_per_step
                    )
                except LlmError as error:
                    stop_reason = "llm_error"
                    warnings.append(str(error))
                    action = None
                    break

                usage = response["usage"]
                call_record = {
                    "step_index": len(actions) + 1,
                    "attempt": attempt,
                    "model": self.client.backend.model,
                    "backend": self.client.backend.name,
                    "usage": usage,
                    "cost_estimate_usd": round(self.client.estimate_cost_usd(usage), 6),
                    "latency_seconds": response["latency_seconds"],
                }
                llm_calls.append(call_record)

                thought, action = parse_reasoning_action(response["content"])
                if action is not None and (action == DONE_ACTION or action in admissible):
                    break
                if action is None:
                    feedback = (
                        "Your last reply had no 'Action:' line. Reply in exactly this "
                        "format:\nThought: <one short sentence>\nAction: <one admissible "
                        "command, verbatim>"
                    )
                else:
                    feedback = (
                        f"Invalid action {action!r}. Choose exactly one command verbatim "
                        f"from the admissible commands list, or reply 'Action: done'."
                    )
                feedback += "\n\nAdmissible commands:\n" + "\n".join(
                    f"- {command}" for command in admissible
                )
                messages.append({"role": "assistant", "content": response["content"]})
                messages.append({"role": "user", "content": feedback})
                warnings.append(
                    f"Step {len(actions) + 1} attempt {attempt}: {feedback}"
                )

            if stop_reason == "llm_error":
                break

            if action is None or (action != DONE_ACTION and action not in admissible):
                stop_reason = "invalid_action_retries_exhausted"
                warnings.append(f"Step {len(actions) + 1}: no valid action after retry.")
                break

            if action == DONE_ACTION:
                stop_reason = "agent_declared_done"
                break

            next_observations, scores, dones, next_infos = env.step([action])
            actions.append(action)
            observations.append(next_observations[0])
            rewards.append(float(scores[0]))
            current_info = _unbatch_info(next_infos)
            messages.append({"role": "assistant", "content": f"Thought: {thought or ''}\nAction: {action}"})
            messages.append(
                {
                    "role": "user",
                    "content": _observation_message(next_observations[0], current_info),
                }
            )
            rationales.append(
                {
                    "step_index": len(actions),
                    "skill_id": execution_input.get("selected_skill_ids", [None])[0] if execution_input.get("selected_skill_ids") else None,
                    "thought": thought,
                    "chosen_action": action,
                    "reason": "model-selected admissible action (ReAct)",
                    "grounded_step": _ground_action_step(action, grounded_steps),
                }
            )

            if dones[0]:
                success = bool(scores[0] > 0)
                stop_reason = "environment_done"
                break

        return {
            "executor_name": self.name,
            "action_source": "react_llm_policy",
            "executor_notes": (
                "Zero-shot ReAct with strict Thought/Action format. Native thinking "
                "mode disabled on the backend. Prompt frozen in "
                f"{self.prompt_path.relative_to(REPOSITORY_ROOT)}."
            ),
            "backend": self.client.backend.name,
            "model": self.client.backend.model,
            "system_prompt": system_message,
            "skill_context_source": "flat_skill_context",
            "structured_skills": self.structured_skills,
            "grounded_steps": grounded_steps,
            "actions": actions,
            "observations": observations,
            "action_rationales": rationales,
            "llm_calls": llm_calls,
            "total_cost_estimate_usd": round(
                sum(call["cost_estimate_usd"] for call in llm_calls), 6
            ),
            "rewards": rewards,
            "success": success,
            "stop_reason": stop_reason,
            "warnings": warnings,
        }


def _observation_message(observation: str, info: Dict[str, Any]) -> str:
    admissible = list(info.get("admissible_commands", []))
    lines = [f"Observation:\n{observation}", "\nAdmissible commands:"]
    lines.extend(f"- {command}" for command in admissible)
    return "\n".join(lines)


PROCEDURE_SECTION_PATTERN = re.compile(r"## Procedure\s*\n(.*?)(?=\n## |\Z)", re.DOTALL)
NUMBERED_STEP_PATTERN = re.compile(r"^\s*(\d+)\.\s+(.+)$", re.MULTILINE)

# action-leading-verb → step keywords, for lightweight grounding.
GROUND_KEYWORDS = {
    "go": ("go", "navigate", "explore"),
    "take": ("take", "pick", "grab"),
    "move": ("move", "place", "put"),
    "open": ("open",),
    "close": ("close",),
    "clean": ("clean", "wash", "rinse"),
    "heat": ("heat", "microwave", "warm"),
    "cool": ("cool", "fridge", "chill"),
    "use": ("use", "toggle", "lamp", "light", "examine"),
    "examine": ("examine",),
    "look": ("look", "observe"),
}


def extract_procedure_steps(execution_input: Dict[str, Any]) -> List[str]:
    """Return the numbered Procedure steps of the top selected skill."""

    native_payloads = execution_input.get("selected_native_skills") or []
    if not native_payloads:
        return []
    section_match = PROCEDURE_SECTION_PATTERN.search(native_payloads[0])
    if not section_match:
        return []
    steps = [
        match.group(2).strip()
        for match in NUMBERED_STEP_PATTERN.finditer(section_match.group(1))
    ]
    return steps


def _ground_action_step(action: str, steps: List[str]) -> Optional[int]:
    """Lightweight map: which numbered skill step this action implements."""

    if not steps:
        return None
    leading_verb = action.split(" ")[0] if action else ""
    keywords = GROUND_KEYWORDS.get(leading_verb, (leading_verb,))
    for index, step in enumerate(steps, start=1):
        step_lower = step.lower()
        if any(keyword in step_lower for keyword in keywords):
            return index
    return None


def _unbatch_info(infos: Dict[str, Any]) -> Dict[str, Any]:
    return {
        key: value[0] if isinstance(value, list) and len(value) == 1 else value
        for key, value in infos.items()
    }
