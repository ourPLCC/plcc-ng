# 162 - Python `_run()` docs show plain string return, but plcc-rep prints it quoted

**Type:** docs
**Date:** 2026-07-23

## Description

The Python quick-start example (`docs/quick-start.md`) shows `_run()`
returning a plain string via `'\n'.join(...)`, and the language guide
(`docs/language-guide/languages/python.md`) documents: "The return value
is converted to a string and printed by `plcc-rep`." In practice,
returning a plain `str` from `_run()` prints it wrapped in quotes (e.g.
`'hello'` instead of `hello`) instead of the plain string the docs show.

## Steps to Reproduce

1. `spec.plcc`:
   ```
   skip WHITESPACE '\s+'
   token NUM '\d+'
   %
   <Prog> **= <NUM>
   %
   Python

   Prog
   %%%
   def _run(self):
       return "hello"
   %%%
   ```
2. `echo "1 2 3" | plcc-rep`
3. Actual: `'hello'`. Expected per docs: `hello`.

Using `print(...)` instead of `return` inside `_run()` avoids the issue
entirely (confirmed).

## Notes

Originally filed as issue #3 in `ourPLCC/languages-ng`
(`dev-docs/issues/003-python-run-return-value-quoted.md`), found while
validating a phase-0/phase-1 plan there. That repo now uses `print(...)`
everywhere for the Python target as a workaround rather than `return`.

Either the docs should be corrected to show the actual (quoted) behavior
of `return`-ing a string, or `plcc-rep`'s handling of `_run()`'s return
value should be changed to match the documented behavior.
