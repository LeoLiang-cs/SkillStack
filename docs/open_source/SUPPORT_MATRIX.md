# Core support matrix

Status: G1 Batch 1 in progress (2026-09-16). A row marked `configured` is not
yet a hosted-platform evidence claim; the package acceptance script must be run
before the row is described as verified.

| Surface | Maintained target | Evidence status | Boundary |
|---|---|---|---|
| Core import, offline demo, tests | Python 3.11 / 3.12 | `configured`; full suite local Python 3.10 historical and Python 3.12 macOS | No model, dataset, or network calls |
| Linux core CI | Ubuntu, Python 3.11 / 3.12 | `configured`; hosted run pending | Required gate for G1 |
| macOS core CI | macOS, Python 3.12 | `configured`; hosted run pending | Apple Silicon/x86 result must be recorded separately |
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

The Python 3.12 macOS package smoke is useful local evidence but does not
replace hosted Linux/macOS CI or a full maintained-platform test run. Until
those rows have real outputs, README and release material must use
“target/configured” language rather than “verified support”.

## Week 7 local evidence record

- Date: 2026-09-16; host: macOS 26.6.2 arm64; `uv 0.11.28`.
- Python: 3.12.13 maintained-target local smoke and 3.10.20 historical
  reproduction; `uv.lock` SHA-256:
  `8f2f69d3b0b9bb13e757c80198541b8fd1a3e1cdca6b98799af433fb4270890f`.
- Core gate: [`g1_core_gate_local_312.json`](../../report/week7/g1_core_gate_local_312.json)
  and [`g1_core_gate_local_310.json`](../../report/week7/g1_core_gate_local_310.json);
  each reports 137 tests, zero failures/errors, and one allowlisted conditional skip.
- Packaging: [`g1_package_acceptance_continuation_312.json`](../../report/week7/g1_package_acceptance_continuation_312.json)
  and [`g1_package_acceptance_continuation_310.json`](../../report/week7/g1_package_acceptance_continuation_310.json).
