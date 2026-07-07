# 140 — Retry the TestPyPI smoke-test install

**Date:** 2026-07-03
**Issue:** [dev-docs/issues/done/140-release-smoke-test-testpypi-propagation.md](../issues/done/140-release-smoke-test-testpypi-propagation.md)

## Problem

In `.github/workflows/release.yml`, the "Smoke test TestPyPI install" step runs
`pip install --index-url https://test.pypi.org/simple/ "plcc-ng==${VERSION}"`
seconds after the "Publish to TestPyPI" step. TestPyPI's simple index can lag
the upload by seconds to minutes, so the install intermittently fails with
"No matching distribution found" even though the upload succeeded. The
`publish` job fails, `create-release` is skipped, and the release lands in the
tagged-but-not-released state described by issue 134. Observed live with
v0.64.2 (run 28677279797, 2026-07-03).

## Decision

Retry the actual `pip install` with a fixed backoff, inline in the workflow
step. Retrying the real install (rather than polling the JSON API or the
simple index first) tests the exact contract that must hold: the simple index
pip uses serving the new version. The JSON API and the simple index propagate
independently, so a poll-then-install scheme can still flake.

## Design

Only the "Smoke test TestPyPI install" step in
`.github/workflows/release.yml` changes:

- `/tmp/smoke-venv` is created once, before the loop. A failed install leaves
  nothing harmful behind, so the venv is not rebuilt per attempt.
- The `pip install` runs in a retry loop: up to **20 attempts** with a **15s
  sleep** between failures (~5 minutes worst case, matching the budget
  suggested in the issue).
- The install gains **`--no-cache-dir`** so a stale index response cached by
  pip on an early attempt cannot poison later attempts.
- Each failed attempt logs
  `TestPyPI index not ready (attempt N/20); retrying in 15s` so a flaky run is
  diagnosable from the workflow log.
- The functional assertions (`plcc-make` against the trivial fixture and the
  `plcc-ng/spec.json` existence check) stay outside the loop and run once —
  they are deterministic once the install succeeds.

## Error handling

If all 20 attempts fail, the step exits 1 with
`FAIL: plcc-ng==<version> not installable from TestPyPI after 20 attempts`.
Behavior from there is unchanged: `publish` fails, `create-release` is
skipped, and the issue-134 manual recovery ("Re-run failed jobs" on the same
run) still applies — it just becomes far less likely to be needed.

Accepted side effects:

- The loop also absorbs unrelated transient pip/network errors.
- A genuinely broken upload takes ~5 minutes to fail instead of seconds.

Runner-time cost is not a concern: GitHub-hosted jobs may run up to 6 hours,
and the repository is public, so minutes are free.

## Testing

Workflow steps have no unit-test tier in this repository. Verification:

- Syntax-check the step's script (`bash -n`; `shellcheck`/`actionlint` if
  available in the container).
- The real proof is the next release run on `main`.

## Alternatives considered

- **Poll `https://test.pypi.org/pypi/plcc-ng/json` before installing** —
  cheaper per attempt, but the JSON API can show the release while the simple
  index pip uses still lags; rejected as false confidence.
- **Poll the simple index itself, then install once** — waits on the right
  signal but adds HTML/JSON parsing and still may not hit the same CDN node
  pip does; rejected as complexity without a correctness gain.
- **Extract the smoke test to a `bin/` script** — follows the repository's
  bin/ convention, but the step is only meaningful immediately after a
  TestPyPI upload and needs the semantic-release version output; kept inline
  for the smallest diff.
