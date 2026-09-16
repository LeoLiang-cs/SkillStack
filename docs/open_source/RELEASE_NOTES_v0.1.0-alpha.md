# SkillStack v0.1.0-alpha release notes

Status: release candidate documentation; MIT licensed; no tag has been created.

G1 Batch 1 note (2026-09-16): the maintained core target is now Python
3.11/3.12 on Linux/macOS. The older 3.9/3.10 statements below describe the
historical alpha draft and are not current maintained-support evidence; see
[`SUPPORT_MATRIX.md`](SUPPORT_MATRIX.md).

Target tag: `v0.1.0-alpha`

Package version: `0.1.0a0`

## Highlights

- Installable Python package and `skillstack` command-line entry point.
- Deterministic, zero-model Demo comparing two retriever cells through the
  same adapter, executor, and trace path.
- Repository preflight and public-file scanner for credentials, private paths,
  invalid JSON/YAML, broken local links, and text hygiene.
- Commit-based public snapshot check with a versioned scope policy, per-file
  SHA-256 manifest, dirty-worktree isolation, and source/wheel/sdist checks.
- Maintained-support CI configuration for Python 3.11/3.12 on Linux/macOS;
  Python 3.9/3.10 remains a historical reproduction boundary.

## Verified release-candidate checks

On 2026-09-15, a temporary candidate containing the G0 implementation completed:

- `uv sync --frozen`;
- `skillstack preflight`;
- `skillstack check-repo` with 238 files and zero findings;
- `skillstack demo` with no model calls;
- 112 unit tests (2 conditional skips in the fresh-clone environment);
- wheel and source-distribution builds.

The temporary candidate selected 244 source files. Its source, wheel, and
sdist manifests contained no forbidden or unsafe members. The current project
`HEAD` is intentionally rejected until the scope policy is present in the
selected commit.

The older 108-test Python 3.9/3.10 result is historical evidence for the alpha
draft, not a current maintained-support claim. G1 Batch 1 currently has local
Python 3.10 historical and Python 3.12 macOS evidence; hosted Linux/macOS
evidence and Python 3.11 remain pending.

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
- Commit the G0 implementation in a narrow project commit, then observe the
  first hosted CI run.
- Review the final tracked-file list before creating the tag.

## What this alpha provides

- A package and `skillstack` command-line entry point; the current maintained
  target is Python 3.11/3.12, while 3.9/3.10 is historical reproduction.
- Repository preflight and public-file checks that make no network or model
  calls.
- A deterministic composability demo exercising two retrievers through the
  same adapter, recorded-action executor, and trace writer.
- Modular experiment code and claim-bounded evidence through Week 5.
- Explicit provenance and fidelity labels for GRASP, SkillRL, and SkillOps
  integration cells.
- CI definitions for preflight, repository scanning, Demo, unit tests, and
  package build on the maintained target matrix (hosted result pending).

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
`f5733aedcfbf0303248df0ec97bffb28e911a2f6ad0a79bde678114ce0446838`.

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
