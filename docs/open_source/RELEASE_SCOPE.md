# Open-source release scope

Status: implemented release policy for the `v0.1.0-alpha` candidate.

This document is a scope decision. The owner selected MIT as recorded in
[`LICENSE_DECISION.md`](LICENSE_DECISION.md); third-party redistribution
permissions are documented separately.

## Include in the core repository

| Area | Contents | Condition |
|---|---|---|
| Runtime | `src/skillstack/` | SkillStack-authored code only |
| Commands | `scripts/` | Paths and credentials are configurable |
| Tests | `tests/` | No required local secrets or private checkouts |
| Configuration | Safe files under `configs/` | No keys or private endpoints |
| Native examples | `skills/alfworld_static/` | Project-authored fixtures |
| Evidence | Curated `reports/` | Relative paths and claim-bounded wording |
| Design | `docs/original/` and `docs/README.md` | Historical/reference labels retained |
| Contributor surface | `CONTRIBUTING.md`, issue and PR templates | Evidence and repository-hygiene rules enforced |
| Provenance | `THIRD_PARTY_NOTICES.md` and `configs/component_fidelity.yaml` | Third-party distribution and fidelity remain distinct |
| Research skills | Six tracked directories under `.agents/skills/` | Derived from MIT-licensed `chtc66/academic-skills`; notice retained |

## Hold until publication policy is decided

- `docs/final_cards/`: BLM is a research candidate and may conflict with a
  double-blind submission or reveal unpublished experimental framing.
- Detailed novelty-search outputs and intermediate idea-spark artifacts.
- Any report whose wording or provenance has not passed the publication audit.

## Do not commit

- `.env`, API keys, tokens or credentials;
- `runs/` and generated model outputs;
- `data/alfworld/` benchmark assets;
- `papers/` PDFs and extracted full text copied from external sources;
- `.venv/`, `dist/`, `build/`, caches and `.DS_Store` files;
- temporary `step*.md` and `allinone.md` research scratch files.

## Required review before release

- [x] Select and record the MIT project license.
- [x] Check provenance and license compatibility of the six tracked
      `.agents/skills/` directories.
- [x] Check every GRASP/SkillRL/SkillOps integration for source-faithful versus
      adapted status.
- [x] Replace private absolute paths with repository-relative paths or CLI
      arguments.
- [x] Confirm that the 243-file release snapshot redistributes no external data
      or paper PDF.
- [ ] Decide whether the release is anonymous for the target venue.

## Release acceptance

A release candidate is publishable only when a fresh clone can run the
zero-model checks without private files, the documentation describes current
claims and limits accurately, and the final file list has passed the
publication audit in `PUBLICATION_AUDIT.md`. The technical fresh-clone gate now
passes; publication remains blocked only on the venue/anonymity decision and
final hosted-CI/file-list review.
