# 018 - ^D exit does not print a newline, leaving the shell prompt mid-line

**Type:** fix
**Date:** 2026-05-14

## Description

When the user presses ^D to exit an interactive session, the shell exits without
printing a newline. The terminal's next prompt therefore appears on the same
line as the last prompt that was displayed, producing output like:

```
>>> $
```

When the user presses ^C to exit (on an empty buffer), a newline is printed
first, so the shell prompt appears at the beginning of the next line:

```
>>>
$
```

^D should produce the same clean exit as ^C.

## Steps to Reproduce

1. Start an interactive session (`plcc-rep` or equivalent).
2. At the `>>> ` prompt, press ^D.

**Expected:** a newline is printed and the shell prompt appears at the start of
the next line.

**Actual:** the shell prompt follows `>>> ` on the same line.

## Notes

The fix is a one-liner in `SourceRunner._run_interactive`
([src/plcc/cmd/source_runner.py](../../src/plcc/cmd/source_runner.py)).
When `readline()` returns an empty bytes object (^D, line 52), add
`print(file=sys.stderr)` before the `break`. This mirrors the `print` already
emitted on line 43 for the ^C exit path.

Related to issue [013](013-ctrl-c-does-not-exit-interactive-shell.md),
which fixed ^C exit behavior. The newline on the ^C path was added as part of
that fix; the ^D path was not updated to match.
