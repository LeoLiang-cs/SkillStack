# Third-party provenance and fidelity register

Audit date: 2026-09-10

Scope: files distributed in the alpha snapshot and optional external research
integrations referenced by SkillStack.

## Distribution boundary

| Item | Upstream | License observed | Distributed here? | Boundary |
|---|---|---:|---:|---|
| Six tracked academic research skills | [chtc66/academic-skills](https://github.com/chtc66/academic-skills) | MIT | Yes, under `.agents/skills/` | Attribution retained in `THIRD_PARTY_NOTICES.md`; untracked local skills are excluded |
| PyYAML | [yaml/pyyaml](https://github.com/yaml/pyyaml) | Installed dependency | No source vendoring | Resolved through `uv.lock` |
| ALFWorld | [alfworld/alfworld](https://github.com/alfworld/alfworld) | External project terms apply | No | Optional dependency and separately downloaded benchmark assets |
| GRASP | [jomoll/GRASP](https://github.com/jomoll/GRASP) | MIT at pinned checkout | No | Optional external checkout at `9d7d125a3e9b46ed591692475eb07aff4ae67d34` |
| SkillRL | [aiming-lab/SkillRL](https://github.com/aiming-lab/SkillRL) | MIT at pinned checkout | No | Optional external checkout at `8e66726ed866a4e0a7f053586a41022798192e6c` |
| SkillOps | [Hik289/SkillOps](https://github.com/Hik289/SkillOps) | MIT at pinned checkout | No | Optional external checkout at `c80b05246369c0b9d82a293390ca5add675c516a` |
| AgentBench | Used through GRASP's benchmark tree | External project terms apply | No | Services and benchmark assets remain external |
| Paper PDFs and extracted full text | Original publishers/authors | Varies | No | `papers/` is excluded from release |

“License observed” records the license file present in the inspected source
snapshot; it is not legal advice and does not change an upstream license.

## Runtime constraints

| Integration | Frozen source/version | Python boundary |
|---|---|---|
| Core YAML parsing | PyYAML 6.0.3 in `uv.lock` | Maintained core Python 3.11/3.12 |
| ALFWorld | PyPI `alfworld==0.4.2` through the optional `alfworld` extra | Separate environment and downloaded assets; not imported by core/demo |
| GRASP + AgentBench | GRASP commit `9d7d125a3e9b46ed591692475eb07aff4ae67d34` | Pinned external checkout; its historical environment is not resolved by the core lock |
| SkillRL | commit `8e66726ed866a4e0a7f053586a41022798192e6c` | Pinned external checkout; Python compatibility remains experiment-specific |
| SkillOps | commit `c80b05246369c0b9d82a293390ca5add675c516a` | Pinned external checkout; Python compatibility remains experiment-specific |

The maintained core upgrade does not rewrite historical external environments.
An integration whose pinned environment does not resolve on Python 3.11/3.12
stays historical or isolated instead of lowering the core support baseline.

## Fidelity register

The machine-readable source of truth is
[`configs/component_fidelity.yaml`](../../configs/component_fidelity.yaml). The
current public evidence supports these boundaries:

| Cell | Label | What is supported | What is not supported |
|---|---|---|---|
| Native fixture Demo | `not_applicable_local` | Same interface path, deterministic trace, changed retrieval selection | Benchmark performance or paper reproduction |
| GRASP proposer under GRASP gate | `source_variant` + `source_component_experiment` | Released proposer/repository boundary compatibility | Full GRASP paper performance |
| SkillRL updater under GRASP gate | `source_variant` + `cross_paper_slot_experiment` | ADD-only adapter compatibility | Zero-conversion interchangeability; complete SkillRL |
| SkillRL provider-substituted smoke | `source_variant` + `provider_substituted` | Released prompt/parser path with recorded substitution | Source-faithful o3 result or quality superiority |
| SkillOps maintenance sweep | `source_variant` + `source_component_experiment` | Released primitive-level maintenance path | Complete SkillOps/CGPD reproduction |
| Complete SkillOps method | `blocked` | The missing-artifact boundary is recorded | A successful full-method result |

## Required update rule

Any pull request that changes an external method, source commit, provider,
adapter semantics, or experimental claim must update both the machine-readable
register and the corresponding evidence report. A successful compatibility
check must not silently promote a fidelity label.
