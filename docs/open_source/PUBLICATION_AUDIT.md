# Publication audit

Audit date: 2026-09-10

Scope: repository public-release preparation, not a paper integrity review.

## Current findings

| Check | Status | Notes |
|---|---|---|
| Core package builds | PASS | Wheel and source distribution build locally |
| Zero-model preflight | PASS | No data, network or model call required |
| Unit tests | PASS WITH NOTE | 108 passed locally on Python 3.9 and 3.10, 1 conditional external-integration test skipped |
| Personal absolute paths | PASS after current cleanup | Scripts/tests use configurable or portable roots; historical reports use relative placeholders |
| Secrets in intended public snapshot | PASS | 237 text/config files scanned with zero findings; `.env` remains ignored |
| Documentation migration | PASS IN SNAPSHOT | `docs/original/` is included; `docs/final_cards/` is explicitly held from the public alpha snapshot |
| License | PASS | Project owner selected MIT; root license and package SPDX metadata are present |
| Third-party provenance | PASS | Tracked academic skills are attributed to the MIT-licensed upstream; external repository code/data is not redistributed; fidelity register added |
| Zero-model demo | PASS | Both retriever cells complete the deterministic fixture; stable fingerprint checked; no network/model calls |
| CI | READY LOCALLY | Python 3.9/3.10 workflow runs preflight, public scan, demo, tests and build; first hosted run awaits push |
| Fresh-clone release gate | PASS | 243-file allowlisted snapshot, including the MIT license, was committed to a temporary repository, cloned, installed, scanned, demoed, tested and built successfully without a waiver |
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
- [ ] CI passes the same no-secret test suite.
- [x] No absolute local paths, credentials or private external checkout paths
      in the intended public snapshot.
- [x] Public research claims are bounded by a report, fixture, provenance entry,
      or trace schema.
- [ ] Venue/anonymity decision recorded for `docs/final_cards/`.
- [ ] Final tracked-file list reviewed by the project owner.
