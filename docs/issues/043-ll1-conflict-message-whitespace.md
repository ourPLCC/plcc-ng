# 043 - Improve the format of LL(1) conflict error messages

**Type:** fix
**Date:** 2026-05-27

## Description

The LL(1) conflict messages introduced in #036 are correct but dense. All sections
run together without blank lines, making them hard to scan quickly. Adding vertical
whitespace between the header, the production list, the conflict-type explanation,
and the tip would significantly improve readability.

### Current output (FIRST/FIRST)

```
plcc-make: error: grammar is not LL(1); see build/ll1.json
LL(1) conflict: <stmts> on lookahead IDENT
All of these productions apply:
<stmts> ::= <IDENT> ELSE
<stmts> ::= <IDENT> IF
This is a FIRST/FIRST conflict: all productions start with IDENT, so
the parser cannot choose between them.
Tip: left-factor the common prefix:
<stmts> ::= <IDENT> <stmtsTail>
<stmtsTail> ::= ELSE
<stmtsTail> ::= IF
```

### Current output (FIRST/FOLLOW)

```
plcc-make: error: grammar is not LL(1); see build/ll1.json
LL(1) conflict: <elsePart> on lookahead ELSE
All of these productions apply:
<elsePart> ::= ELSE <stmt>
<elsePart> ::=    (empty)
This is a FIRST/FOLLOW conflict: ELSE can start the non-empty production(s)
above, but also appears in the FOLLOW set of <elsePart>, making the empty
production ambiguous here.
Tip: look at the rule(s) that use <elsePart> — one of them places
ELSE in a position that follows <elsePart>, creating the ambiguity.
This often means the grammar is genuinely ambiguous (e.g., the
dangling-else problem) and must be restructured.
```

### Target output (FIRST/FIRST)

```
plcc-make: error: grammar is not LL(1); see build/ll1.json

LL(1) conflict: <stmts> on lookahead IDENT

  All of these productions apply:
    <stmts> ::= <IDENT> ELSE
    <stmts> ::= <IDENT> IF

  This is a FIRST/FIRST conflict: all productions start with IDENT, so
  the parser cannot choose between them.

  Tip: left-factor the common prefix:
    <stmts>     ::= <IDENT> <stmtsTail>
    <stmtsTail> ::= ELSE
    <stmtsTail> ::= IF
```

### Target output (FIRST/FOLLOW)

```
plcc-make: error: grammar is not LL(1); see build/ll1.json

LL(1) conflict: <elsePart> on lookahead ELSE

  All of these productions apply:
    <elsePart> ::= ELSE <stmt>
    <elsePart> ::=    (empty)

  This is a FIRST/FOLLOW conflict: ELSE can start the non-empty production(s)
  above, but also appears in the FOLLOW set of <elsePart>, making the empty
  production ambiguous here.

  Tip: look at the rule(s) that use <elsePart> — one of them places
  ELSE in a position that follows <elsePart>, creating the ambiguity.
  This often means the grammar is genuinely ambiguous (e.g., the
  dangling-else problem) and must be restructured.
```

## Notes

- A blank line before the `LL(1) conflict:` header visually separates it from the
  `plcc-make: error:` line when multiple conflicts are reported in sequence.
- Indenting the productions list and the explanation paragraphs ties them visually
  to the conflict header above.
- When multiple conflicts are reported, each block should be separated by a blank
  line so the boundaries between conflicts are immediately obvious.
