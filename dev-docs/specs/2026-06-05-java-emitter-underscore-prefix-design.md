# Design: Java Emitter Underscore Prefix (Issue 057)

**Date:** 2026-06-05

## Summary

Rename `$run` to `_run` in the Java emitter to match the Python emitter convention. The `$` sigil is unusual in Java; `_` is the established prefix for generated identifiers already used elsewhere (e.g., `_Start`, `_RULE_NAME`, `_FIELDS`).

## Changeset

All five occurrences of `$run` become `_run`. This is a breaking change for any Java grammar that previously defined `public void $run()` — those grammars must be updated to define `public void _run()` instead. The reflection mechanism in `Main.java` is unchanged; it still calls the method named by `entry_point`, which is sourced from `_DEFAULT_ENTRY_POINT`.

| File | Change |
|------|--------|
| `src/plcc/lang/ext/java/emit.py:25` | `_DEFAULT_ENTRY_POINT = '$run'` → `'_run'` |
| `src/plcc/lang/ext/java/emit.py:29` | `public void $run()` → `public void _run()` in `_START_JAVA` |
| `src/plcc/lang/ext/java/emit_test.py:27` | Body fragment test data `$run` → `_run` |
| `tests/fixtures/trivial-java.plcc:8` | User-defined method `$run()` → `_run()` |
| `tests/bats/integration/java-emit.bats:42` | Test name string updated to reference `_run()` |

## Done When

`bin/test/` passes clean. No `_DEFAULT_ENTRY_POINT = '$run'` or `public void $run()` remains in the Java emitter or its fixtures (the negative assertion `'$run' not in ...` in the unit test is expected and correct).
