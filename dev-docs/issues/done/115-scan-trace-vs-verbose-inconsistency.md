# 115 - Group help options into Output vs Diagnostics sections

**Type:** fix
**Date:** 2026-06-25

## Description

Users confuse `--trace` and `--verbose` because they appear as a flat list of options with no indication that they serve different purposes.

`--verbose` (`-v`) is a diagnostic volume knob. It writes structured information about a command's internal operations to stderr. Orchestrating tools use it to get machine-readable detail from low-level commands; it is not something end users normally reach for.

`--trace` and `--banner` are feature flags. They augment the user-facing output of a command with specific additional information the user has opted into.

`--verbose` is already consistent across all commands (via `VERBOSE_OPTIONS`). The issue is that nothing in the help text signals that these two groups of flags are different in kind.

## Notes

- Split the Options section in each command's docopt string into two named groups:
  - `Output:` — feature flags that change what the command shows (`--trace`, `--banner`)
  - `Diagnostics:` — verbose flags aimed at orchestrators and debuggers (`-v`, `--verbose-format`)
- Apply consistently to `plcc-scan`, `plcc-parse`, `plcc-rep`, and any other user-facing commands
- No flag renames needed; this is a help-text-only change
