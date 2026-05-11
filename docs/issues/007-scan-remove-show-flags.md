# 007 - Remove --show-* flags from plcc-scan

**Type:** fix
**Date:** 2026-05-11

## Description

`plcc-scan` still exposes four granular flags — `--show-skips`, `--show-line`,
`--show-regex`, and `--show-attempts` — that were intended to be replaced by
`--trace` when that flag was introduced. They were not removed at that time and
are now dead surface area in the public interface.

Remove all four `--show-*` flags. `--trace` is the supported way to enable
detailed output.

## Notes

- `--trace` already implies all four flags (`show_skips or trace`, etc. in
  `scan.py`), so no tracing capability is lost.
- The flags appear in the docstring/usage, argument parsing, and the
  `any_enrichment` logic in `scan.py` — all need to be cleaned up.
- Bats tests that exercise `--show-skips`, `--show-line`, `--show-regex`, and
  `--show-attempts` directly will need to be removed or rewritten against
  `--trace`.
