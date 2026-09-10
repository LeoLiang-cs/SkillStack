# Contributing to SkillStack

Thank you for helping improve SkillStack. This repository is a research
harness, so reproducibility and claim accuracy matter as much as code quality.

## Set up a development checkout

SkillStack supports Python 3.9 and 3.10.

```bash
git clone <your-fork-url>
cd SkillStack
uv sync --frozen
uv run skillstack preflight
uv run skillstack demo
uv run python -m unittest discover -s tests -q
```

Install `uv` first if it is not already available. ALFWorld-backed experiments
are optional and require `uv sync --extra alfworld` plus separately downloaded
benchmark assets.

## Before opening a pull request

Run the complete zero-model gate:

```bash
uv run skillstack preflight
uv run skillstack check-repo
uv run skillstack demo
uv run python -m compileall -q src scripts tests
uv run python -m unittest discover -s tests -q
uv build
```

These commands must not require API keys, private checkouts, benchmark data, or
network access after dependencies are installed.

## Research evidence rules

- Separate compatibility, gate acceptance, task performance, and paper
  reproduction claims.
- Label every external-method integration with the vocabulary in
  [`configs/component_fidelity.yaml`](configs/component_fidelity.yaml).
- Preserve raw failures and adapter transformations. Do not treat an empty
  `dropped` list as proof of semantic equivalence.
- Record source repository and commit for source-backed experiments.
- Do not describe provider-substituted or reconstructed cells as
  `paper_faithful`.
- Add or update a claim-bounded report when behavior or experimental evidence
  changes.

## Repository hygiene

Never commit credentials, `.env`, generated runs, downloaded benchmark data,
paper PDFs, private absolute paths, or external repository checkouts. Keep
large or model-backed runs resumable and document the exact command, expected
outputs, and failure state instead of hiding unsuccessful attempts.

The proposed BLM research cards are held from the public alpha snapshot until
the venue and anonymity policy is decided.

## Issues and pull requests

Use the provided templates. Keep each pull request focused, state which checks
ran, and identify any external component and fidelity change. A pull request
that changes a research claim should link to the exact report or trace schema
that supports it.

By contributing, you agree that your contribution will be distributed under
the repository's MIT License.
