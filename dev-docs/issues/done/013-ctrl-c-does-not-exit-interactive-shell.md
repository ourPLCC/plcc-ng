# 013 - ^C does not exit the interactive shell

**Type:** fix
**Date:** 2026-05-14

## Description

Pressing ^C (Ctrl+C) in interactive mode (`plcc-rep`) does not exit the shell.
It clears the current input buffer and returns to the prompt instead.
Users expect ^C to exit, matching the convention of virtually every interactive
shell (Python, Ruby, Node, bash, etc.).

Additionally, depending on where ^C is pressed (e.g. while a subprocess is
running), a `KeyboardInterrupt` traceback may be printed — surprising and
confusing for users.

## Steps to Reproduce

1. Run `plcc-rep` with a valid grammar file.
2. At the `>>> ` prompt, press ^C.

**Expected:** the shell exits cleanly (exit code 130 by convention).

**Actual:** the buffer is cleared and the prompt reappears; no exit occurs.

## Notes

The `KeyboardInterrupt` is caught in `SourceRunner._run_interactive`
([src/plcc/cmd/source_runner.py:56](../../src/plcc/cmd/source_runner.py#L56))
and silently swallowed. The fix should re-raise (or `sys.exit(130)`) on the
first ^C, and suppress the Python traceback so the exit looks clean.

A common pattern is to print a short message (`^C`) and then exit, or to exit
silently — matching what Python's own REPL does (`KeyboardInterrupt` on an
empty line exits with a newline and no traceback).

Subprocess-level interrupts (e.g. `plcc-tokens`, `plcc-tree`) may also surface
tracebacks if ^C reaches them before the parent handles it; those should be
suppressed as well.
