# Troubleshooting

## `skillstack` is not found

Confirm that the environment where the package was installed is active:

```bash
python -m pip show skillstack
python -m skillstack --version
```

If you are checking a local artifact, install the wheel or sdist explicitly
from its containing directory. An editable source checkout is not evidence for
the user installation path.

## The demo says a repository is required

`preflight`, `check-repo`, and `release-check` are contributor-only commands.
Run `skillstack demo` without `--root` for packaged resources. If a contributor
needs checkout fixtures, pass the checkout explicitly:

```bash
skillstack demo --root /path/to/SkillStack --output-root ./skillstack-runs
```

The output root may be outside the checkout and must be writable.

## Output path or run ID is rejected

Use a writable output directory and a simple run ID such as
`demo_c1_20260916`. Do not pass an absolute run ID, `..`, a slash, or a path
that points outside the output root. Existing run directories are not reused by
the default demo.

## A run cannot be resumed

Check that the original `run_manifest.json` exists and that the proposed
configuration has the same `run_identity_sha256`. A drift error is deliberate:
create a new run rather than mixing traces from different inputs. A duplicate
episode ID or an existing summary also requires a new run or an explicit
caller-side recovery decision.

## Backend configuration fails

Check the effective source order in
[`configuration_and_runs.md`](configuration_and_runs.md). Validate the JSON,
confirm the named environment variable is present, and ensure the selected
backend exists before starting a provider call. Never paste the key into a
configuration file or an issue.

## A provider request times out or returns an error

The provider path is an optional research experiment, not part of the offline
demo gate. Keep the redacted error, run manifest, and completed raw episodes;
record the provider, model, timeout, retry count, and budget. Authentication or
configuration errors should be fixed, not repeatedly retried. Do not count a
timeout or provider error as a valid task result.

## Optional benchmark data is missing

ALFWorld and other external environments are intentionally separate. Install
their locked optional dependencies and obtain data through the source's own
terms before running a historical script. A skipped optional environment must
remain labelled `skip`/`not run`; it does not become maintained-core evidence.
