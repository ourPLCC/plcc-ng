# Fix 009 — Model generator emits token name as field type instead of Token

**Date:** 2026-05-14
**Issue:** docs/issues/009-model-generator-token-type-wrong.md
**Type:** fix

## Problem

Single-character uppercase token names (e.g. `A`) are misclassified as non-terminals during syntactic spec parsing. The regex in `_parseCapturing` uses `+` (one or more) for the second character class, so a one-character name never matches and falls through to `RhsNonTerminal`. Downstream, `build_model` treats non-terminals as class references and emits `"type": "A"` instead of `"type": "Token"`.

## Fix

In `src/plcc/spec/syntax/parse_syntactic_spec.py`, `_parseCapturing` (line 92):

```python
# before
terminal = re.match(r"[A-Z][A-Z_]+", name)

# after
terminal = re.fullmatch(r"[A-Z][A-Z_]*", name)
```

Two changes:
- `+` → `*` so a single uppercase character matches.
- `re.match` → `re.fullmatch` to anchor the entire string, making the invariant explicit and preventing accidental partial matches on names like `A123`.

## Tests

Two new unit tests in `src/plcc/spec/syntax/parse_syntactic_spec_test.py`:

1. **`test_single_char_capturing_terminal`** — rule `<noun> ::= <A>` produces `CapturingTerminal("A")`. This is the direct regression test for the bug.
2. **`test_single_char_capturing_terminal_with_altname`** — rule `<noun> ::= <A>:b` produces `CapturingTerminal("A", "b")`. Covers the alt-name path with a single-char token.

No changes to `build_model_test.py` — the model builder is correct; the bug is entirely in upstream classification.

## Worktree

Work in `.worktrees/fix-009-token-type` per project convention.
