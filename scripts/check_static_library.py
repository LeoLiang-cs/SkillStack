"""Check that the P0.0 static ALFWorld library is complete and readable."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "skills" / "alfworld_static"
EXPECTED_SKILLS = {
    "skill_pick_and_place.md": "pick_and_place_simple",
    "skill_light_inspection.md": "look_at_obj_in_light",
    "skill_clean_then_place.md": "pick_clean_then_place_in_recep",
    "skill_heat_then_place.md": "pick_heat_then_place_in_recep",
    "skill_cool_then_place.md": "pick_cool_then_place_in_recep",
    "skill_pick_two_then_place.md": "pick_two_obj_and_place",
}
REQUIRED_HEADINGS = ("## Purpose", "## Procedure", "## When to use", "## Common failure modes")


def main() -> int:
    errors = []
    for filename, task_family in EXPECTED_SKILLS.items():
        path = LIBRARY / filename
        if not path.exists():
            errors.append(f"Missing skill artifact: {filename}")
            continue
        text = path.read_text(encoding="utf-8")
        if f"`{task_family}`" not in text:
            errors.append(f"{filename} does not declare {task_family}")
        for heading in REQUIRED_HEADINGS:
            if heading not in text:
                errors.append(f"{filename} is missing {heading}")

    actual = set(LIBRARY.glob("skill_*.md"))
    if len(actual) != len(EXPECTED_SKILLS):
        errors.append(f"Expected {len(EXPECTED_SKILLS)} skill files, found {len(actual)}")

    if errors:
        print("Static library check failed:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print(f"Static library check passed: {len(EXPECTED_SKILLS)} skill artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

