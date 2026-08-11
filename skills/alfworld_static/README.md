# ALFWorld Static Skill Library v0

This directory contains six hand-authored **native text artifacts** for the
P0.0 vertical slice. Each artifact is intended to be read as ordinary skill
documentation by a retriever or executor. The headings are library-local
conventions, not a proposed Canonical Skill Interface.

The six files cover ALFWorld's supported task families:

| Skill artifact | ALFWorld task family |
|---|---|
| `skill_pick_and_place.md` | `pick_and_place_simple` |
| `skill_light_inspection.md` | `look_at_obj_in_light` |
| `skill_clean_then_place.md` | `pick_clean_then_place_in_recep` |
| `skill_heat_then_place.md` | `pick_heat_then_place_in_recep` |
| `skill_cool_then_place.md` | `pick_cool_then_place_in_recep` |
| `skill_pick_two_then_place.md` | `pick_two_obj_and_place` |

## Provenance and limits

- **Author:** SkillStack P0.0 harness authors.
- **Evidence:** ALFWorld task semantics and inspected task trajectories.
- **Representation:** human-readable natural-language procedures plus
  task-family labels.
- **Not included:** executable code, formal preconditions/effects, a state
  schema, or guarantees that the described action is currently applicable.

Those omissions are intentional: P0.0 should reveal when downstream
components have to invent such information.

