# 050 - Rename --grammar-file to --grammar in all commands

**Type:** refactor
**Date:** 2026-05-29

## Description

The flag `--grammar-file` is longer than necessary. `--grammar` is shorter, more
natural, and consistent with how similar tools name this option. Rename it across
all commands that accept it.

## Notes

- Affects all level-2 commands (`plcc-scan`, `plcc-parse`, `plcc-rep`) and any
  internal commands that accept `--grammar-file` (e.g. `plcc-make`).
- This is a breaking change for any scripts or workflows that use `--grammar-file`.
  Consider keeping `--grammar-file` as a deprecated alias for one release, or
  just making a clean break.
- First noted as a consideration in issue 046.
