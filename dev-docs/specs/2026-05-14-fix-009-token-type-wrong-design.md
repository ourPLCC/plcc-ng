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
terminal = re.fullmatch(r"[A-Z_][A-Z0-9_]*", name)
```

Two changes:
- Align with the lexical name grammar (`src/plcc/spec/lexical/Parser.py:41` uses `[A-Z_][A-Z0-9_]*`): allow a leading underscore, allow digits after the first character (e.g. `NUM1`), and allow a single-character name.
- `re.match` → `re.fullmatch` to anchor the entire string.

## Tests

Two new unit tests in `src/plcc/spec/syntax/parse_syntactic_spec_test.py`:

1. **`test_single_char_capturing_terminal`** — rule `<noun> ::= <A>` produces `CapturingTerminal("A")`. Direct regression test for the single-char bug.
2. **`test_single_char_capturing_terminal_with_altname`** — rule `<noun> ::= <A>:b` produces `CapturingTerminal("A", "b")`. Covers the alt-name path with a single-char token.
3. **`test_digit_containing_capturing_terminal`** — rule `<noun> ::= <NUM1>` produces `CapturingTerminal("NUM1")`. Covers digit-containing token names per the lexical name grammar.

No changes to `build_model_test.py` — the model builder is correct; the bug is entirely in upstream classification.

## Worktree

Work in `.worktrees/fix-009-token-type` per project convention.
