# Design: Remove plcc-make from Examples

**Issue:** 081
**Date:** 2026-06-22

## Problem

`docs/language-guide/examples.md` includes an explicit "Build" step that invokes `plcc-make -s subtract.plcc` directly. Users should not need to call `plcc-make` by hand — `plcc-scan`, `plcc-parse`, and `plcc-rep` each invoke it automatically.

## Decision

Remove the `### Build` section (heading, code block, and "Exits silently on success." line) from `docs/language-guide/examples.md`. No other files are changed.

## Result

The example flow becomes: define the language, then run `plcc-scan`, `plcc-parse`, and `plcc-rep`. Each command builds implicitly. This matches the pattern in `quick-start.md`.

## Out of Scope

- `docs/cli/guide/under-the-hood.md` — references to `plcc-make` are intentional; that page explains the internal architecture.
- `docs/cli/guide/language-extensions.md` — explanatory parenthetical; intentional.
- `docs/cli/commands/plcc-make.md` — command reference page for `plcc-make` itself.
