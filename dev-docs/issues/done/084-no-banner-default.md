# 084 - Make no-banner the default; print banner to stderr with -v

**Type:** feat
**Date:** 2026-06-08

## Description

Level 2 commands (`plcc-scan`, `plcc-parse`, `plcc-rep`, `plcc-make`) currently
print a version-and-grammar banner to stdout by default, with `--no-banner` to
suppress it. This pollutes stdout in scripted and piped workflows and forces
users to add `--no-banner` to get clean output.

## Desired Behavior

- Remove the banner from stdout entirely. Make no-banner the default.
- Remove the `--no-banner` option (no longer needed).
- When `-v` is passed, print the banner to **stderr** so it is visible during
  interactive use without contaminating stdout.

## Notes

This is a breaking change for users who rely on the banner appearing on stdout,
but stdout cleanliness is more important for composability. The banner on stderr
with `-v` preserves discoverability without the cost.
