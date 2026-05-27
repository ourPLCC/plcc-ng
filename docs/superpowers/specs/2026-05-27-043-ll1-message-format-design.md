# Design: Issue 043 — LL(1) conflict message formatting

**Date:** 2026-05-27
**Issue:** [docs/issues/043-ll1-conflict-message-whitespace.md](../../issues/043-ll1-conflict-message-whitespace.md)

## Problem

The LL(1) conflict error output from `plcc-make` has two cosmetic issues:

1. The header line reads `plcc-make: error: grammar is not LL(1); see build/ll1.json`. The `see build/ll1.json` pointer is redundant — the conflict messages are now self-contained — and confusing to students.
2. No blank line separates the header from the first conflict block, or consecutive conflict blocks from each other, making dense output hard to scan.

`format_conflict_message` already produces correct internal formatting (indentation, blank lines within a block). No changes are needed there.

## Scope

- **In scope:** header line wording; blank lines between the header and conflict blocks; blank lines between multiple conflict blocks.
- **Out of scope:** column-aligning `::=` in the factoring tip; changes to `format_conflict_message`; left-recursion message formatting.

## Design

### Approach

All changes land in `_report_ll1_failure` in `make.py`. `format_conflict_message` is a pure formatter and remains unchanged.

### `src/plcc/cmd/make.py` — `_report_ll1_failure`

Remove the `path` parameter. Change the header. Print a blank line before each conflict block.

**Before:**
```python
def _report_ll1_failure(ll1, path):
    print(f"plcc-make: error: grammar is not LL(1); see {path}", file=sys.stderr)
    for conflict in ll1.get("conflicts", []):
        print(format_conflict_message(conflict), file=sys.stderr)
    for entry in ll1.get("left_recursion", []):
        cycle = entry.get("cycle", [])
        print(f"plcc-make: error: left-recursion cycle: {' -> '.join(cycle)}", file=sys.stderr)
```

**After:**
```python
def _report_ll1_failure(ll1):
    print("plcc-make: error: grammar is not LL(1)", file=sys.stderr)
    for conflict in ll1.get("conflicts", []):
        print("", file=sys.stderr)
        print(format_conflict_message(conflict), file=sys.stderr)
    for entry in ll1.get("left_recursion", []):
        cycle = entry.get("cycle", [])
        print(f"plcc-make: error: left-recursion cycle: {' -> '.join(cycle)}", file=sys.stderr)
```

Update the call site from `_report_ll1_failure(ll1, ll1_json)` to `_report_ll1_failure(ll1)`.

### `src/plcc/ll1/format_conflict_message.py`

No changes.

## Target output

**Single FIRST/FIRST conflict:**
```
plcc-make: error: grammar is not LL(1)

LL(1) conflict: <stmts> on lookahead IDENT

  All of these productions apply:
    <stmts> ::= IDENT ELSE
    <stmts> ::= IDENT IF

  This is a FIRST/FIRST conflict: all productions start with IDENT, so
  the parser cannot choose between them.

  Tip: left-factor the common prefix:
    <stmts> ::= IDENT <stmtsTail>
    <stmtsTail> ::= ELSE
    <stmtsTail> ::= IF
```

**Two conflicts:** each block is preceded by a blank line, so they are clearly delimited.

## Tests

### `src/plcc/cmd/make_test.py`

- **Update** `test_report_ll1_failure_prints_error_and_conflicts`: remove the `"build/ll1.json" in err` assertion; assert instead that the header line contains `"grammar is not LL(1)"` and does NOT contain `"see"` or `"ll1.json"`.
- **Add** `test_report_ll1_failure_no_path_in_header`: explicit assertion that `"see"` is absent from stderr.
- **Add** `test_report_ll1_failure_blank_line_before_conflict`: assert that a blank line (`\n\n`) appears between the header line and the conflict block.
- **Add** `test_report_ll1_failure_blank_line_between_conflicts`: call with two conflicts; assert that a blank line separates them.

### `src/plcc/ll1/format_conflict_message_test.py`

No changes.
