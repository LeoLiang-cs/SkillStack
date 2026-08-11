# Pick and place an object

**Task family:** `pick_and_place_simple`

## Purpose

Move one named object to one named destination receptacle.

## Procedure

1. Read the task to identify the object and destination exactly; preserve
   qualifiers such as colour, slicing state, or the requested receptacle.
2. Explore the scene until the object is visible. Open a closed container only
   when it may contain the object.
3. Navigate to the object and take it.
4. Navigate to the named destination. Open the destination if it is a closed
   container.
5. Put the object in or on the destination as the environment permits.
6. Use task feedback to confirm completion before adding unnecessary actions.

## When to use

Use for instructions of the form “put/place/move `<object>` in/on
`<receptacle>`” when no cleaning, heating, cooling, lighting, or second object
is required.

## Common failure modes

- The correct object is inside a closed container that has not been opened.
- The destination is closed, so placing fails until it is opened.
- A semantically similar object or receptacle is selected instead of the one
  named in the instruction.
- The object is placed before the requested transformation in a compound task.

