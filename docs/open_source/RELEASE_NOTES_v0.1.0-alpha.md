# SkillStack v0.1.0-alpha release notes

Status: release candidate documentation; MIT licensed; no tag has been created.

Target tag: `v0.1.0-alpha`

Package version: `0.1.0a0`

## Highlights

- Installable Python package and `skillstack` command-line entry point.
- Deterministic, zero-model Demo comparing two retriever cells through the
  same adapter, executor, and trace path.
- Repository preflight and public-file scanner for credentials, private paths,
  invalid JSON/YAML, broken local links, and text hygiene.
- Isolated 243-file public snapshot check that creates and clones a temporary
  Git repository before repeating installation, Demo, tests, and build.
- Python 3.9/3.10 CI, contributor guidance, structured issue/PR templates, and
  third-party provenance plus component-fidelity records.

## Verified release-candidate checks

On 2026-09-10, the isolated snapshot completed:

- `uv sync --frozen`;
- `skillstack preflight`;
- `skillstack check-repo` with 237 files and zero findings;
- `skillstack demo` with no model calls;
- 108 unit tests;
- wheel and source-distribution builds.

The same 108-test suite passed locally on Python 3.9 and 3.10, with one
conditional external-integration test skipped in each environment.

## Scope and limitations

- The release demonstrates a modular, traceable experimental harness; it does
  not establish universal component interchangeability or better task
  performance.
- External GRASP, SkillRL, SkillOps, AgentBench, and ALFWorld source/data are
  not bundled. Source-backed cells require separate checkouts and retain their
  recorded fidelity labels.
- BLM is a proposed research direction and its held cards are not included in
  the public alpha snapshot.
- Model/API experiments and complete paper reproductions are not part of the
  zero-model release gate.

## Remaining publication gates

- Decide the target venue's anonymity policy before publishing research cards.
- Push the candidate and observe the first hosted CI run.
- Review the final tracked-file list before creating the tag.

## What this alpha provides

- A Python 3.9/3.10 package and `skillstack` command-line entry point.
- Repository preflight and public-file checks that make no network or model
  calls.
- A deterministic composability demo exercising two retrievers through the
  same adapter, recorded-action executor, and trace writer.
- Modular experiment code and claim-bounded evidence through Week 5.
- Explicit provenance and fidelity labels for GRASP, SkillRL, and SkillOps
  integration cells.
- CI definitions for preflight, repository scanning, Demo, unit tests, and
  package build on Python 3.9 and 3.10.

## Reproduce the zero-model path

```bash
uv sync --frozen
uv run skillstack --version
uv run skillstack preflight
uv run skillstack check-repo
uv run skillstack demo
uv run python -m unittest discover -s tests -q
uv build
```

Expected Demo fingerprint:
`266c773e6beb483d91121de31ad65bd75c1eb673bcca4f3d30ed0f097089e0f2`.

## Evidence boundary

This release demonstrates a modular and traceable harness plus specific
compatibility experiments. It does not establish universal plug-and-play
interchangeability, full GRASP/SkillRL/SkillOps reproduction, benchmark
superiority, or implementation of the proposed Boundary Load Maps method.

External repositories, benchmark datasets, paper PDFs, generated runs, and
credentials are not included. ALFWorld and external-method paths remain
optional and require separately obtained dependencies or source checkouts.

## Known limitations and release gates

- The first hosted CI run cannot be verified until the candidate is pushed.
- BLM idea cards remain outside the public alpha snapshot pending target-venue
  and anonymity decisions.
- Some strict task-performance cells remain blocked by external services,
  credentials, or missing released artifacts; the reports preserve those
  boundaries.

## Upgrade note

This is the first named alpha. APIs, trace schemas, and configuration fields may
change before a stable release.
