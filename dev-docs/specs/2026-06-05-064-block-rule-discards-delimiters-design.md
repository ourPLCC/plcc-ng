# Design: Issue 064 — Block rules discard opening/closing delimiters

**Date:** 2026-06-05
**Issue:** [064-block-rule-discards-delimiters](../../issues/064-block-rule-discards-delimiters.md)

## Problem

When a block token or skip rule matches, the lexeme includes only the content between the delimiters — the opening and closing patterns are stripped. They should be included, consistent with how non-block tokens work (where `match.group()` is the full matched text).

## Root Cause

`Scanner._scanBlock` in `src/plcc/scan/scanner.py` has the opening delimiter in `opened.lexeme` and the closing delimiter in `m.group()`, but neither is included when assembling the lexeme/buffer passed to `make_block_result`.

## Fix

Three lines change in `_scanBlock`. No other production code changes.

**Same-line case:**
```python
# before
lexeme = line.string[start:m.start()]
# after
lexeme = opened.lexeme + line.string[start:m.start()] + m.group()
```

**Multi-line case (two lines):**
```python
# before
buffer = line.string[start:]
...
buffer += next_line.string[:m.start()]
# after
buffer = opened.lexeme + line.string[start:]
...
buffer += next_line.string[:m.start()] + m.group()
```

## Tests

Four existing tests in `src/plcc/scan/scanner_test.py` assert the buggy behavior and must be updated:

| Test | Old expected lexeme | New expected lexeme |
|---|---|---|
| `test_block_token_single_line` | `'hello'` | `'<<<hello>>>'` |
| `test_block_token_multi_line` | `'line1\nline2\n'` | `'<<<line1\nline2\n>>>'` |
| `test_block_skip_emits_Skip` | `' hello '` | `'/* hello */'` |
| `test_block_token_multi_line_no_doubled_newlines` | `'line1\nline2\n'` | `'<<<line1\nline2\n>>>'` |

One new test covers the multi-line block token case with correct delimiter-inclusive expectations explicitly.

## Scope

- `src/plcc/scan/scanner.py` — 3 lines changed in `_scanBlock`
- `src/plcc/scan/scanner_test.py` — 4 tests updated, 1 test added

No changes to `TokenRule`, `SkipRule`, `BlockOpened`, `make_block_result`, or any other file.
