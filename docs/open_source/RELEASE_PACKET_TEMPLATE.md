# G1 release packet template

This template is a checklist, not evidence by itself. Copy it to
`report/weekN/` for one candidate and fill every field from the same resolved
commit. Use `not run` rather than an empty field.

## Identity

- Candidate commit SHA:
- Branch/tag state:
- Dirty-worktree paths (informational):
- Source snapshot hash:
- Release policy hash:
- Generated at (UTC):

## Artifacts

| Artifact | Path | SHA-256 | Bytes | Environment check |
|---|---|---|---:|---|
| source snapshot | | | | |
| wheel | | | | |
| sdist | | | | |

The artifact check must run from a non-repository directory in a fresh
environment. Do not list an artifact as verified from `uv build` alone.

## Evidence

- Core offline command and result:
- Packaging command and result:
- Integration fixture command and result:
- Linux/Python 3.11:
- Linux/Python 3.12:
- macOS/Python 3.12:
- Hosted CI URL and commit:
- Test pass/skip counts:
- Network/model calls:

## Contract and security

- Manifest/trace/summary schema versions:
- Identity/resume fixtures:
- Path containment and atomic-write checks:
- Secret redaction and credential scan:
- CI permissions/action pins:
- Dependency/provenance review:
- Known limitations and unsupported platforms:
- Rollback commit/artifact/config:

## Scope decision

- Held research and external data excluded: `yes/no`
- BLM implementation claim made: `no`
- Tag/GitHub Release/PyPI publication authorized by owner: `no/yes`
- Final owner file-list review: `pending/complete`
