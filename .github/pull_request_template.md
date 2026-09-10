## Summary

Describe the scoped change and why it belongs in SkillStack.

## Evidence and claim boundary

- Evidence artifact or test:
- Component slot(s):
- External source and pinned commit, if any:
- Fidelity label before/after:
- What this change does **not** establish:

## Verification

- [ ] `uv run skillstack preflight`
- [ ] `uv run skillstack check-repo`
- [ ] `uv run skillstack demo`
- [ ] `uv run python -m unittest discover -s tests -q`
- [ ] `uv build`
- [ ] No credentials, private paths, generated runs, downloaded data, PDFs, or external checkouts were added.
- [ ] Provenance and fidelity records were updated if an external integration changed.
- [ ] Documentation distinguishes implemented behavior from proposed research.
