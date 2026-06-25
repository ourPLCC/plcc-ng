# 115 - `plcc-scan` uses `--trace` while `plcc-parse` and `plcc-rep` use `--verbose`

**Type:** fix
**Date:** 2026-06-25

## Description

`plcc-scan` exposes its diagnostic output under `--trace` / `-t`, but `plcc-parse` and `plcc-rep` expose equivalent diagnostic output under `--verbose` / `-v`. A user switching between commands has to remember two different flag names for the same concept.

## Notes

- Decide on one term and apply it consistently across all three commands.
- `--verbose` is the more conventional choice and matches `parse` and `rep`.
- If `--trace` is kept for scan (because "trace" more accurately describes what it shows), at minimum document the distinction clearly.
- Either way, the short flag should also be consistent (`-v` vs `-t`).
