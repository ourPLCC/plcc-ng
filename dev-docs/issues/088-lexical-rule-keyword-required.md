# 088 - Make `token` or `skip` required in lexical rules

**Type:** feat
**Date:** 2026-06-08

## Description

Lexical rules should require an explicit `token` or `skip` keyword. Rules
without either keyword should be a syntax error.

## Desired Behavior

Valid:

```text
token NUM '\d+'
skip  SPACE '\s+'
```

Invalid (syntax error):

```text
NUM '\d+'
```

## Rationale

Requiring an explicit keyword makes the intent of each rule unambiguous and
improves readability. It also makes the grammar file format easier to parse
and to explain to students.
