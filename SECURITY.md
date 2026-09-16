# Security policy

SkillStack is an experimental research harness. The repository must not
contain API keys, cookies, private absolute paths, benchmark credentials,
generated provider transcripts, or external checkouts.

## Reporting a vulnerability

For a suspected credential exposure, path escape, unsafe code execution, or
supply-chain issue, use a private GitHub Security Advisory for the repository
when that service is available. Do not open a public issue containing a secret.
If private reporting is unavailable, remove the sensitive value from the
message and contact the project owner through the repository's established
private channel before discussing details publicly.

Include the affected commit/version, a minimal safe reproduction, impact, and
whether the issue affects the offline core, an optional integration, or a
research-only script. Never attach the original credential or unredacted
provider response.

## Current safety boundaries

- The public demo is zero-model and zero-network.
- `preflight`, `check-repo`, and `release-check` are repository-only checks.
- Output root and run ID containment is enforced by the trace writer.
- Manifest and summary writes are atomic and refuse accidental overwrite.
- Provider error details are truncated and credential-like values are redacted;
  callers still must redact copied logs.
- Live client calls have finite timeout/retry/backoff settings and a run-level
  call/token/cost budget; exhaustion is recorded as an error rather than a
  valid measurement.
- External model/benchmark code is not automatically executed by the core
  package and remains outside the maintained offline guarantee.

Security fixes must add a focused regression test and update the release audit
or known-issues record. Do not silently rewrite historical raw evidence.
