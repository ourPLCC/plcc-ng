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

Root cause confirmed: `src/plcc/lang/ext/python/templates/main.py.jinja`
builds the result record with
`repr(result) if result is not None else None`. `repr("hello")` is
`"'hello'"`, hence the quoting.

Checked the other three targets for the same "return value converted to
a string" contract the docs describe:

- **JavaScript** (`src/plcc/lang/ext/javascript/templates/main.js.jinja`):
  uses `String(result)` — plain conversion, matches its docs.
- **Haskell** (`src/plcc/lang/ext/haskell/emit.py`, `_write_main`):
  `_run` returns a `String`, which Aeson's `.=` encodes as a proper
  JSON string — matches its docs.
- **Java**: uses a different contract entirely (void return, print
  directly inside `_run()`), not a return-and-convert model at all —
  tracked separately as [#165](../165-java-run-void-print-model-inconsistent.md).

Since JavaScript and Haskell already implement "return value converted
to a plain string" correctly, this resolves the either/or in the
original description: the fix is to bring Python's driver in line with
them (`str(result)` instead of `repr(result)`), not to redocument
`repr`-style quoting as intended behavior. Scope stays limited to
Python; the code lives in `main.py.jinja`, not in `docs/`.
