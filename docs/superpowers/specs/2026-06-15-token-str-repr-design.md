# Token `__str__` and `__repr__` — Design Spec

**Issue:** 086
**Date:** 2026-06-15

## Problem

The Python runtime `Token` class has no `__str__` or `__repr__` method. Users who write
`str(token)` or use a token in an f-string get the default object representation
(`<runtime.base.Token object at 0x...>`) rather than the lexeme.

Java's `Token.toString()` already returns the lexeme. This change brings Python to parity.

## Scope

Python runtime only. Java already has `toString()` returning `lexeme`. No template changes needed — `Token` is defined in the shared runtime, not emitted per-project.

## Design

Add `__str__` and `__repr__` to `Token` in `src/plcc/lang/ext/python/runtime/base.py`. Both return `self.lexeme`.

```python
class Token:
    def __init__(self, kind, lexeme):
        self.kind = kind
        self.lexeme = lexeme

    def __str__(self):
        return self.lexeme

    def __repr__(self):
        return self.lexeme
```

### Why both `__str__` and `__repr__`?

- `__str__` covers `str(token)`, `print(token)`, and f-string interpolation (`f"{token}"`).
- `__repr__` covers REPL output and `repr(token)`. Without it, bare token evaluation in a REPL still shows the object address.

### Why the same value for both?

The lexeme is the meaningful content of a token. There is no distinction between a "human-readable" and a "developer-repr" form that would justify different values.

## Tests

Two new tests in `src/plcc/lang/ext/python/runtime/base_test.py`:

- `test_token_str_returns_lexeme` — asserts `str(Token('NUM', '42')) == '42'`
- `test_token_repr_returns_lexeme` — asserts `repr(Token('NUM', '42')) == '42'`

## Files Changed

| File | Change |
|------|--------|
| `src/plcc/lang/ext/python/runtime/base.py` | Add `__str__` and `__repr__` to `Token` |
| `src/plcc/lang/ext/python/runtime/base_test.py` | Add two tests |
