# Pick two objects and place both

**Task family:** `pick_two_obj_and_place`

## Purpose

Deliver two named objects to the same requested destination.

## Procedure

1. Extract both object identities and the common destination from the task.
2. Locate the first object, take it, and place it at the destination.
3. Locate the second object, take it, and place it at the same destination.
4. Open source or destination containers whenever access requires it.
5. Verify that both objects, not merely one, satisfy the destination condition.

## When to use

Use when the task names two distinct objects that must both end up in one
receptacle or location.

## Common failure modes

- Only the first object is delivered.
- Both objects are confused because they have similar names or appearances.
- The agent assumes it can carry two objects at once when the current state
  does not permit it.
- The destination is closed or cannot accept the selected placement action.

