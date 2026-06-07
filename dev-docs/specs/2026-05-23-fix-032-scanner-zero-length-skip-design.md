# Fix 032: Scanner hangs on zero-length skip match

**Date:** 2026-05-23
**Issue:** 032 — Scanner hangs when a skip pattern matches an empty string
**Branch:** fix-scanner-empty-match

## Problem

`plcc-scan` hangs indefinitely when a `skip` pattern can match the empty string (e.g., `\s*`) and the current input position does not satisfy the pattern. The regex matches `""`, the skip is selected as the winner, and `scanner.py` advances `index` by `len("") == 0` — infinite loop.

## Fix

One guard in `matcher.py:_getMatches`, immediately after the regex match:

```python
if m.end() == index:   # discard zero-length matches
    continue
```

Zero-length matches are never added to the candidate list. If all candidates are filtered out, the existing `if not matches: return LexError(...)` path in `match` handles it naturally. No other production code changes.

This mirrors the original PLCC Java fix in `Scan.java`:

```java
int e = m.end();
if (e == start)
    continue; // empty match, so try next pattern
```

## Tests

### `matcher_test.py` — two new unit tests

- `test_skip_zero_length_match_is_lex_error`: matcher with `skip WS '\s*'` at a non-whitespace position returns `LexError`, not an empty `Skip`.
- `test_token_zero_length_match_is_lex_error`: matcher with `token NUM '\d*'` at a non-digit position returns `LexError`, not an empty `Token`.

### `scanner_test.py` — one new integration test

- `test_scanner_does_not_hang_on_zero_length_skip`: real `Matcher` built from `skip WS '\s*'\ntoken NUM '\d+'`, scans `"2"`, asserts a single `NUM` token result.

### Bats commands-tier fixture

A fixture grammar matching the issue's reproduction case:

```plcc
skip WHITESPACE '\s*'
token NUM '\d+'
token PERIOD '\.'
```

A `plcc-scan` bats test in `tests/bats/commands/` feeds `2` and asserts a clean `NUM` token output — the exact hang scenario from the issue. Commands tier is correct because a single installed command (`plcc-scan`) is exercised against a fixture.

## Files changed

| File | Change |
| --- | --- |
| `src/plcc/scan/matcher.py` | Add zero-length guard in `_getMatches` |
| `src/plcc/scan/matcher_test.py` | Two new unit tests |
| `src/plcc/scan/scanner_test.py` | One new integration test |
| `tests/bats/` | New fixture + bats test for the issue reproduction case |
