# Third-party notices

This file records third-party material distributed in this repository.
SkillStack-authored material is separately covered by the root MIT `LICENSE`.

## Academic research skills

Files under the six tracked directories in `.agents/skills/` were derived from
[`chtc66/academic-skills`](https://github.com/chtc66/academic-skills), which is
distributed under the MIT License:

- `benchmark-extractor`
- `experiment-log-summarizer`
- `paper-deep-note`
- `research-gap-finder`
- `survey-writer`
- `weekly-lab-update`

Upstream copyright and permission notice:

```text
MIT License

Copyright (c) 2026 chtc66

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

The upstream license is also available in the
[`academic-skills` repository](https://github.com/chtc66/academic-skills/blob/main/LICENSE).
SkillStack-specific or untracked skills are not covered by this notice.

## External research repositories

GRASP, SkillRL, SkillOps, AgentBench, and ALFWorld source trees and datasets are
not redistributed in this repository. Some optional experiment adapters invoke
separately obtained checkouts. Their sources, pinned commits, and fidelity
boundaries are recorded in
[`docs/open_source/THIRD_PARTY_PROVENANCE.md`](docs/open_source/THIRD_PARTY_PROVENANCE.md).

## Python dependencies

Python dependencies are installed from their own distributions and retain
their respective copyright and license terms. See `pyproject.toml` and
`uv.lock` for the resolved dependency set.
