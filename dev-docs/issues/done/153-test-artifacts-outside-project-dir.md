# 153 - test-artifacts-outside-project-dir

**Type:** test
**Date:** 2026-07-07

## Description

A test run leaves a `plcc-ng/` directory (containing `spec.json`,
`model.json`, and per-language output) sitting in the project working
tree — a byproduct of `plcc-make`'s default build directory sharing the
project's own name (issue 125). `.gitignore` does not exclude `plcc-ng/`,
so it shows up as untracked and gets swept into commits if not
noticed.

Every test that invokes `plcc-make` (or the lower-level `plcc-spec` /
`plcc-model` / emit pipeline) should run it inside a directory created
outside the project — e.g. via `mktemp -d` and `cd`, as most of the
existing bats and pytest suites already do — rather than in the project
root or any path under it. Audit for any test that doesn't already do
this, and fix it.

## Notes

- Not a user-facing bug — `plcc-make`'s build-directory naming behaves
  as designed; this is purely test isolation. Classify as `test` or
  `chore`, not `fix`, so it doesn't spin the release version.
- Consider also gitignoring `plcc-ng/` at the project root as
  defense-in-depth, the same way `Java/`, `Python/`, and `languages/`
  are already ignored for the same reason.
