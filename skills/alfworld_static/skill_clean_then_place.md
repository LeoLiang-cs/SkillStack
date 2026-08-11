# Clean an object, then place it

**Task family:** `pick_clean_then_place_in_recep`

## Purpose

Clean one named object with a sink basin before placing it at its destination.

## Procedure

1. Identify the object, sink basin, and destination from the task.
2. Locate and take the object; open its current container if necessary.
3. Locate the sink basin and apply the environment's cleaning action to the
   object.
4. Confirm that cleaning succeeded from the observation or task feedback.
5. Navigate to the destination, open it if needed, and place the cleaned
   object there.

## When to use

Use when the instruction explicitly requires cleaning, washing, or rinsing an
object before it is put in/on a receptacle.

## Common failure modes

- The object is placed at the destination before being cleaned.
- A generic “use sink” action is attempted without holding or targeting the
  requested object.
- The sink basin or destination is confused with another nearby receptacle.
- The agent continues after a failed cleaning action instead of re-checking the
  object's state.

