# Publication audit

Audit date: 2026-09-16

Scope: repository public-release preparation, not a paper integrity review.

## Current findings

| Check | Status | Notes |
|---|---|---|
| Core package builds | PASS | Wheel and source distribution build locally |
| Zero-model preflight | PASS | No data, network or model call required |
| Unit tests | PASS WITH NOTE | 140 passed locally and on all four hosted Python/platform cells; local run had 1 and hosted runs had 2 allowlisted optional-data skips, with no unexpected skip |
| Personal absolute paths | PASS after current cleanup | Scripts/tests use configurable or portable roots; historical reports use relative placeholders |
| Secrets in intended public snapshot | PASS | 280 text/config files scanned with zero findings; `.env` remains ignored |
| Documentation migration | PASS IN SNAPSHOT | `docs/original/` is included; `docs/final_cards/` is explicitly held from the public alpha snapshot |
| License | PASS | Project owner selected MIT; root license and package SPDX metadata are present |
| Third-party provenance | PASS | Tracked academic skills are attributed to the MIT-licensed upstream; external repository code/data is not redistributed; fidelity register added |
| Zero-model demo | PASS | Both retriever cells complete the deterministic fixture; stable fingerprint checked; no network/model calls |
| CI | PASS | Commit `fc6a446` passed Ubuntu/macOS Python 3.11/3.12 in [hosted run 35158925050](https://github.com/LeoLiang-cs/SkillStack/actions/runs/35158925050); core/packaging JSON summaries are retained as artifacts |
| Wheel/sdist non-repo acceptance | PASS | Fresh Python 3.12 macOS and hosted Ubuntu wheel/sdist paths pass metadata/license/entrypoint, packaged demo, uninstall, and temporary-directory isolation checks; Python 3.10 remains historical only |
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
- [x] CI passes the same no-secret test suite.
- [x] Core G1 commit has no unexplained core-scope diff and no
      absolute local paths, credentials or private external checkout paths.
- [x] Public research claims are bounded by a report, fixture, provenance entry,
      or trace schema.
- [ ] Venue/anonymity decision recorded for `docs/final_cards/`.
- [ ] Final tracked-file list reviewed by the project owner.
