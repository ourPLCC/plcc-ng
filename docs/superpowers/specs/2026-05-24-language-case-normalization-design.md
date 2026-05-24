# Language Case Normalization in build_model

**Issue:** #035 — Python emitter not including semantics blocks
**Date:** 2026-05-24

## Problem

`parse_dividers.py` captures the language token from the spec divider verbatim. So `% HiPy python` produces `Divider(language='python')`. The model carries this through unchanged, but `_find_python_section` in the Python emitter (and `_find_java_section` in the Java emitter) compare against `'Python'` and `'Java'` respectively. The case mismatch means no section is ever found, so user-defined semantics blocks are silently ignored.

## Decision

Normalize the language field to title case in `build_model.py` when constructing the model JSON. The model is the right seam: it is the boundary between the raw parsed spec and the language-neutral representation consumed by all emitters.

The divider parser and `SemanticSpec` continue to store the literal value from the spec file. Emitters are unchanged.

## Change

In `_build_semantic_sections` in `src/plcc/model/build_model.py`, apply `.title()` to the language string:

```python
'language': s['language'].title(),
```

`str.title()` title-cases a single word: `'python'` → `'Python'`, `'JAVA'` → `'Java'`, `'jAvA'` → `'Java'`.

## Tests

- `build_model_test.py`: add a test that feeds a semantic section with a lowercase language name and asserts the model output uses title case.
- `emit_test.py` (Python emitter): add a regression test that passes a model with `"language": "python"` and asserts body fragments are included in the generated class file.

No existing tests change.

## Edge Cases

`.title()` is safe for all non-empty strings. The language field always has a value (the divider parser defaults to `'Java'`). An empty string produces another empty string, which no emitter matches — harmless.

The model JSON is generated fresh each build and never stored at rest, so no migration is needed.
