# Cool an object, then place it

**Task family:** `pick_cool_then_place_in_recep`

## Purpose

Cool one named object in a fridge before placing it at its destination.

## Procedure

1. Identify the object, fridge, and destination.
2. Locate and take the object; open a container if it blocks access.
3. Navigate to the fridge and open it.
4. Put the object in the fridge and invoke the environment's cooling action.
5. Take the cooled object back out of the fridge.
6. Navigate to the destination, open it if necessary, and place the cooled
   object there.

## When to use

Use when the instruction explicitly requires cooling, chilling, or putting an
object in a fridge before final placement.

## Common failure modes

- The object is put in the fridge but no cooling action is issued.
- The agent tries to cool an object that it has not placed in the fridge.
- The cooled object is left in the fridge rather than delivered.
- The target receptacle is confused with the fridge, causing premature success
  assumptions.

