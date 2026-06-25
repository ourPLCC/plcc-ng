# 122 - `plcc-rep` with Python emitter produces object repr instead of expected value

**Type:** fix
**Date:** 2026-06-25

## Description

When using `plcc-rep` with Python-generated code, evaluating an expression returns the object's repr (e.g., `<Add.Add object at 0x104c64ec0>`) instead of the computed value. The Python semantics methods are not returning or printing the result correctly.

Additionally, a semantics block containing valid Java code (e.g., `return Integer.parseInt(integer.toString());`) was silently accepted during the build phase with no error, suggesting the Python emitter is not validating that semantics code is actually Python.

## Steps to Reproduce

1. Write a spec file with Python semantics for a simple arithmetic grammar.
2. Run `plcc-rep`.
3. Evaluate an expression such as `/+34 19 2`.
4. Observe: output is `<Add.Add object at 0x104c64ec0>` instead of the numeric result.

## Notes

- Two related problems may be present:
  1. The Python emitter's generated `__str__` or evaluation method is not invoking the user's semantics correctly.
  2. Java-style code in a Python semantics block is not rejected at build time.
- Investigate whether the generated Python code properly calls the user-defined method and whether the return value is surfaced to the REPL output.
- The board member noted: "plcc-rep with Python code is not yet ready" — this may be a known limitation rather than a recent regression.
