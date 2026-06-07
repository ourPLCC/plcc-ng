# Design: Remove `entry_point` from Grammar Syntax (Issue 031)

**Date:** 2026-06-01
**Type:** refactor / fix

## Background

The `%` divider line in a PLCC grammar file optionally accepts a third token that
sets the entry point method name for the generated interpreter:

```
% semantics python evaluate
```

This was added to support portability across different implementations of the same
language extension (e.g., two Python emitters that disagree on the default method
name). In practice, the primary audience is students who never need this control,
and no real grammar files use it. It also introduced a crash (issue 031): if a
grammar declares a custom entry point but the grammar writer does not implement
that method, the generated `main.py` or `Main.java` calls a method that does not
exist on `_Start`.

## Decision

Remove `entry_point` from grammar syntax entirely. Language extensions own the
entry point name via their internal `_DEFAULT_ENTRY_POINT` constant. Grammar
writers never specify it. The portability use case is unlikely enough that it does
not justify the complexity.

This is a clean break — no backwards compatibility shim.

## Scope

### Production code

| File | Change |
|------|--------|
| `src/plcc/spec/rough/parse_dividers.py` | Tighten `toolLanguage` regex to reject a third token; raise a parse error with a clear message if one is present |
| `src/plcc/spec/rough/Divider.py` | Remove `entry_point: str \| None` field |
| `src/plcc/spec/semantics/SemanticSpec.py` | Remove `entry_point: str \| None` field |
| `src/plcc/spec/semantics/parse_semantic_spec.py` | Remove `entry_point` pass-through when constructing `SemanticSpec` |
| `src/plcc/model/build_model.py` | Remove `'entry_point': s.get('entry_point')` from model dict |
| `src/plcc/lang/ext/python/emit.py` | Replace `(section.get('entry_point') or _DEFAULT_ENTRY_POINT)` with `_DEFAULT_ENTRY_POINT` directly; keep the constant |
| `src/plcc/lang/ext/java/emit.py` | Same as above |

`_Start.py` and `_Start.java` templates are already correct — they hardcode
`_run()` / `$run()` and need no changes.

### Tests — delete

| File | Tests to delete |
|------|----------------|
| `src/plcc/spec/rough/parse_dividers_test.py` | `test_one_divider_with_entry_point`, `test_one_divider_without_entry_point_has_null`; remove `entry_point` param from `make_divider` helper |
| `src/plcc/lang/ext/python/emit_test.py` | `test_emit_main_py_contains_entry_point`, `test_emit_main_py_entry_point_defaults_to_run_when_null`; remove `entry_point` key from model fixtures |
| `src/plcc/lang/ext/java/emit_test.py` | `test_entry_point_defaults_to_dollar_run_when_null`, `test_declared_entry_point_is_used`; remove `entry_point` key from model fixtures |
| `src/plcc/model/build_model_test.py` | `test_semantic_section_entry_point_null_when_absent`, `test_semantic_section_entry_point_when_present` |
| `tests/bats/integration/python-emit.bats` | `null entry_point in model generates main.py calling _run` |

### Tests — add

| File | Test to add |
|------|-------------|
| `src/plcc/spec/rough/parse_dividers_test.py` | Assert that a divider line with three tokens (e.g., `% semantics python evaluate`) raises a parse error |

### Fixture grammar files

No changes — none use `entry_point`.

## Parse error behavior

A `%` divider line with a third token is a parse error. Error message should
identify the unexpected token and its location. Example:

```
Error: unexpected token 'evaluate' on divider line (line 5)
```

## What does NOT change

- `_DEFAULT_ENTRY_POINT` constants in each emitter stay — they are the right home
  for the language-specific default name and will be the extension point if a new
  language ever needs a different name.
- The `_Start` base class templates are unchanged.
- All fixture grammar files are unchanged.
