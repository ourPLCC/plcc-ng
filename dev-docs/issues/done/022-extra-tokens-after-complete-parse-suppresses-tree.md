# 022 - Extra tokens after a complete parse suppresses the tree

**Type:** fix
**Date:** 2026-05-14

## Description

When input contains a complete, valid program followed by extra tokens,
`plcc-parse` reports an error for the trailing tokens but does not print
the tree for the successfully parsed portion. The student loses the output
for input that was valid up to the extra tokens.

## Steps to Reproduce

Grammar:

```
skip WS '\s+'
token A 'a'
token AA 'aa'
token ID '\w+'
%
<prog> ::= <A> <AA> <ID>
```

Input:

```
a aa aaa aaaa
```

Actual output:

```
{"stage": "plcc-parser-table", ...  "message": "unexpected token 'ID' after complete parse at {'file': '-', 'line': 1, 'column': 10}"}
plcc-parser-table: error: unexpected token 'ID' after complete parse at {'file': '-', 'line': 1, 'column': 10}
```

Expected output: the tree for `a aa aaa` printed first, then the error for
the trailing `aaaa`:

```
prog
  A 'a' [-:1:1]
  AA 'aa' [-:1:3]
  ID 'aaa' [-:1:6]
plcc-parse: error: unexpected token 'ID' after complete parse at -:1:10
```

## Notes

- The parse itself succeeded; only the post-parse token check failed. The
  tree should be emitted before (or independently of) the trailing-token
  error.
- The error message format is also the unfriendly JSON output described in
  issue [019](019-parse-error-not-student-friendly.md).
- Related to issue [008](008-parse-multi-program-streaming.md), which proposes
  that `plcc-parse` should handle multiple programs in one input stream. The
  "unexpected token after complete parse" case may become a trigger for
  starting a second parse rather than an error, once issue 008 is implemented.
  The fix here should keep that future direction in mind.
