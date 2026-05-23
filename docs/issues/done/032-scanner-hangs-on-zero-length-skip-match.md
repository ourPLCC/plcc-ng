# 032 - Scanner hangs when a skip pattern matches an empty string

**Type:** fix
**Date:** 2026-05-23

## Description

`plcc-scan` hangs indefinitely when a `skip` pattern can match an empty string (e.g., `\s*`) and the current character does not satisfy the pattern.

Example grammar:

```
skip WHITESPACE '\s*'
token NUM '\d+'
token PERIOD '\.'
%
<start> ::= <stuff>
<stuff>:Stuff1 ::= NUM <stuff>
<stuff>:Stuff2 ::= PERIOD
```

```
$ plcc-scan
>>> 2
^C   (must kill manually — hangs)
```

## Steps to Reproduce

1. Write a grammar with `skip WHITESPACE '\s*'`.
2. Run `plcc-make && plcc-scan`.
3. Enter any non-whitespace token (e.g., `2`).
4. Observe that the scanner never returns and must be killed with Ctrl-C.

## Root Cause

In `scanner.py`, the scan loop advances `index` by `len(result.lexeme)`:

```python
index += len(result.lexeme)
```

In `matcher.py`, a skip pattern is accepted even when it matches an empty string. When `\s*` is tried at a non-whitespace position it matches `""`. The skip is first in the match list and is chosen as the result. `len("") == 0`, so `index` never advances — infinite loop.

## Notes

The original PLCC Java scanner (`Scan.java`) explicitly guards against this:

```java
int e = m.end();
if (e == start)
    continue; // empty match, so try next pattern
```

The fix belongs in `matcher.py` (or `scanner.py`): discard any match whose end position equals its start position, mirroring the original behavior.
