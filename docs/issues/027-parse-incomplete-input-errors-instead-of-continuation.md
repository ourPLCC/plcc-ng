# 027 - plcc-parse: incomplete input triggers errors instead of continuation prompt

**Type:** bug
**Date:** 2026-05-18

## Description

In interactive mode, when the user enters a partial expression that cannot yet be completed
(e.g. an operator with no right-hand operand), `plcc-parse` reports parse errors and returns
to the primary prompt instead of showing the continuation prompt `...` and waiting for more
input.

## Steps to Reproduce

Given this grammar:

```
skip WS '\s+'
token NUM '\d+'
token OP '[-*/+]'
%
<exp> ::= <NUM> <exp2>
<exp2>:Exp2More ::= <OP> <exp>
<exp2>:Exp2None ::=
```

Run `plcc-parse` interactively and enter:

```
>>> 23 +
```

**Actual output:**

```
{"stage": "plcc-parser-table", "time": 405185959589579, "event": "error", "severity": "error", "pos": {"file": "-", "line": 1, "column": 4}, "message": "unexpected 'eof', no production for 'exp'"}
{"stage": "plcc-parser-table", "time": 405185959745824, "event": "error", "severity": "error", "pos": {"file": "-", "line": 1, "column": 4}, "message": "unexpected 'OP', no production for 'exp'"}
-:1:4: error: unexpected 'eof', no production for 'exp'
-:1:4: error: unexpected 'OP', no production for 'exp'
>>>
```

**Expected output:**

```
>>> 23 +
...
```

## Notes

The parser sees `eof` at the end of the first line and treats the input as complete, failing
to recognize that `23 +` is a valid prefix of a longer expression. The interactive session
should instead detect that the parse could succeed with more input and issue a continuation
prompt.

Note also that the errors are reported twice — once as JSONL and once as plain text — without
`-v` specified. See issue 026.
