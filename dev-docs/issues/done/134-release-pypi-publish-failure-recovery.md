# 134 - No recovery path when PyPI publish fails after tagging

**Type:** feat
**Date:** 2026-07-03

## Description

In `.github/workflows/release.yml`, `python-semantic-release` computes the next version from commits that are *unreleased* since the last tag. Once it tags `v{version}` and pushes the CHANGELOG commit, those commits are considered released — even if the downstream `publish` job (build → TestPyPI → smoke test → real PyPI) fails partway through, e.g. from a transient PyPI outage.

Re-running the release workflow (push or `workflow_dispatch`) afterward finds no new releasable commits, so `semantic-release` outputs `released: false` and the `publish` job is skipped again. There is currently no documented or automated way to retry publishing an already-tagged version to PyPI.

## Notes

- Found while writing the release SOP (issue 130).
- Possible approaches: a workflow_dispatch input for "republish this tag" that skips the semantic-release step and re-runs only the build/publish steps for a given existing tag; or building the wheel from the tag directly via a separate manual-trigger job.
- Related to issue 133 (docs deploy ordering) and issue 135 (skip-existing behavior on the real PyPI step).
