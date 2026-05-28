# Design: 039 — Level-2 errors to stdout

**Date:** 2026-05-28
**Issue:** [039](../../issues/039-level-2-errors-to-stdout.md)

## Problem

`plcc-parse` and `plcc-rep` print user-facing error messages (parse errors, scan errors,
interpreter/semantic errors) to stderr. `plcc-scan` already prints its errors to stdout but
does so with a plain `print()` call whose intent is invisible. The three commands should be
consistent, and the intent behind "this is a user-facing error, not a tool diagnostic" should
be encoded at every call site.

Students who redirect stdout to capture experiment results lose errors to an unredirected
stderr. They should not need to understand stream redirection to use these tools.

## Rule

> User-facing language errors (scan errors, parse errors, semantic/interpreter errors) go to
> **stdout**. Tool-level diagnostics (grammar file not found, subprocess failures, verbose
> events) go to **stderr**.

## Design

### New module: `cmd/output.py`

```python
def print_user_error(message):
    print(message)
```

The name encodes the distinction. Every call site that uses `print_user_error()` is
self-documenting: "this message is for the user about their language or input." Call sites
that use `print(..., file=sys.stderr)` are, by contrast, explicitly tool diagnostics. The
two forms remain visually distinct throughout the codebase.

### Call sites that change

**`pipeline.py` — `print_parse_error()`**

The final `print` calls `print_user_error()` instead of `print(..., file=sys.stderr)`. This
is the single fix point for parse/scan errors from both `plcc-parse` and `plcc-rep`.

**`rep.py` — `_render_record()`**

The `error` branch (interpreter/semantic errors returned by the student's language processor)
calls `print_user_error()` instead of `print(..., file=sys.stderr)`.

The other stderr calls in `rep.py` — "interpreter exited unexpectedly", "no semantic
sections", usage errors — are tool diagnostics and do not change.

**`scan.py` — `_render_record()`**

The `error` branch already prints to stdout. It is updated to call `print_user_error()` for
consistency. No behavioural change; the intent becomes explicit.

### Commands not in scope

`plcc-make` and `plcc-diagram` are left unchanged for this issue.

## Tests

### Unit tests

**`pipeline_test.py`:** Five tests for `print_parse_error()` currently assert on `err`
(stderr). They switch to assert on `out` (stdout). Test names are unchanged.

**`rep_test.py`:** Tests for parse/scan errors currently assert on `err`. They switch to
`out`. Tests that assert tool-failure messages on `err` (e.g., "interpreter exited
unexpectedly") are unchanged.

**New unit tests for `output.py`:** A small test file (`output_test.py`) confirms that
`print_user_error()` writes to stdout and not stderr.

### Bats tests

No bats changes are needed. Audit of `plcc-parse.bats`, `plcc-rep.bats`, and
`plcc-scan.bats` found no tests that assert user-facing parse/scan/semantic errors on
`$stderr`. The `$stderr` assertions that exist check tool-level messages (missing grammar
file, unknown tool name) which correctly stay on stderr.
