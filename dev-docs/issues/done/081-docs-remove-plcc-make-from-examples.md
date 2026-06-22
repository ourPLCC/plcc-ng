# 081 - Rework examples to not use plcc-make

**Type:** docs
**Date:** 2026-06-07

## Description

Examples throughout the docs invoke `plcc-make` directly. Users should not need to call it by hand — the examples should reflect the correct, simplified workflow.

## Desired Behavior

Audit all examples in the docs and replace any direct `plcc-make` invocations with the appropriate commands users should actually run.

## Notes

Related to issue 074, which addresses the same problem in the quickstart specifically. This issue covers the broader audit of all other examples and pages in the docs.

See also: [[074-docs-simplify-quickstart]]
