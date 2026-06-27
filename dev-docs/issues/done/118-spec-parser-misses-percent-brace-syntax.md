# 118 - Spec parser silently accepts `%%{...%%}` instead of `%%%...%%%`, generates bad code

**Type:** fix
**Date:** 2026-06-25

## Description

When a user writes `%%{...%%}` (the old or incorrect delimiter syntax) instead of the correct `%%%...%%%` block delimiters, the spec parser does not report an error. Instead it silently generates malformed Java code — in the observed case a file literally named `%%{.java` — which then causes a downstream `FileNotFoundError`:

```text
FileNotFoundError: [Errno 2] No such file or directory: 'build/Java/    /**.java'
```

The user had no indication from the tool that their spec file contained invalid syntax.

## Steps to Reproduce

1. Write a spec file that uses `%%{` and `%%}` as block delimiters instead of `%%%`.
2. Run `plcc-rep` or the Java emitter against it.
3. Observe: no spec-parse error, but downstream `FileNotFoundError` or garbled output.

## Notes

- The spec parser should detect `%%{` / `%%}` and emit a clear error pointing to the offending line, e.g.: `error: unexpected '%%{' — did you mean '%%%'?`
- The Java emitter (or build step) should not be reachable with a malformed AST.
- Check whether other emitters (Python, Haskell, JavaScript) are equally affected.
