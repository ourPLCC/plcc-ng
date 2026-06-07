# 017 - plcc-tokens: unrecognized-character error omits the character and its position

**Type:** fix
**Date:** 2026-05-14

## Description

When `plcc-tokens` encounters a character that matches no rule it emits:

```
plcc-tokens: error: unrecognized character
```

The message does not say which character was unrecognized, nor where in the
source it appeared (file, line, column). This makes it difficult to locate
and fix the offending input.

## Desired behaviour

The error should identify the character and its source position, for example:

```
plcc-tokens: error: unrecognized character '@' at file.txt:12:5
```

Or, if errors are emitted as structured JSON records (consistent with the rest
of the pipeline), the record should include both a human-readable `message`
and a `source` field:

```json
{
  "kind": "error",
  "message": "unrecognized character '@'",
  "stage": "plcc-tokens",
  "source": {"file": "file.txt", "line": 12, "column": 5}
}
```

## Notes

- Related to issue [012](012-parser-table-error-record-missing-position.md),
  which addresses missing source position in `plcc-parser-table` error records.
  Both issues follow the same pattern — a pipeline stage emits an error without
  enough diagnostic detail — but the fixes are independent: they live in
  different stages and likely in different source files.
- The scanner already tracks position to produce token records; the position
  information should be available at the point the unrecognized character is
  detected.
