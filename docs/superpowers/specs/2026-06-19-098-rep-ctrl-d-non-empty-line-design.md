# 098 — ^D on a non-empty line requires a second ^D

**Issue:** [dev-docs/issues/098-rep-ctrl-d-non-empty-line.md](../../../dev-docs/issues/098-rep-ctrl-d-non-empty-line.md)
**Date:** 2026-06-19
**Type:** fix

## Summary

Pressing ^D while text is typed but not yet submitted requires a second ^D before `plcc-rep` processes the input. This is a regression introduced in issue 093, which replaced `read1(65536)` with `readline()` in `SourceRunner._read_line`. The fix restores `read1(65536)`.

## Root Cause

In canonical (cooked) TTY mode, pressing ^D on a non-empty line causes the OS to flush the buffered content to the process in a single `read()` call — without a trailing newline. Python's `readline()` sees no newline and calls `read()` again, blocking until a second ^D arrives. `read1(N)` makes exactly one underlying OS `read()` call and returns immediately, so the first ^D delivers the partial line and processing happens right away.

The 093 spec incorrectly stated that `readline()` "already returns a partial line (no trailing newline) when the user presses ^D after typing without Enter." Issue 098 is the empirical correction.

## Change

One line in `src/plcc/cmd/source_runner.py`, inside `SourceRunner._read_line`:

```python
# before (093 regression)
return sys.stdin.buffer.readline()

# after
return sys.stdin.buffer.read1(65536)
```

No other code changes. The rest of `_process_line` already handles all cases correctly:

| `read1` result | Meaning | `_process_line` path |
|---|---|---|
| `b"hello\n"` | User pressed Enter | `_incremental` |
| `b"hello"` (no `\n`) | User pressed ^D on non-empty line | `_force_submit(buffer + line)` |
| `b""` | User pressed ^D on empty line | `_ctrl_d` → exit or force-submit buffer |

The 65536-byte buffer is the same value the pre-093 `read1` call used. In canonical mode the OS delivers at most MAX_CANON bytes (~4096) per `read()`, so the buffer size is not a practical constraint.

## Testing

- Verify the existing test `test_partial_line_then_ctrl_d_force_submits_with_partial` in `src/plcc/cmd/source_runner_test.py` passes (it covers this exact scenario and likely fails today due to the regression).
- If that test passes already (due to mock behavior), add a focused test that simulates a partial-line ^D: `read1` returns `b"hello"` (no newline) → `_force_submit` is called with `b"hello"` and `eof=True`.

## Out of scope

- Changes to `_ctrl_d`, `_force_submit`, `_incremental`, or any other `SourceRunner` method.
- Changes to `RepHandler`, `ParseHandler`, or the pipeline.
- Any grammar, spec, or docs changes.
