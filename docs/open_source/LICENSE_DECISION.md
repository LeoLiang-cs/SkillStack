# SkillStack project license decision

Status: **MIT selected by the project owner on 2026-09-10.**

This record concerns SkillStack-authored code and documentation. Third-party
material keeps its own license and notice as documented in
[`THIRD_PARTY_PROVENANCE.md`](THIRD_PARTY_PROVENANCE.md) and
[`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md).

## Decision: MIT License

The project owner selected MIT for the `v0.1.0-alpha` release. The complete
license text is stored at the repository root in [`LICENSE`](../../LICENSE),
and package metadata records the SPDX expression `MIT`.

## Alternative considered: Apache License 2.0

Apache-2.0 was considered because it is permissive while stating an explicit contributor
patent grant and patent-termination condition. It is longer than MIT and
requires preservation of its notices. The MIT-licensed academic skills can be
redistributed alongside an Apache-2.0 SkillStack project as separately noticed
third-party material.

## Selected trade-off

MIT is short, widely recognized, and imposes minimal redistribution
conditions. It does not contain the same explicit patent-license language as
Apache-2.0.

## Owner acceptance checklist

- [x] Project owner selected `MIT`.
- [x] Add the complete chosen text as the repository-root `LICENSE` file.
- [x] Add the matching license identifier and license files to
      `pyproject.toml`.
- [x] Remove pending-license wording from contributor and release documents.
- [ ] Independently confirm any university or employer ownership obligations
      that may apply to particular contributions.
- [x] Run `uv run skillstack release-check` without the waiver flag.

This document records engineering trade-offs, not legal advice.
