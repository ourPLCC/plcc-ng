# Design: Group Help Options into Output vs Diagnostics Sections

**Issue:** 115
**Date:** 2026-06-29
**Status:** approved

## Problem

All user-facing plcc commands display a flat `Options:` section in `--help` output. This causes users to confuse `--verbose` (a diagnostics flag for orchestrators and debuggers) with `--trace` and `--banner` (output feature flags the end user opts into). Nothing in the help text signals that these two groups of flags are different in kind.

## Goal

Split each command's flat `Options:` section into up to three named sections so the distinction is self-evident from the help text. No flag renames. No behavior changes. Help-text only.

## Design

### Section structure

Each user-facing command's docopt string is restructured into three sections:

```
Options:
    -h --help       Show this message.
    [--spec]        (if applicable)
    [--through]     (make only — a control flag, not an output feature)

Output:
    -b --banner     Show the version and spec banner on stderr.
    -t --trace      Show detailed scanning output.  ← scan only

Diagnostics:
    -v              Increase verbosity (may repeat: -v, -vv, -vvv for levels 1-3).
    --verbose-format=FMT    Output format: text or json [default: text].
```

**Placement rules:**
- `Options:` — general/control flags: `-h/--help`, `--spec`, `--through`
- `Output:` — feature flags that augment user-facing output: `--banner`, `--trace`
- `Diagnostics:` — flags aimed at orchestrators and debuggers: `-v`, `--verbose-format`

### Change 1: `verbose.py`

Rename `VERBOSE_OPTIONS` → `DIAGNOSTICS_OPTIONS` and prepend the section header:

```python
DIAGNOSTICS_OPTIONS = """
Diagnostics:
    -v                      Increase verbosity (may repeat: -v, -vv, -vvv for levels 1-3).
    --verbose-format=FMT    Output format: text or json [default: text].
"""
```

### Change 2: Command docstrings (5 files)

Each command in `src/plcc/cmd/` updates its `__doc__` string:

- `scan.py` — `Output:` contains `--trace` and `--banner`
- `parse.py` — `Output:` contains `--banner` only
- `rep.py` — `Output:` contains `--banner` only
- `make.py` — `Output:` contains `--banner` only; `--through` stays in `Options:`
- `diagram.py` — `Output:` contains `--banner` only

All 5 update their import and docstring concatenation: `VERBOSE_OPTIONS` → `DIAGNOSTICS_OPTIONS`.

### Change 3: Tests

No new test cases needed — flags and behavior are unchanged. Existing tests that assert on `--help` output or docopt section structure must be updated to reflect the new section headers. Check both:

- `src/plcc/cmd/*_test.py` unit tests
- `tests/bats/commands/` bats tests

## Scope

- **In scope:** `src/plcc/cmd/` (scan, parse, rep, make, diagram) and `src/plcc/verbose.py`
- **Out of scope:** Lower-level CLI files (`tokens_cli.py`, `ll1_cli.py`, `model_cli.py`, etc.) — they are not user-facing commands in the same sense and are not mentioned in the issue
- **No flag renames, no behavior changes**
