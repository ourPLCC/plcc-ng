# Design: Make Banner Opt-In (Issue 084)

**Date:** 2026-06-15
**Issue:** [084](../../../dev-docs/issues/084-make-no-banner-the-default-print-banner-to-stderr-with-v.md)

## Problem

Level-2 commands (`plcc-scan`, `plcc-parse`, `plcc-rep`, `plcc-make`, `plcc-diagram`) currently print a version-and-grammar banner to stdout by default. This pollutes stdout in scripted and piped workflows. Users must pass `--no-banner` to suppress it.

## Decision

Replace the default-on, opt-out banner with a default-off, opt-in banner.

## Behavior

| Invocation | Banner output |
|---|---|
| No flag (default) | Nothing — stdout and stderr both clean |
| `--banner` / `-b` | Version + grammar lines printed to **stderr**, human-readable text only |
| `--no-banner` | Flag removed entirely |

The banner content is unchanged:
```
plcc-ng 0.41.0
grammar: /path/to/grammar.plcc
```
For `plcc-rep`, the "Running {tool} with {language}." line is also gated on `--banner`.

The banner always uses human-readable text format. `--verbose-format=json` has no effect on it.

## Orchestrator–Child Suppression

Orchestrators (`plcc-scan`, `plcc-parse`, `plcc-rep`, `plcc-diagram`) call `plcc-make` as a subprocess. Under the new design, orchestrators simply do not pass `--banner` to their children. Children are silent about the banner by default. No suppression flag is needed.

## Shared Library

`plcc/cmd/output.py` gains a `print_banner(version, grammar_path, tool=None, language=None)` function that:
- Always writes to `sys.stderr`
- Always formats as human-readable text
- Replaces the separate `print_version_line` + `print_grammar_line` calls at banner sites

Each level-2 command calls `print_banner(...)` once — after grammar resolution, before spawning any children — guarded by `if args["--banner"]`. The pre-`docopt` version-line print is removed (it existed only to show something on usage errors; with opt-in `--banner` that is no longer relevant).

## Testing

**Deleted:**
- All `--no-banner` unit tests
- All tests asserting the banner appears on stdout by default

**New unit tests (per command, `capsys`):**
- `--banner` prints version line to stderr
- `--banner` prints grammar line to stderr
- Default (no flag) prints nothing to stderr or stdout for the banner
- `--banner` output is human-readable text even when `--verbose-format=json` is passed

**New orchestrator unit tests (per orchestrator):**
- The subprocess call to `plcc-make` does not include `--banner`

**Bats command-tier tests:**
- Updated to match: `--banner` produces output on stderr; no flag produces nothing

## What Does Not Change

- The verbose event system (`-v`, `VerboseContext`, STARTED/PHASE/FINISHED events) is unaffected.
- All other stdout output from each command is unaffected.
- `print_version_line` and `print_grammar_line` helpers remain in `output.py` (used independently elsewhere).
