# 025 - Interactive shell should attempt to process first line before entering continuation mode

**Type:** feat
**Date:** 2026-05-17

## Description

When not in continuation mode, the interactive shell (`>>>` prompt) should attempt
to process the first line of input immediately. If that line produces a result, it
is displayed and the shell returns to `>>>`. If it does not produce a result, the
shell enters continuation mode (`...`) and accumulates further input until the user
signals end-of-input with `^D`, at which point the accumulated input is processed.

## Motivation

Currently, users must press `^D` to submit any input, even a single self-contained
line. This creates unnecessary friction when testing small snippets that fit on one
line.

It also creates an inconsistency with `plcc-scan`, which processes each line
immediately because newline is its input terminal character. For `plcc-parse` and
`plcc-rep`, EOF (`^D`) is the terminal character. The proposed behavior bridges
this gap: the first line (`>>>`) always attempts immediate processing, so
single-line inputs work without `^D`, while multi-line inputs naturally fall into
continuation mode (`...`) where `^D` is clearly the signal to submit. Users get
a visual cue from the prompt itself about when `^D` is needed.

## Expected Behavior

```
>>> 1 + 2
3
>>> 1 +
... 2
... ^D
3
>>>
```

- `>>>` prompt: submit the line and attempt processing; if successful, display
  result and return to `>>>`. If not, enter continuation mode.
- `...` prompt: accumulate lines until `^D`, then process the full accumulated
  input.

## Notes

- "Does not produce a result" means the tool exited with no output (the current
  signal for "need more input"). The existing continuation logic applies unchanged
  once the shell enters `...` mode.
- This only affects the `>>>` → attempt → `...` transition. Behavior once in
  continuation mode is unchanged.
- Related to issues [016](016-interactive-session-drops-whitespace-only-lines.md)
  and [done/020](done/020-ctrl-d-behavior-in-continuation.md).
