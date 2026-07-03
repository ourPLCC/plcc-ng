# 140 - Smoke test races TestPyPI index propagation

**Type:** fix
**Date:** 2026-07-03

## Description

In `.github/workflows/release.yml`, the "Smoke test TestPyPI install" step
runs `pip install --index-url https://test.pypi.org/simple/ "plcc-ng==${VERSION}"`
immediately after the "Publish to TestPyPI" step. TestPyPI's simple index
can lag the upload by seconds to minutes, so the install intermittently
fails with "No matching distribution found" even though the upload
succeeded. The `publish` job then fails, `create-release` is (correctly)
skipped, and the release is left in the tagged-but-not-released state that
issue 134 describes.

Observed live with v0.64.2 (run 28677279797, 2026-07-03): TestPyPI upload
completed at 18:24:13 UTC, the smoke test ran seconds later and failed;
the files were visible on TestPyPI shortly after.

## Steps to Reproduce

1. Merge a releasable commit to `main`.
2. The `publish` job uploads to TestPyPI and immediately pip-installs the
   new version from TestPyPI.
3. Intermittently, the index has not yet propagated and the install fails.

## Notes

- Recovery today is manual: "Re-run failed jobs" on the failed Release run
  (the re-run keeps `semantic-release`'s outputs, `skip-existing: true`
  absorbs the duplicate TestPyPI upload, and by then the index has
  propagated).
- Likely fix: wrap the `pip install` in a retry loop with backoff (e.g.
  up to ~5 minutes), or poll `https://test.pypi.org/pypi/plcc-ng/json`
  for the version before attempting the install.
- Related: issue 134 (recovery path when publish fails after tagging) —
  this flake is currently the most likely way to end up in that state.
