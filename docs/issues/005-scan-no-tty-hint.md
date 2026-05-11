# 005 - plcc-scan does not display ^D hint for interactive sessions

**Type:** fix
**Date:** 2026-05-11

## Description

When `plcc-scan` is run interactively (stdin is a TTY) with no source file
arguments, it reads from stdin but gives no indication that it is waiting for
input or how to signal end-of-input. The user is left staring at a blank
prompt with no hint to press `^D`.

The existing bats test `plcc-scan TTY hint absent when stdin is not a TTY`
confirms the negative case is already expected, but the positive case — printing
a hint when stdin *is* a TTY — is not yet implemented.

## Steps to Reproduce

1. Run `plcc-scan` in a terminal (stdin is a TTY, no source file arguments).
2. Observe: no prompt or hint is displayed.
3. Expected: a message such as `press ^D when done` (or similar) is printed to
   stderr so the user knows the command is waiting for input.

## Notes

- Testing inside a Docker container: `docker exec -it` gives a TTY, so the
  fix should work in that environment too.
- The hint should go to stderr and must be absent when stdin is not a TTY
  (the existing test already guards that).
- `sys.stdin.isatty()` is the standard way to detect this in Python.
