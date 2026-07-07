# Haskell Fragment Validation Design

**Date:** 2026-06-23
**Issue:** 105 — haskell-fragment-concrete-class-name-silently-ignored

## Problem

The Haskell emitter uses a one-nonterminal-per-module model: each abstract rule
(e.g. `ExprRest`) maps to one `.hs` module, and its concrete alternatives
(e.g. `AddRest`, `NilRest`) are constructors within that module — not modules
themselves. Lone concrete classes (no abstract parent, e.g. `Prog`) do get their
own module.

When a user tags a `%haskell` fragment with a concrete-with-abstract-parent
class name (e.g. `AddRest`), the emitter silently drops it: no module named
`AddRest` exists, so the fragment is never placed anywhere. The result is
missing code that fails to compile with no explanation.

This is an impedance mismatch with Java/Python/JavaScript, which all use a
one-class-one-file model where every class name — concrete or abstract — is a
valid fragment target.

## Decision

Raise a fatal error (`SystemExit`) before writing any output files when a
fragment's `class_name` is invalid for its kind. "Invalid" is defined
per fragment kind:

| Fragment kind | Concrete-with-abstract-parent name | Completely unknown name |
|---|---|---|
| `top` / `import` / `body` | Error | Error |
| `file` | Error | OK (helper module) |

`file` fragments with completely unknown names are allowed because creating
helper modules (e.g. `Helpers.hs`) is a legitimate use case. Concrete
alternative names are still an error for `file` fragments because the name
suggests the user believed `AddRest` would get its own file, which it does not.

## Architecture

### New module: `src/plcc/lang/ext/haskell/validate.py`

Validation is separated from emission into its own module, parallel to
`emit.py`, `build.py`, and `run.py`. This keeps `emit.py` focused on file
generation and makes validation independently testable.

Public entry point:

```python
def validate_fragments(fragments, classes):
    """Raise SystemExit if any fragment has an invalid class_name for Haskell.

    fragments: list of fragment dicts from the model's haskell semantic section.
    classes:   list of class dicts from the model.
    """
```

Internally it builds two structures from `classes`:

- `modules`: set of valid module names (abstract rules + lone concretes) —
  reuses `_group_modules` logic or accepts the already-built dict.
- `concrete_to_abstract`: dict mapping each concrete-with-abstract-parent name
  to its abstract parent's name (e.g. `{'AddRest': 'ExprRest'}`).

### Changes to `emit.py`

`emit()` calls `validate_fragments` after building `fragments_by_class` and
before any file I/O:

```python
def emit(model, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    modules = _group_modules(model['classes'])
    ...
    all_frags = section.get('fragments', []) if section else []
    fragments_by_class = _group_fragments(all_frags)
    validate_fragments(all_frags, model['classes'])  # new — exits before I/O if invalid
    ...  # rest unchanged
```

## Error Messages

All errors are printed to stderr and exit non-zero via `SystemExit`.

**Concrete-with-abstract-parent (all fragment kinds):**
```
plcc-haskell-emit: fragment tagged 'AddRest': AddRest is a concrete alternative of ExprRest.
In Haskell, concrete alternatives are constructors inside their abstract rule's module.
Use 'ExprRest' as the fragment class name instead.
```

**Completely unknown name (`top`/`import`/`body` only):**
```
plcc-haskell-emit: fragment tagged 'FooBar': no Haskell module for 'FooBar'.
Valid module names are: Expr, ExprRest, Prog
```

## Testing

### `validate_test.py` (new)

Tests call `validate_fragments` directly.

**Group 1 — Valid names pass silently:**
- Abstract rule name with each of the four fragment kinds → no error.
- Lone concrete name with each of the four fragment kinds → no error.
- Completely unknown name with `file` kind → no error (helper module).

**Group 2 — Concrete-with-abstract-parent errors:**
- One test per fragment kind (`top`, `import`, `body`, `file`), each asserting
  `SystemExit` with a message naming the concrete class and the parent module.

**Group 3 — Unknown name on injected kinds:**
- `top` fragment with unknown name → `SystemExit` listing valid names.
- `import` fragment with unknown name → same.
- `body` fragment with unknown name → same.

### `emit_test.py` (one addition)

One new test: a `body` fragment tagged with a concrete alternative's name causes
`SystemExit` when `emit()` is called — verifying wiring without duplicating
message assertions.

## Out of Scope

- Adding helper `file`-fragment module names to `interpreter.cabal`'s
  `other-modules`. That is a separate issue.
- Validation for other language emitters. The pattern (`validate.py` parallel
  to `emit.py`) is established here for Haskell; other languages adopt it if
  they develop structural constraints.
- Documentation of the Haskell one-module-per-rule model. Tracked separately
  in issue 105's "Related: Haskell documentation needed" note.
