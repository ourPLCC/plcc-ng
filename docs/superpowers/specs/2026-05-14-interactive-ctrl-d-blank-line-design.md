# Design: Interactive loop ^D and blank-line fixes (issues 018, 020, 021)

**Date:** 2026-05-14
**Branch:** fix/interactive-ctrl-d-blank-line
**Issues:** [018](../../issues/018-ctrl-d-exit-missing-newline.md), [020](../../issues/020-ctrl-d-behavior-in-continuation.md), [021](../../issues/021-blank-line-submit-silently-discards-incomplete-input.md)

---

## Summary

Three bugs in `SourceRunner._run_interactive` (`src/plcc/cmd/source_runner.py`) are fixed together because they all live in the same method and share the same state. The fix also refactors the method into a small family of single-purpose methods following clean code principles.

---

## Structure

A new `_InteractiveState` dataclass carries the loop's mutable state so each handler returns a new state rather than mutating variables in place:

```python
@dataclass
class _InteractiveState:
    buffer: bytes
    prompt: str
    done: bool = False
```

`_run_interactive` becomes a setup-and-loop with no conditionals. A `_process_line` dispatch table routes each line type to a dedicated handler. Predicate methods name the conditions.

```
_run_interactive
  _read_line                              I/O; converts KeyboardInterrupt to None
  _process_line                           pure dispatch table
    _is_interrupted                       line is None
    _is_eof                               not line
    _is_partial_eof                       not line.endswith(b"\n")
    _is_blank                             not line.strip()
    _clear_buffer_or_exit                 ^C handler
    _exit_or_submit_accumulated_buffer    ^D on empty line (fixes 018, 020)
    _force_submit_including_partial_line  ^D after partial text (fixes 020)
    _force_submit_accumulated_buffer      blank line (fixes 021)
    _accumulate_and_evaluate              normal line
```

---

## Behavior changes

### 018 — ^D exit missing newline

`_exit_or_submit_accumulated_buffer` prints a newline to stderr before doing anything else, matching the newline already printed on the ^C exit path.

### 020 — ^D behavior in continuation

`_exit_or_submit_accumulated_buffer` distinguishes two cases:
- **Fresh prompt** (empty buffer): print newline and exit — unchanged behavior.
- **In continuation** (non-empty buffer): print newline, submit buffer, reset to `>>>`, continue the loop.

`_force_submit_including_partial_line` handles ^D after partial text. When `readline()` returns bytes without a trailing `\n`, the partial bytes are appended to the buffer, submitted, and the session resets to `>>>`.

### 021 — Blank-line submission silently discards incomplete input

All three force-submit paths (blank line, ^D in continuation, ^D after partial text) call `_evaluate` with `eof=True`. If the handler returns `False`, `_evaluate` prints a PLCC internal error to stderr and exits with code 1. A well-behaved handler will always surface its own diagnostic before returning `False`; a handler that returns `False` silently on a forced submission is a PLCC bug, and the process exits rather than continuing in an inconsistent state.

---

## Testing

Existing tests covering ^C and normal-line paths remain unchanged.

New tests:

| Test | Covers |
|------|--------|
| `^D` on fresh prompt produces a newline in stderr | 018 |
| `^D` on empty continuation line submits buffer, returns to `>>>`, does not exit | 020a |
| `^D` after partial text appends partial text, submits, returns to `>>>` | 020b |
| Blank line force-submit exits with error when handler returns `False` | 021 |
| `^D` in continuation force-submit exits with error when handler returns `False` | 021 |
| `^D` after partial text force-submit exits with error when handler returns `False` | 021 |
| Blank line resets to `>>>` when handler accepts the submission | 021 |
| `_is_eof`, `_is_partial_eof`, `_is_blank`, `_is_interrupted` each return correct value | predicates |
