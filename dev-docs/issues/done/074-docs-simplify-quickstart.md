# 074 - Simplify the quickstart and fix its sample output

**Type:** docs
**Date:** 2026-06-07

## Description

The quickstart has two problems:

1. It tells users to run `plcc-make` directly, which is unnecessary — users should not need to invoke it by hand.
2. The sample output shown in the quickstart is inaccurate and does not match what the tool actually produces.

## Desired Behavior

- Remove the `plcc-make` step (or replace it with whatever the correct simplified flow is).
- Replace all sample output blocks with real, verified output copied from an actual run.

## Notes

When fixing the output, run the quickstart steps from scratch in a clean environment to capture genuine output rather than editing by hand.
