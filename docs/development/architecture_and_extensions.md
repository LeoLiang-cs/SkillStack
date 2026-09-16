# Architecture and extensions

SkillStack is a small experimental harness, not a general agent framework.
The stable core path is intentionally narrow:

```text
task + observation
        │
     Retriever ── native retrieval response ──┐
                                                ▼
       explicit retrieval → execution Adapter
                                                │
                                      Executor / fixture environment
                                                │
                                      append-only trace + summary
```

## Responsibility coordinates

R–A–D–C–L are responsibility coordinates, not five mandatory packages or a
fixed execution order:

- **R — Representation:** what a skill stores and how it is described;
- **A — Acquisition/Evolution:** how candidates are proposed or updated;
- **D — Discovery/Selection:** how a task selects candidate skills;
- **C — Composition/Execution:** how selected skills become executable input;
- **L — Lifecycle Management:** evaluation, admission, versioning, rollback,
  and retirement.

The public zero-model demo freezes a D→C boundary. It does not claim that all
R–A–D–C–L responsibilities are interchangeable or that the proposed BLM
measurement method is implemented.

## Adding a component

Use the smallest explicit interface that the neighboring component already
needs. Preserve the component's native payload and record adapter events for
fields that are read, generated, dropped, approximated, or defaulted. A new
adapter must declare its external source and fidelity label; compatibility is
not the same as source-faithful reproduction.

For a new retriever or executor:

1. add a focused implementation under the corresponding `src/skillstack/`
   package;
2. add a deterministic fixture or round-trip test with no provider call;
3. run the shared demo/trace path where possible;
4. update provenance and the claim-bounded report if an external method is
   involved;
5. document unsupported semantics instead of silently defaulting them.

Do not add a new abstraction layer merely to mirror the R–A–D–C–L vocabulary.
The writer, adapter, retriever, executor, and fixture environment are the
current minimal extension points.

## Trace and schema rules

The core schemas are exported from `skillstack.tracing`:

- `skillstack-run-manifest-v1`;
- `skillstack-episode-trace-v1`;
- `skillstack-run-summary-v1`.

Schema changes require a versioned migration or an explicitly new schema name.
Do not mutate checked-in expected fingerprints without reviewing the complete
trace change. Keep raw evidence append-only and make derived summaries
recomputable.

## Verification before a pull request

Run the commands listed in [`CONTRIBUTING.md`](../../CONTRIBUTING.md). Changes
to paths, configuration, schemas, adapters, or claims should include the
smallest relevant fixture and explain what the test does not establish.
