# P0.0 Runtime Contracts

These are small, execution-time boundary conventions for the P0.0 harness.
They make the runner observable and swappable; they are **not** SkillStack's
Canonical Skill Interface and do not prescribe how another method represents a
skill internally.

## Task record

Every selected task supplies:

```json
{
  "task_id": "stable manifest identifier",
  "task_family": "ALFWorld task-type label",
  "task_instruction": "human task text",
  "game_file": "relative game.tw-pddl path"
}
```

## Native skill artifact

The loader preserves each library artifact as:

```json
{
  "skill_id": "library-local stable identifier",
  "source_path": "repository-relative Markdown path",
  "native_payload": "complete unmodified Markdown text",
  "local_metadata": {"task_family": "library-local label"}
}
```

`local_metadata` is extracted from this static library's own Markdown
convention. A future method may expose no such label or may use a different
native payload.

## Retrieval request and response

Retriever input contains a task record, the current raw observation, the
complete native skill list, and `top_k`. Its output records the implementation
name, ranked candidates, raw implementation output, and warnings.

Each ranked candidate retains `skill_id`, `score`, and the complete
`native_payload`. A score need not be calibrated across retrieval methods.

## Adapter event

The retrieval-to-execution adapter records one event per conversion:

```json
{
  "component": "retrieval_to_execution_adapter",
  "read": [],
  "generated": [],
  "dropped": [],
  "approximated": [],
  "defaulted": [],
  "warnings": []
}
```

This is the source of the adapter-friction ledger. In P0.0, the adapter must
not silently infer formal preconditions, effects, or graph dependencies.

## Executor report and episode trace

Executor output records the action sequence, raw observations, rewards,
success status, stop reason, and warnings. The resulting episode trace also
stores the effective configuration, environment version, selected native
skills, retriever raw output, adapter events, seed, and timestamp.

Every failure remains a trace. `indeterminate` is an allowed failure label.

