# 026 - plcc-parse: errors reported twice when no `-v` specified

**Type:** bug
**Date:** 2026-05-18

## Description

When `plcc-parse` encounters an error without `-v`, the error is emitted twice: once as plain
text and once as a JSONL verbose event. The JSONL line should be suppressed when verbose mode
is not active.

## Steps to Reproduce

```bash
echo "bad input" | plcc-parse
```

Observe the error message appears as plain text followed by a `{"event":...}` JSONL line on
stderr.

## Notes

JSONL verbose events should only be emitted when `-v` is active. The fix likely involves
guarding the verbose event emission in the error path with a check on whether verbose mode is
enabled.
