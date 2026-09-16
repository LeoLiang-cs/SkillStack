# Reproducibility and claim boundaries

SkillStack separates four kinds of evidence:

1. **Implementation:** code and unit tests show that a path exists.
2. **Compatibility/acceptance:** a fixture, package install, or adapter round
   trip shows that a specified boundary executes.
3. **Measured performance:** a frozen task set, model/provider, budget, seed,
   and raw trace support a task result.
4. **Paper reproduction:** source-faithful code, data, settings, and provenance
   support a reproduction claim.

Passing an earlier category does not imply the next one.

## Fidelity

Every external method should carry a declared fidelity label and source/commit
where available. `paper_faithful`, `source_variant`, `reconstructed`,
`paper_inspired`, `blocked`, and `not_applicable_local` are different claims.
Provider substitution can test a harness boundary, but it cannot be described
as a faithful reproduction of the original model or service.

## Freeze before measuring

Before a task-performance run, record:

- task IDs, split, and input/data hashes;
- component IDs, versions, source repositories, commits, and fidelity;
- effective model/provider ID and prompt hash;
- decoding parameters, budget, timeout/retry policy, and seed scope;
- oracle usage and any controlled fixture or adapter behavior.

The run manifest and raw episode trace are the evidence source. Keep failures,
timeouts, invalid inputs, abstentions, and cancellations. A summary must not
turn missing or unknown values into successful or failed task outcomes.

The maintained core entrypoints are the package CLI, writer, adapter, and
offline fixture path. `scripts/run_w*.py`, provider probes, and external
benchmark launchers remain historical or experiment-specific entrypoints;
they are not silently promoted to stable installed-package commands.

## BLM boundary

Boundary Load Mapping (BLM) remains a proposed measurement method. The current
alpha harness provides trace plumbing and a controlled D→C composability demo;
it does not implement saved-state replay, atom probing, load-bearing recovery,
or a validated BLM result. BLM calibration and formal evidence are G2/G4 work,
not G1 package evidence.

## Reporting

Reports should state the exact command, environment, pass/fail/skip count,
artifact or lock hash, and whether the result is local, hosted, historical, or
not run. Do not replace a missing provider, benchmark, or platform result with a
different environment's success. Link the report and retained trace/fixture
when making a research claim.
