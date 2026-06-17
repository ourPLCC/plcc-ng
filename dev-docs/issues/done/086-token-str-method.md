# 086 - Token should have a string conversion method returning its lexeme

**Type:** feat
**Date:** 2026-06-08

## Description

The generated `Token` class in both the Python and Java emitters has no
string conversion method. Users who write `str(token)` (Python) or
`token.toString()` (Java) in their semantic code get the default object
representation rather than the token's lexeme, which is almost always
what they want.

## Desired Behavior

- **Python emitter:** `Token.__str__(self)` returns `self.lexeme`.
- **Java emitter:** `Token.toString()` returns the lexeme string.

This allows natural string interpolation in semantic code:

```python
# Python — after this change
print(f"Got token: {self.num}")   # prints the lexeme, not <Token object at 0x...>
```

```java
// Java — after this change
System.out.println("Got token: " + num);  // prints the lexeme
```

## Notes

The lexeme is already accessible via `token.lexeme` (Python) and
`token.lexeme()` or similar (Java — verify exact field name). The string
conversion methods are convenience wrappers that follow each language's
idiomatic protocol for "print this as a string."
