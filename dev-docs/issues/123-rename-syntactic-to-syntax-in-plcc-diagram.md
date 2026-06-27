# 123 - Rename syntactic to syntax in plcc-diagram-* and output filenames

**Type:** refactor
**Date:** 2026-06-27

## Description

The `plcc-diagram-*` commands and the filenames they produce use the word "syntactic" (e.g. `syntactic-diagram`). This should be renamed to "syntax" for consistency and clarity.

## Notes

- Affects command names under `plcc-diagram-*` that include "syntactic"
- Affects the names of output files those commands produce
- A breaking change for users relying on the current output filenames
