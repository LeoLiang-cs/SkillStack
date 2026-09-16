# Maintenance and support policy

This alpha is maintained as a reproducible research harness, not as a hosted
service. The maintained target is Python 3.11/3.12 on Linux/macOS; Python
3.9/3.10 is historical reproduction and Windows is unverified. Optional
ALFWorld, AgentBench, GRASP, SkillRL, and SkillOps environments retain their
own dependency and service boundaries.

## Change policy

- Core changes must keep the zero-model path offline and deterministic.
- Schema or public CLI changes require a focused test, documentation update,
  and a migration note when the schema version changes.
- External components require source/commit, license, and fidelity updates.
- A research claim change requires a claim-bounded report or fixture; a passing
  unit test alone is not performance evidence.
- Alpha releases may introduce breaking changes. No SLA is promised.

## Release policy

Each release candidate is tied to one resolved commit. The release packet must
include source/wheel/sdist hashes, support-matrix evidence, test summary,
known limitations, provenance, and rollback instructions. A dirty worktree or
an unverified platform cannot be silently folded into the packet.

Creating a tag, GitHub Release, publishing to PyPI, or changing the held BLM
research scope requires separate owner confirmation. Until then, the state is
`release-ready` at most, never published.

## Dependency and rollback review

Review `uv.lock`, CI action pinning, optional extras, and third-party notices
when dependencies change. Roll back by selecting the previous verified commit,
artifact, and configuration; never delete or rewrite raw experiment evidence.

Use [`SUPPORT_MATRIX.md`](SUPPORT_MATRIX.md) and
[`PUBLICATION_AUDIT.md`](PUBLICATION_AUDIT.md) as the current release review
surfaces.
