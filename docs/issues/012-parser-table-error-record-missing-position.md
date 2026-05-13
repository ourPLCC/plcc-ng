# 012 - plcc-parser-table error record missing source position

**Type:** enhancement
**Date:** 2026-05-13

## Description

When `plcc-parser-table` encounters a parse error it emits:

```json
{"kind": "error", "message": "...", "stage": "plcc-parser-table"}
```

The record has no source position (`file`, `line`, `column`). Downstream tools that display
parse errors (e.g. `plcc-parse`, `plcc-rep`) cannot point the user to the offending token.

## Desired behaviour

The error record should include a `source` field derived from the token that triggered the
parse error, matching the shape used by lex error records from `plcc-tokens`:

```json
{
  "kind": "error",
  "message": "...",
  "stage": "plcc-parser-table",
  "source": {"file": "...", "line": 1, "column": 5}
}
```

## Notes

Adding position requires `ParseError` (or `IncompleteInputError`) to carry the offending
token's source metadata. This is a non-trivial change to `predictive_parser.py`: the
exception currently holds only the message string. Deferred from the source-runner
refactor to keep that PR focused.
