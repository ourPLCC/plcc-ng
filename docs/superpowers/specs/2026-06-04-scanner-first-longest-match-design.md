# Scanner First-Longest-Match Design

**Date:** 2026-06-04
**Issue:** 056

## Problem

The scanner uses a two-phase algorithm: if any skip pattern matches at the current position, the first-declared skip wins immediately, regardless of length. Only when no skips match does longest-match apply, and only among tokens.

This gives skips categorical priority over tokens. A 1-character skip beats a 10-character token match at the same position. This diverges from how lexer generators like flex/lex work and adds conceptual surface area that serves no pedagogical purpose.

## Decision

Replace the two-phase algorithm with a single first-longest-match algorithm where skips and tokens compete together:

- All patterns (skips and tokens) are tried at the current position.
- The match with the longest lexeme wins.
- Ties are broken by declaration order — whichever rule appears first in the spec wins.

This is exactly how tokens already work among themselves. Skips are simply integrated into the same algorithm.

## Changes

### `src/plcc/scan/matcher.py`

Remove the skip-priority branch in `match()`:

```python
# Before
if isinstance(matches[0], Skip):
    result = matches[0]
else:
    result = self._getLongestMatch(self._removeSkips(matches))

# After
result = self._getLongestMatch(matches)
```

Delete `_removeSkips()`. No other production code changes — `_getLongestMatch` already implements first-longest-match with declaration-order tiebreaking via `max(..., key=lambda m: len(m.lexeme))`.

### `src/plcc/scan/matcher_test.py`

Four tests encode the old skip-priority behavior and are rewritten:

| Test | Change |
|---|---|
| `test_skip_wins_if_it_matches_before_any_token_rules` | Rename and invert: a longer token beats a shorter skip even when the skip is declared first. |
| `test_once_a_token_matches_subsequent_skip_are_ignored` | Rewrite: when a skip and token tie on length, declaration order decides regardless of type. |
| `test_match_mid_string` | Update the index=3 assertion: `NUMBER` wins with `123` instead of `ONE` winning with `1`. |
| `test_record_attempts_skip_win_includes_token_candidates` | Update comment: the skip still wins (declared first, same-length tie), but the reason is declaration-order tiebreaking, not skip short-circuiting. |

## Backward compatibility

All example grammars use whitespace skips (`\s+` or `\s*`) whose non-empty matches cannot overlap with token patterns (digits/symbols). No grammar relies on a skip preempting a longer token, so no existing grammar behavior changes.

## Invariants preserved

- Zero-length matches are still rejected.
- `record_attempts` still records all candidates and marks the winner.
- Declaration order still breaks ties — the rule is the same for skips and tokens.
