# Changelog

All notable public changes are documented here.

## [0.1.0-alpha] - Unreleased

See the complete
[`v0.1.0-alpha` release notes](docs/open_source/RELEASE_NOTES_v0.1.0-alpha.md).

- Added installable package metadata and the `skillstack` CLI.
- Added deterministic preflight, repository scanning, and composability Demo.
- Added Python 3.9/3.10 CI and zero-model verification.
- Added contributor guidance, issue/PR templates, and third-party provenance
  plus component-fidelity records.
- Added commit-based release selection, a versioned public-scope policy,
  hash-addressed manifests, and source/wheel/sdist isolation checks.
- Began G1 Batch 1: packaged the offline demo and safe backend metadata,
  added a fresh-environment wheel/sdist acceptance script, and configured the
  Python 3.11/3.12 Linux/macOS maintained matrix while retaining 3.9/3.10 as
  historical reproduction.
- Began G1 O04: added run-manifest identity hashes, atomic JSON writes, safe
  run IDs, resume drift checks, and separate episode/measurement status fields.
- Began G1 O06/O07: added user, development, reproducibility, security,
  maintenance, and release-packet guidance; provider error details are bounded
  and credential-like values are redacted.
- Fixed the seeded random retriever for Python 3.12 by using a stable integer
  seed derived from task ID and seed; added a cross-process regression test.
- Kept BLM research cards and private/intermediate research artifacts outside
  the intended public alpha snapshot.
