# Publication audit

Audit date: 2026-09-16

Scope: repository public-release preparation, not a paper integrity review.

## Current findings

| Check | Status | Notes |
|---|---|---|
| Core package builds | PASS | Wheel and source distribution build locally |
| Zero-model preflight | PASS | No data, network or model call required |
| Unit tests | PASS WITH NOTE | 137 passed in local Python 3.12 macOS environment, 1 conditional external-integration test skipped; prior Python 3.10/3.12 127-test results remain historical evidence |
| Personal absolute paths | PASS after current cleanup | Scripts/tests use configurable or portable roots; historical reports use relative placeholders |
| Secrets in intended public snapshot | PASS | 280 text/config files scanned with zero findings; `.env` remains ignored |
| Documentation migration | PASS IN SNAPSHOT | `docs/original/` is included; `docs/final_cards/` is explicitly held from the public alpha snapshot |
| License | PASS | Project owner selected MIT; root license and package SPDX metadata are present |
| Third-party provenance | PASS | Tracked academic skills are attributed to the MIT-licensed upstream; external repository code/data is not redistributed; fidelity register added |
| Zero-model demo | PASS | Both retriever cells complete the deterministic fixture; stable fingerprint checked; no network/model calls |
| CI | CONFIGURED, HOSTED RESULT PENDING | Maintained target is Ubuntu 3.11/3.12 plus macOS 3.12; core/packaging JSON summaries are retained as pinned artifacts; first hosted run awaits push |
| Wheel/sdist non-repo acceptance | PARTIAL | Fresh Python 3.12 macOS wheel/sdist paths pass metadata/license/entrypoint, demo, and uninstall checks; prior Python 3.10 historical and hosted Linux/macOS/Python 3.11 evidence remain pending |
| Commit-based fresh-clone release gate | PASS ON TEMP CANDIDATE | Temporary candidate `2ad50819c55d8586ffb58cfc15454645e97a0dec`: 244 files, source/wheel/sdist checks, zero-model gate and 112-test run passed. Current project `HEAD` is correctly blocked until the policy is committed. |
| BLM publication status | HOLD | Keep final cards private until venue/anonymity policy is decided |

## Claim boundary for the current release

The repository can claim a modular, traceable harness for controlled Skill
Agent component swaps and compatibility experiments. It must not claim that BLM
is implemented, that the Canonical Interface is behaviorally complete, or that
GRASP/SkillRL have been fully reproduced.

## Final release gates

- [x] MIT license decision recorded; any university/employer ownership
      obligations remain the project owner's administrative check.
- [x] Fresh-clone install and zero-model demo succeed.
- [x] Commit-based collector, policy validation, manifest hashes, and
      wheel/sdist member checks pass on the temporary candidate.
- [ ] CI passes the same no-secret test suite.
- [ ] Final project commit has no unexplained release-scope diff and no
      absolute local paths, credentials or private external checkout paths.
- [x] Public research claims are bounded by a report, fixture, provenance entry,
      or trace schema.
- [ ] Venue/anonymity decision recorded for `docs/final_cards/`.
- [ ] Final tracked-file list reviewed by the project owner.
