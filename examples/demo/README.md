# Zero-model composability demo

This fixture is the smallest public demonstration of the SkillStack runtime
boundary. It runs one fixed task through two retriever cells, the same
retrieval-to-execution adapter, the same recorded-action executor, and a
deterministic local environment.

From the repository root:

```bash
uv sync
uv run skillstack demo
```

The command creates two immutable run directories under `runs/demo/`. Each
contains `run_manifest.json`, append-only `episodes.jsonl`, and `summary.json`.
The command also checks a stable fingerprint that excludes timestamps, host
details, run IDs, and output paths.
The checked-in `expected_summary.json` makes the intended cell comparison
reviewable without opening a generated run.

The `c0_no_skill` cell selects no native skills. The `c1_debug_lexical` cell
uses the transparent lexical retriever and should select the lamp-inspection
artifact. Both cells use the same fixture action (`look`) and should complete
the fixture. This demonstrates component interchangeability and trace
plumbing; it is not an ALFWorld result, an agent-policy comparison, or a
benchmark-success claim.

To run one cell or write elsewhere:

```bash
uv run skillstack demo --configuration c1_debug_lexical --output-root /tmp/skillstack-demo
```
