# SkillStack documentation

This directory separates historical design material from current research
candidates and release documentation.

## Directory map

| Path | Purpose | Status |
|---|---|---|
| `plan/` | Cross-week project roadmap, execution backlog, gate plans and historical plan versions | Current planning source of truth |
| `original/` | Original SkillStack framework, runtime contracts and Canonical Interface draft | Historical reference |
| `final_cards/` | Boundary Load Maps (BLM) idea cards produced by the idea-spark run | Private/held research candidate; excluded from the public alpha snapshot |
| `open_source/` | Public-release scope, provenance and publication audit | Maintained during release preparation |
| `open_source/SUPPORT_MATRIX.md` | Maintained vs historical Python/platform boundaries | G1 Batch 1 |
| `user/` | Install, configuration, run recovery and troubleshooting guides | G1 O06 |
| `development/` | Architecture and extension guidance | G1 O06 |
| `research/` | Reproducibility and claim-boundary guidance | G1 O06 |
| `../examples/demo/` | Deterministic zero-model demo fixtures and expected output | Public runtime validation |
| `../reports/` | Experiment plans, summaries and evidence audits | Evidence is claim-bounded |

The original framework and the BLM candidate are related but not equivalent.
SkillStack is the executable component-composability harness. BLM is a proposed
measurement method that still requires a feasibility spike and does not yet
constitute a validated interface-completeness result.

## Reading order

1. Start with the repository [README](../README.md) for installation and the
   current implementation boundary.
2. Read the historical framework in `original/` to understand R-A-D-C-L and
   the implementation-first, schema-later decisions.
3. Read [`plan/`](plan/README.md) for the current cross-week roadmap, gate order,
   and execution status.
4. Read the reports for completed evidence and limitations.
5. If you have access to the held `final_cards/`, read them only as a research
   proposal; do not infer that replay or atom-probing machinery is already
   present in `src/`.

## Status vocabulary

- **Implemented**: available in the repository and covered by a test or
  reproducible command.
- **Evidence-backed**: supported by a committed report and retained trace or
  fixture.
- **Adapted/provider-substituted**: useful compatibility evidence, but not a
  source-faithful reproduction.
- **Proposed**: design material that has not passed its executable feasibility
  gate.
