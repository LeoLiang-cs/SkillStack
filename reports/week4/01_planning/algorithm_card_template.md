# Paper Algorithm Card Template

Use one copy of this template for every main algorithm paper. Complete it from
the paper and released source before proposing a SkillStack implementation.
Do not fill unknown fields by inference without labelling them.

## A. Identity and evidence

- Paper:
- arXiv ID and version:
- Authors/year:
- Paper URL:
- Official project/repository URL:
- Source snapshot date:
- Evidence read: abstract / method / algorithm / experiments / appendix / code
- Reproduction assets available: code / prompts / configs / data / checkpoints
- Evidence gaps:

## B. Claimed contribution

- Problem addressed:
- Claimed algorithmic unit:
- What is new relative to its baselines:
- What the paper explicitly does not claim:

## C. Native pipeline context

- Upstream components:
- Downstream components:
- Native host agent/executor:
- Persistent library or memory:
- External models/tools:
- Offline stages:
- Online stages:
- Update clock: per step / episode / batch / training phase / library maintenance

## D. Algorithm anatomy

### Inputs

- Required inputs:
- Optional inputs:
- Hidden/native assumptions:

### State and artifacts

- Skill representation:
- Task/state representation:
- Intermediate artifacts:
- Persistent mutations:

### Ordered mechanism

1. 
2. 
3. 

### Outputs

- Primary output:
- Auxiliary/raw output:
- Failure output:
- Confidence/score/evidence:

### Invariants

- Correctness or validity conditions:
- Information that must not be dropped:
- Ordering/dependency assumptions:

## E. Candidate plug-in boundary

- Proposed SkillStack responsibility:
- Proposed internal primitive:
- Smallest faithful swappable unit:
- Is the paper method a component or a composite system?
- Required adapter inputs/outputs:
- Neighboring components that must remain unchanged in a valid swap:
- Conditions that would make the integration only `paper_inspired`:

## F. Native experimental design

### Evaluation grid

- Benchmarks/environments:
- Splits and task counts:
- Skill library source/size/quality:
- Backbone, writer, user, verifier, or reranker models:
- Seeds/runs/temperature:
- Step/token/time budgets:

### Baselines and controls

- Native baseline:
- Strongest matched baseline:
- Ablations:
- Negative/no-op controls:

### Metrics

- Primary task metric:
- Efficiency metrics:
- Intrinsic component metrics:
- Reliability/regression metrics:
- Statistical reporting:

### Transfer and stress axes

- Cross-model:
- Cross-domain/OOD:
- Scale:
- Complexity:
- Quality degradation:
- Writer-by-user or component-by-host matrix:

## G. Paper-reported findings

Record findings as paper-reported, with section/table references. Do not treat
them as independently reproduced SkillStack results.

- Finding 1:
- Finding 2:
- Finding 3:
- Limitations:

## H. SkillStack architecture test

- Responsibilities covered:
- Boundaries exposed cleanly:
- Responsibilities currently conflated by the paper:
- Information missing from current SkillStack interfaces:
- Current SkillStack fields unused by the paper:
- Does this paper support keeping, refining, or revising the current structure?

## I. Reproduction and integration verdict

- Fidelity status: `unassessed` / `paper_faithful_possible` /
  `paper_inspired_only` / `blocked`
- Native reproduction requirement:
- First safe smoke test:
- Proposed host configurations:
- Expected adapter friction:
- Open questions and blockers:

