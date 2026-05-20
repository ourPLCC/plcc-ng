# 029 - plcc-rep: ^C shows an error instead of exiting silently

**Type:** fix
**Date:** 2026-05-20

## Description

Pressing `^C` in an interactive `plcc-rep` session displays an error message (and possibly a Python traceback) instead of exiting silently. `plcc-scan` and `plcc-parse` handle `^C` cleanly.

## Steps to Reproduce

1. Start an interactive `plcc-rep` session.
2. Type some input and press Enter (so the interpreter is evaluating).
3. Press `^C`.

Expected: exits silently (exit code 130).
Observed: prints something like `plcc-rep: interpreter exited unexpectedly` to stderr, exits with a non-130 code, or shows a Python traceback.

## Notes

`plcc-rep` keeps a long-lived interpreter subprocess open (via `subprocess.Popen`) for the entire session. When `^C` is pressed, the terminal sends SIGINT to the entire foreground process group, killing both the parent and the interpreter subprocess.

The `SourceRunner` machinery (`_read_line`, `_evaluate`) already catches `KeyboardInterrupt` and calls `sys.exit(130)`. But if `^C` arrives while `_read_response` is blocking on `interpreter.stdout.readline()`, the interpreter dies first. Python restarts the interrupted `readline()` (EINTR handling), which then returns `b""` because the child's stdout is now closed. `_read_response` treats an empty read as "interpreter exited unexpectedly" and calls `sys.exit(1)` — bypassing the clean exit path.

`plcc-scan` and `plcc-parse` are unaffected because they do not block on a long-lived subprocess stdout during interactive input.

Fix: in `_read_response` (or `RepHandler.feed`), detect that the interpreter exited with a signal (check `interpreter.poll()` for a negative or 130 return code) and exit cleanly (`sys.exit(130)`) rather than reporting an unexpected error.
