# Core support matrix

Status: G1 core matrix verified at commit `fc6a446` (2026-09-16). Hosted run:
<https://github.com/LeoLiang-cs/SkillStack/actions/runs/35158925050>.

| Surface | Maintained target | Evidence status | Boundary |
|---|---|---|---|
| Core import, offline demo, tests | Python 3.11 / 3.12 | `verified` in hosted matrix | No model, dataset, or network calls |
| Linux core CI | Ubuntu, Python 3.11 / 3.12 | `verified` at `fc6a446` | x86_64 runner evidence |
| macOS core CI | macOS, Python 3.11 / 3.12 | `verified` at `fc6a446` | Apple Silicon runner evidence; x86 remains unverified |
| Python 3.9 / 3.10 | Historical reproduction | `historical` | Do not present as maintained support |
| Windows | Not classified | `unverified` | No support or incompatibility claim |
| ALFWorld / AgentBench / GRASP / SkillRL / SkillOps | Experiment-specific environments | `separate` | Their locks, services, and evidence remain versioned independently |

## Required evidence record

For each maintained-platform run, retain the Python patch version, OS and
architecture, `uv` version, lock-file hash, date, command, and pass/fail output.
The canonical local command is:

```bash
uv run python scripts/check_package_install.py --python 3.12 \
  --summary report/week7/g1_package_acceptance.json
```

The package smoke runs in hosted Ubuntu Python 3.12 and in the local macOS
Python 3.12 environment. The other matrix cells build the package and run the
full core gate, but do not repeat the fresh-environment wheel/sdist smoke.

## G1 hosted evidence record

| Runner | Python | Core gate | Optional skips |
|---|---|---:|---:|
| Ubuntu x86_64 | 3.11.15 | 140 passed | 2 allowlisted |
| Ubuntu x86_64 | 3.12.3 | 140 passed | 2 allowlisted |
| macOS arm64 | 3.11.9 | 140 passed | 2 allowlisted |
| macOS arm64 | 3.12.10 | 140 passed | 2 allowlisted |

All four jobs reported zero failures, zero errors, and no unexpected skip
reason. The Ubuntu Python 3.12 packaging job also passed wheel/sdist metadata,
license, entrypoint, packaged demo, uninstall, and temporary-directory
isolation checks. The workflow pins `uv 0.11.28`; `uv.lock` SHA-256 is
`8f2f69d3b0b9bb13e757c80198541b8fd1a3e1cdca6b98799af433fb4270890f`.

## Week 7 local evidence record

- Date: 2026-09-16; host: macOS 26.6.2 arm64; `uv 0.11.28`.
- Python: 3.12.13 maintained-target local smoke and 3.10.20 historical
  reproduction; `uv.lock` SHA-256:
  `8f2f69d3b0b9bb13e757c80198541b8fd1a3e1cdca6b98799af433fb4270890f`.
- Core gate: [`g1_core_gate_local_final_312.json`](../../report/week7/g1_core_gate_local_final_312.json)
  reports 140 tests, zero failures/errors, and one allowlisted conditional skip.
  Earlier 137-test Python 3.12 and Python 3.10 records remain historical.
- Packaging: [`g1_package_acceptance_continuation_312.json`](../../report/week7/g1_package_acceptance_continuation_312.json)
  and [`g1_package_acceptance_continuation_310.json`](../../report/week7/g1_package_acceptance_continuation_310.json).
