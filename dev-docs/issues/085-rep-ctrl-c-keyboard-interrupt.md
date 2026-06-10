# 085 - plcc-rep prints KeyboardInterrupt stack trace on ^C

**Type:** fix
**Date:** 2026-06-08

## Description

Pressing ^C in `plcc-rep` prints a full Python stack trace instead of exiting
silently. This is confusing and alarming for students.

## Steps to Reproduce

```bash
plcc-rep -g g.plcc
# at the >>> prompt, press ^C
```

## Observed

```text
^C
Traceback (most recent call last):
  File "/path/to/build/sum/main.py", line 13, in <module>
    for line in sys.stdin:
                ^^^^^^^^^
KeyboardInterrupt
```

## Desired Behavior

^C exits `plcc-rep` silently (or with a brief "Interrupted." message), with no
stack trace and exit code 130 (the standard for SIGINT termination).

## Notes

The `KeyboardInterrupt` is raised inside generated user code (`main.py`), so the
fix likely belongs in the generated entry-point template — wrapping the main loop
in a `try/except KeyboardInterrupt: sys.exit(130)` — rather than in `plcc-rep`
itself.
