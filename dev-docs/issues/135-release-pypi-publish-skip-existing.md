# 135 - Real PyPI publish step lacks skip-existing, unlike TestPyPI

**Type:** fix
**Date:** 2026-07-03

## Description

In `.github/workflows/release.yml`, the "Publish to TestPyPI" step sets `skip-existing: true`, so re-running it against a version already on TestPyPI succeeds as a no-op. The "Publish to PyPI" step has no `with:` block at all, so a rerun against a version already published to real PyPI fails hard (PyPI rejects re-uploading an existing file) instead of skipping gracefully.

This is a minor inconsistency on its own, but it compounds issue 134 (no recovery path for a failed publish): any retry mechanism built for that issue needs the real-PyPI step to tolerate "already published" without erroring.

## Notes

- Found while writing the release SOP (issue 130).
- Straightforward fix: add `skip-existing: true` to the "Publish to PyPI" step's `with:` block, matching the TestPyPI step.
