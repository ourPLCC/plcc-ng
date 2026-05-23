# ^D Handling Design

## Summary

Adjust `SourceRunner`'s interactive `^D` behavior in two ways:

1. **Empty prompt, empty buffer**: require two `^D` presses to exit. The first prints `(press ^D again to exit)` and re-shows the prompt; the second exits cleanly.
2. **`SubmitOn.EOF` mode** (used by `plcc-parse` and `plcc-rep`): Enter never evaluates — it only accumulates. `^D` is the sole submit trigger.

The non-empty-line `^D` path (`_is_partial_eof`) is unchanged: it already force-submits the buffer + partial line.

## Scope

All changes are confined to `src/plcc/cmd/source_runner.py` and its test file `src/plcc/cmd/source_runner_test.py`.

## State

Add `pending_exit: bool = False` to `_InteractiveState`:

```python
@dataclass
class _InteractiveState:
    buffer: bytes
    prompt: str
    done: bool = False
    pending_exit: bool = False
```

The flag resets automatically: any state transition that does not explicitly set `pending_exit=True` leaves it `False`. No instance variable is needed on `SourceRunner`.

## `_process_line` Changes

### Split the `_is_eof` branch

Current code handles empty-buffer and non-empty-buffer in `_exit_or_submit_accumulated_buffer`. Split into two paths:

```python
if self._is_eof(line):
    if state.buffer:
        return self._exit_or_submit_accumulated_buffer(handler, state)
    return self._warn_then_exit(state)
```

`_exit_or_submit_accumulated_buffer` retains its current behavior (submit buffer with `eof=True`, loop).

### `SubmitOn.EOF` becomes pure accumulation

Remove the `_attempt_first_line` call. All Enter presses accumulate:

```python
if self._submit_on == SubmitOn.EOF:
    return self._accumulate_only(line, state)
```

`_attempt_first_line` is deleted.

## New Method: `_warn_then_exit`

```python
def _warn_then_exit(self, state):
    print(file=sys.stderr)
    if state.pending_exit:
        return _InteractiveState(buffer=b"", prompt=self._prompt, done=True)
    print("(press ^D again to exit)", file=sys.stderr)
    return _InteractiveState(buffer=b"", prompt=self._prompt, pending_exit=True)
```

- **First `^D`**: prints a blank line (moves off the prompt), prints the warning, returns `pending_exit=True`. The loop prints the prompt on the next iteration.
- **Second `^D`**: prints a blank line, returns `done=True` — the same clean exit path already used by the loop.

## Error Handling

No new error conditions. The `pending_exit` path never calls `handler.feed`, so the handler's return value is irrelevant there.

## Testing

### Existing tests to update

- `test_ctrl_d_on_fresh_prompt_prints_newline`: currently asserts `err.endswith(">>> \n")`. Update to assert the warning message appears and the prompt is shown again. `_tty_stdin([b""])` already produces two empty reads from `BytesIO`, so the fixture needs no change — only the assertion.

### Existing tests unaffected

- `test_interactive_eof_with_empty_buffer_does_not_call_feed`: still passes — no feed is called. `_tty_stdin([b""])` gives two empty reads; first triggers warning, second exits.

### New tests

| Scenario | Assertion |
|---|---|
| First `^D` on empty prompt | `(press ^D again to exit)` appears in stderr; loop continues (second prompt shown) |
| Second `^D` on empty prompt | Exits cleanly; no feed called |
| Non-`^D` input after warning | `pending_exit` cleared; loop continues normally |
| `SubmitOn.EOF`, Enter on first line | No feed called; buffer accumulates |
| `SubmitOn.EOF`, Enter then `^D` | Feed called once with accumulated content |
