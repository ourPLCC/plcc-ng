# Design: Filter comment lines in semantics section at parse time

**Issue:** 040  
**Date:** 2026-05-25  
**Branch:** fix/semantics-comments-empty-files

## Problem

Lines beginning with `#` in the semantics section of a grammar file are intended as comments and should be ignored. Instead they pass through the full pipeline and cause empty files to be written into the build output directory.

The root cause is that `parse_code_fragments.py` does not treat `#`-prefixed lines as empty. They reach `parse_target_locator`, which matches the whole line as a class name (e.g. `className='# This is a helper class'`). That value flows into `SemanticSpec`, then `spec.json`, then `model.json`, where `_compute_kind` classifies it as `kind='file'` (since the name is not in the known class set). Both the Java and Python emitters then write a file named after the comment.

The Java emitter has a partial band-aid (`startswith('#')` guard in `_group_fragments`) that prevents `body`/`import`/`init` fragments from being injected into class files, but the `kind='file'` writing loop has no such guard. The Python emitter has no guard at all.

## Decision

Fix at parse time (Option A): extend `isEmpty()` in `parse_code_fragments.py` to treat `#`-prefixed lines as empty. This is the earliest possible chokepoint — comments are dropped before a `TargetLocator` is ever created, so they never appear in `SemanticSpec`, `spec.json`, `model.json`, or any language emitter. Future language emitters are automatically safe with no additional work required.

Comments in `spec.json` serve no purpose: no current consumer (`plcc-ll1`, `plcc-model`, `plcc-make`, `plcc-tokens`, `plcc-parse`) has any use for them. Allowing them to appear would misrepresent them as malformed `TargetLocator` objects rather than as a recognised syntactic element.

## The Fix

In `src/plcc/spec/semantics/parse_code_fragments.py`, update `isEmpty()`:

```python
def isEmpty(locatorOrBlock):
    if locatorOrBlock is None:
        return True
    if isinstance(locatorOrBlock, Line):
        s = locatorOrBlock.string
        return s is None or s.strip() == '' or s.lstrip().startswith('#')
    return False
```

`s.lstrip().startswith('#')` handles leading whitespace before the `#` consistently with how blank lines are handled.

## Cleanup

**Remove the Java emitter band-aid.** The `startswith('#')` guard in `_group_fragments` in `src/plcc/lang/ext/java/emit.py` is now unreachable. Remove it to avoid misleading future readers into thinking the model can contain comment-named fragments.

**Remove one emitter test.** `test_hash_comment_class_name_is_skipped` in `src/plcc/lang/ext/java/emit_test.py` tests the now-deleted band-aid by injecting a `#`-named fragment directly into the model. The model contract is that such fragments do not exist; this test should be removed.

## Tests

**`src/plcc/spec/semantics/parse_code_fragments_test.py` — new test**

Assert that a line beginning with `#` is treated as empty: it produces no `CodeFragment` and does not interfere with adjacent locators or blocks. This is the canonical regression test for the fix.

**`src/plcc/lang/ext/java/emit_test.py` — remove one test**

Delete `test_hash_comment_class_name_is_skipped`. See Cleanup above.

**`src/plcc/lang/ext/python/emit_test.py` — no new test needed**

The Python emitter has no band-aid to remove and no test to add at the emitter layer. The model contract is that comment-named fragments do not exist; the canonical coverage is the `parse_code_fragments` test above.
