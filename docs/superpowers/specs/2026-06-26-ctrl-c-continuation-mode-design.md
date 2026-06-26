# Design: ^C always exits in interactive mode (issue #119)

**Date:** 2026-06-26
**Status:** Approved

## Problem

When a user presses `^C` in continuation mode (`...` prompt), the REPL clears the
buffer and loops back to `>>>` instead of exiting. Users expect `^C` to terminate
the program immediately.

Trace of current (bad) behavior:
```
>>> 23
... ^C
KeyboardInterrupt
>>> ^C
$
```

`^C` in continuation mode silently swallowed the interrupt and printed
"KeyboardInterrupt" before looping. A second `^C` was required to actually exit.

## Desired behavior

`^C` exits with code 130 at any point in the interactive loop — top-level prompt or
continuation prompt — with no distinction based on buffer state. A trailing newline
is printed to keep the terminal tidy.

```
>>> 23
... ^C
$
```

## Affected component

`SourceRunner` in `src/plcc/cmd/source_runner.py`. It is shared by all interactive
commands (`plcc-parse`, `plcc-rep`, and any future commands that use it), so the
fix applies everywhere at once.

## Code change

`_clear_buffer_or_exit` currently has two branches:
- non-empty buffer → print "KeyboardInterrupt", clear buffer, return to `>>>`
- empty buffer → `sys.exit(130)`

Both branches become the same: print a newline and `sys.exit(130)`. The method is
renamed `_handle_interrupt` since it no longer conditionally clears anything.

```python
# Before
def _clear_buffer_or_exit(self, state):
    print(file=sys.stderr)
    if state.buffer:
        print("KeyboardInterrupt", file=sys.stderr)
        return _InteractiveState(buffer=b"", prompt=self._prompt)
    sys.exit(130)

# After
def _handle_interrupt(self):
    print(file=sys.stderr)
    sys.exit(130)
```

The call site in `_process_line` is updated to match the new name and signature.

## Test changes

`test_ctrl_c_with_buffer_clears_and_continues` currently asserts that `^C` with a
non-empty buffer prints "KeyboardInterrupt" and continues. This test is replaced by
`test_ctrl_c_with_buffer_exits_130`, which asserts exit code 130 — matching the
existing `test_ctrl_c_with_empty_buffer_exits_130`. The two cases can be expressed
as a single parametrized test.

No other test tiers (commands, integration, e2e) need changes: the interactive
behavior tested here is fully covered at the unit level.

## Out of scope

- Behavior of `^C` during evaluation (`_evaluate` already exits 130 — no change).
- Non-interactive (piped/file) stdin — `KeyboardInterrupt` there already exits 130.
- Any change to `^D` (EOF) behavior.
