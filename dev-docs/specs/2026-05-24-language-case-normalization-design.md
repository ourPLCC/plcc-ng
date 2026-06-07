# Language Case Normalization in build_model

**Issue:** #035 — Python emitter not including semantics blocks
**Date:** 2026-05-24

## Problem

`parse_dividers.py` captures the language token from the spec divider verbatim. So `% HiPy python` produces `Divider(language='python')`. The model carries this through unchanged, but `_find_python_section` in the Python emitter (and `_find_java_section` in the Java emitter) compare against `'Python'` and `'Java'` respectively. The case mismatch means no section is ever found, so user-defined semantics blocks are silently ignored.

## Decision

Normalize the language field to **lowercase** in `build_model.py` when constructing the model JSON. The model is the right seam: it is the boundary between the raw parsed spec and the language-neutral representation consumed by all emitters.

`.title()` was considered but rejected: `'PlantUML'.title()` → `'Plantuml'`, which would corrupt the canonical form of multi-word language names. `.lower()` is safe for all realistic language tags.

Both emitters' section-finder functions are also updated to compare against the lowercase canonical form (`s.get('language', '').lower() == 'python'` and `== 'java'`). This is deliberately defensive — the emitters remain correct even if they receive model JSON that was built without the normalization step.

The divider parser and `SemanticSpec` continue to store the literal value from the spec file.

## Changes

**`src/plcc/model/build_model.py`** — `_build_semantic_sections`: normalize to lowercase:

```python
'language': s['language'].lower(),
```

**`src/plcc/lang/ext/python/emit.py`** — `_find_python_section`: compare lowercase:

```python
if s.get('language', '').lower() == 'python':
```

**`src/plcc/lang/ext/java/emit.py`** — `_find_java_section`: compare lowercase:

```python
if s.get('language', '').lower() == 'java':
```

## Tests

- `build_model_test.py`: new test feeds `"PYTHON"` and asserts model has `'python'`; existing `test_semantic_sections_present` updated to assert `'plantuml'` (lowercase).
- `python/emit_test.py`: regression test passes `"language": "python"` and asserts body fragments appear in the generated class file.
- `java/emit_test.py`: same pattern for Java.

## Edge Cases

`.lower()` is safe for all strings including empty. The language field always has a value (the divider parser defaults to `'Java'`). An empty string produces another empty string, which no emitter matches — harmless.

The model JSON is generated fresh each build and never stored at rest, so no migration is needed.
