# 117 - `plcc-scan --trace` output is hard to read

**Type:** fix
**Date:** 2026-06-25

## Description

A user reported that the trace output from `plcc-scan --trace` is "a bit hard to read at first." We believe we worked out a readable format at some point — this issue is to verify that the current output still matches that design and, if not, restore or improve it.

## Notes

- Confirm what the current trace output looks like with a real spec file.
- Compare against any prior agreed-upon format (check git history / past issues).
- If the output has regressed or was never finalized, propose and implement a cleaner format.
- Related: issue #115 (trace vs verbose naming).
