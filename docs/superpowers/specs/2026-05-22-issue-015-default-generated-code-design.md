# Design: Default Generated Code Should Run (Issue 015)

**Date:** 2026-05-22
**Issue:** [docs/issues/015-default-generated-code-should-run.md](../../issues/015-default-generated-code-should-run.md)

## Problem

When a grammar has no semantics section, both emitters (`plcc-python-emit`, `plcc-java-emit`) still generate a `main` entry point that calls `_run()` (Python) or `$run()` (Java) on the root node. Because no semantics section means no method definitions, these calls fail at runtime with a method-not-found error.

The original PLCC solved this by generating a `_Start` class that the start symbol's class extends. `_Start` provides a default `$run()` implementation so the generated code runs without crashing even when the user writes no semantics.

## Solution

Generate a `_Start` class file alongside the other per-class files. The start symbol's class extends `_Start` instead of `runtime.Node` directly. All other classes are unaffected.

This replicates the original PLCC's approach: `_Start` is the honest owner of the default behaviour, and only the root of the AST hierarchy carries it.

## `_Start` Content

**Java — `_Start.java`** (generated to `output_dir/`):

```java
public abstract class _Start extends runtime.Node {
    public void $run() {
        System.out.println(this.toString());
    }
}
```

**Python — `_Start.py`** (generated to `output_dir/`):

```python
import runtime.base as _plcc

class _Start(_plcc.Node):
    def _run(self):
        print(str(self))
```

Both default implementations print the language's default string representation of the root node to stdout, returning void/None. Behaviour is consistent across languages.

## Inheritance

```
runtime.Node  (existing runtime base)
    └── _Start  (generated; provides default _run / $run)
            └── Program  (or whatever the start class is; user overrides _run/$run here)
```

For grammars where the start symbol uses alternative names (making it abstract):

```
runtime.Node
    └── _Start
            └── Expr  (abstract start class)
                    ├── Num
                    └── Add
```

`_Start` is always inserted between `runtime.Node` and the top-level generated class, regardless of whether that class is abstract or concrete.

## Changes Required

### Both emitters (`plcc-python-emit`, `plcc-java-emit`)

1. Compute `start_class_name` from `model['start']` (capitalize first letter).
2. In the class-emission loop, for the class where `name == start_class_name` and `extends is None`, operate on a copy of the class dict with `extends` set to `'_Start'`.
3. After the class loop, write `_Start.py` / `_Start.java` to the output directory.

### Templates — no changes needed

The Python class template already emits `from {{ cls.extends }} import {{ cls.extends }}` for any class with a non-null `extends`, so the start class picks up `_Start` automatically. The Java class template already emits `extends {{ cls.extends }}`. No template modifications are required.

### `runtime.Node` — no changes

`_Start` extends `runtime.Node` but `runtime.Node` itself is unchanged.

## Behaviour

| Scenario | Result |
|---|---|
| No semantics section | `_Start._run()` / `_Start.$run()` prints `str(self)` / `this.toString()` to stdout; JSONL pipeline emits `{"kind":"result","value":null}` |
| User defines `_run()` / `$run()` on the start class | User's method overrides `_Start`'s default; normal operation |
| User defines methods on non-start classes only | `_Start`'s default runs for the root; user methods run for the rest |

## Testing

- **Unit tests** in `plcc/lang/ext/python/emit_test.py` and `plcc/lang/ext/java/emit_test.py`:
  - `_Start.py` / `_Start.java` is written to the output directory
  - The start class's generated file extends `_Start`
  - Non-start classes still extend `runtime.Node` (or their grammar-defined base)
- **Integration tests** in `tests/bats/integration/python-emit.bats` and `java-emit.bats`:
  - A no-semantics grammar produces code that runs without error
  - A grammar with semantics still works as before (regression)
