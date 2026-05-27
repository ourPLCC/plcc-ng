# 044 - Syntax error caret points to wrong column

**Type:** fix
**Date:** 2026-05-26

## Description

The `^` in a syntax error message points to the beginning of the line instead of the column where the error was detected.

```
grammar.plcc:23:7: syntax error
<stmt>Assign     ::= <IDENT> ASSGN <expr>
^
```

The error is reported at column 7, but `^` appears under column 1. It should appear under column 7:

```
grammar.plcc:23:7: syntax error
<stmt>Assign     ::= <IDENT> ASSGN <expr>
      ^
```

## Steps to Reproduce

1. Create a grammar file with a syntactic spec line that has a syntax error past column 1.
2. Run `plcc-rep` (or any command that processes the grammar).
3. Observe that `^` appears at the start of the line regardless of the reported column number.

## Notes

- The column number in the `filename:line:col:` header appears to be correct; only the visual indicator is misaligned.
- Fix should pad `^` with `col - 1` spaces using the column from the error location.
