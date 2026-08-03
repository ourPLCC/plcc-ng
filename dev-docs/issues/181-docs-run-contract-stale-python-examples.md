# 181 - Python examples in docs still use the pre-2.0.0 `_run()` print contract

**Type:** docs
**Date:** 2026-08-03

## Description

Every `=== "Python"` tabbed example in `docs/` implements `_run()` by printing
instead of returning. Under the 2.0.0 `_run()` contract (#162–#165) a `_run()`
that returns `None` is a `specification_error`, so all three examples exit 1.

The failure is easy to miss: the `print()` still reaches the terminal, so the
documented output appears above the error message. A reader following
`docs/quick-start.md` sees the right number and then a complaint about their
own spec.

Affected:

- `docs/quick-start.md` — `print(sum(...))`
- `docs/language-guide/index.md` — `print("Hello")`
- `docs/language-guide/examples.md` — `print(self.exp.eval())`

`docs/language-guide/semantic.md` has a matching prose bug: it says the default
`_run` implementation "prints a string representation of the parse tree root."
It returns it (`src/plcc/lang/ext/python/emit.py`). That page is the language
guide's conceptual home for `_run` and never states the return-a-string
contract at all.

The Java tab on each page is correct, and so are the four
`docs/language-guide/languages/*.md` reference pages, `docs/migration.md`,
`docs/whats-new.md`, and `docs/cli/guide/language-extensions.md`.

## Steps to Reproduce

1. Copy the Python tab of `docs/quick-start.md` into `spec.plcc`.
2. `echo "42 36 2" | plcc-rep`

```
80
Specification error: TypeError: _run() must return a string, got NoneType
Fix the errors in your specification and re-run.
```

Exit status is 1.

## Notes

`docs/language-guide/examples.md` needs more than a mechanical
`print(x)` → `return x` edit. `self.exp.eval()` returns an `int`, so the naive
fix trades one `specification_error` for another (`got int`). It needs
`return str(self.exp.eval())`, mirroring the Java tab's `String.valueOf(...)`.

Root cause is scope, not oversight. The 2.0.0 design doc
(`dev-docs/specs/2026-07-23-issues-162-165-run-contract-design.md`) enumerated
affected docs by hand and scoped `docs/quick-start.md` to "update the Java
example" — Java's `void _run()` could not compile, so it was the one that
announced itself. `language-guide/index.md` and `language-guide/examples.md`
were never listed. See #182 for the prevention side.
