# 057 - java-emitter-underscore-prefix

**Type:** enhancement
**Date:** 2026-06-01

## Description

The Java emitter uses `$run` as the default entry point method name and in the `_Start.java` template, while the Python emitter uses `_run`. Both emitters already use `_Start` as the base class name. The Java emitter should use `_run` to match the Python convention.

Affected locations in `src/plcc/lang/ext/java/emit.py`:
- `_DEFAULT_ENTRY_POINT = '$run'` (line 25)
- `public void $run()` in `_START_JAVA` (line 29)

## Notes

The Python emitter (`src/plcc/lang/ext/python/emit.py`) uses `_run` throughout. Using `_` as the prefix convention for generated identifiers that users should not override makes the Java emitter consistent with Python and avoids the unusual `$` sigil in Java method names (which, while legal, is conventionally reserved for generated or tool code in other ecosystems).
