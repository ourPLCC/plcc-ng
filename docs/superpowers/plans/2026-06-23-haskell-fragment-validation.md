# Haskell Fragment Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Raise a clear fatal error when a `%haskell` fragment is tagged with a class name that has no corresponding Haskell module, replacing the current silent-drop behaviour.

**Architecture:** A new `validate.py` module in the Haskell extension holds all validation logic and is called by `emit.py` before any file I/O. Two private helpers build lookups from the model's class list: the set of valid module names, and a mapping from concrete-alternative names to their abstract parent. The public entry point `validate_fragments` walks every fragment, checks its `class_name` against those lookups, and calls `sys.exit(1)` with a targeted message on the first violation.

**Tech Stack:** Python 3, pytest, existing project test runner (`bin/test/units.bash`).

## Global Constraints

- All new code lives under `src/plcc/lang/ext/haskell/`.
- Test file naming follows the existing `<module>_test.py` convention in the same package directory.
- Error output goes to `sys.stderr`; exit via `sys.exit(1)` (not `raise SystemExit` directly).
- Error message prefix is `plcc-haskell-emit:` to match the tool name.
- No new dependencies.

---

### Task 1: `validate.py` — fragment validation module

**Files:**
- Create: `src/plcc/lang/ext/haskell/validate.py`
- Create: `src/plcc/lang/ext/haskell/validate_test.py`

**Interfaces:**
- Produces: `validate_fragments(fragments, classes)` — raises `SystemExit` on invalid fragment; returns `None` on success.
  - `fragments`: list of dicts, each with at minimum `{'class_name': str, 'kind': str}`.
  - `classes`: list of dicts, each with at minimum `{'name': str, 'abstract': bool, 'extends': str | None}`.

---

- [ ] **Step 1: Write the failing tests**

Create `src/plcc/lang/ext/haskell/validate_test.py`:

```python
import pytest

from .validate import validate_fragments


def _classes():
    return [
        {'name': 'ExprRest', 'abstract': True,  'extends': None},
        {'name': 'AddRest',  'abstract': False, 'extends': 'ExprRest'},
        {'name': 'NilRest',  'abstract': False, 'extends': 'ExprRest'},
        {'name': 'Prog',     'abstract': False, 'extends': None},
    ]


# --- Group 1: valid names pass silently ---

@pytest.mark.parametrize('kind', ['top', 'import', 'body', 'file'])
def test_abstract_rule_name_is_valid(kind):
    validate_fragments([{'class_name': 'ExprRest', 'kind': kind}], _classes())


@pytest.mark.parametrize('kind', ['top', 'import', 'body', 'file'])
def test_lone_concrete_name_is_valid(kind):
    validate_fragments([{'class_name': 'Prog', 'kind': kind}], _classes())


def test_unknown_name_is_valid_for_file_fragments():
    validate_fragments([{'class_name': 'Helpers', 'kind': 'file'}], _classes())


def test_empty_fragment_list_is_valid():
    validate_fragments([], _classes())


# --- Group 2: concrete-with-abstract-parent errors ---

@pytest.mark.parametrize('kind', ['top', 'import', 'body', 'file'])
def test_concrete_alternative_name_raises_for_all_kinds(kind):
    with pytest.raises(SystemExit):
        validate_fragments([{'class_name': 'AddRest', 'kind': kind}], _classes())


def test_concrete_error_message_names_the_concrete_class(capsys):
    with pytest.raises(SystemExit):
        validate_fragments([{'class_name': 'AddRest', 'kind': 'body'}], _classes())
    assert 'AddRest' in capsys.readouterr().err


def test_concrete_error_message_names_the_parent_module(capsys):
    with pytest.raises(SystemExit):
        validate_fragments([{'class_name': 'AddRest', 'kind': 'body'}], _classes())
    assert 'ExprRest' in capsys.readouterr().err


def test_concrete_error_message_suggests_using_parent(capsys):
    with pytest.raises(SystemExit):
        validate_fragments([{'class_name': 'NilRest', 'kind': 'top'}], _classes())
    err = capsys.readouterr().err
    assert 'ExprRest' in err


# --- Group 3: unknown name on injected fragment kinds ---

@pytest.mark.parametrize('kind', ['top', 'import', 'body'])
def test_unknown_name_raises_for_injected_kinds(kind):
    with pytest.raises(SystemExit):
        validate_fragments([{'class_name': 'Helpers', 'kind': kind}], _classes())


def test_unknown_name_error_message_includes_the_bad_name(capsys):
    with pytest.raises(SystemExit):
        validate_fragments([{'class_name': 'Helpers', 'kind': 'body'}], _classes())
    assert 'Helpers' in capsys.readouterr().err


def test_unknown_name_error_message_lists_valid_module_names(capsys):
    with pytest.raises(SystemExit):
        validate_fragments([{'class_name': 'Helpers', 'kind': 'body'}], _classes())
    err = capsys.readouterr().err
    assert 'ExprRest' in err
    assert 'Prog' in err
```

- [ ] **Step 2: Run tests to confirm they all fail**

```bash
bin/test/units.bash src/plcc/lang/ext/haskell/validate_test.py -v
```

Expected: errors because `validate.py` does not exist yet (`ModuleNotFoundError` or similar).

- [ ] **Step 3: Create `validate.py`**

Create `src/plcc/lang/ext/haskell/validate.py`:

```python
import sys


def validate_fragments(fragments, classes):
    """Raise SystemExit if any fragment has an invalid class_name for Haskell.

    fragments: list of fragment dicts with 'class_name' and 'kind' keys.
    classes:   list of class dicts with 'name', 'abstract', and 'extends' keys.
    """
    modules = _build_modules(classes)
    concrete_to_abstract = _build_concrete_to_abstract(classes)

    for frag in fragments:
        class_name = frag['class_name']
        kind = frag['kind']

        if class_name in modules:
            continue

        if class_name in concrete_to_abstract:
            parent = concrete_to_abstract[class_name]
            print(
                f"plcc-haskell-emit: fragment tagged '{class_name}': "
                f"{class_name} is a concrete alternative of {parent}.\n"
                f"In Haskell, concrete alternatives are constructors inside "
                f"their abstract rule's module.\n"
                f"Use '{parent}' as the fragment class name instead.",
                file=sys.stderr,
            )
            sys.exit(1)

        if kind != 'file':
            valid = ', '.join(sorted(modules))
            print(
                f"plcc-haskell-emit: fragment tagged '{class_name}': "
                f"no Haskell module for '{class_name}'.\n"
                f"Valid module names are: {valid}",
                file=sys.stderr,
            )
            sys.exit(1)


def _build_modules(classes):
    """Return the set of valid Haskell module names.

    Includes abstract rules and lone concretes (concretes whose extends is
    not an abstract rule, including extends=None).
    """
    abstract_names = {cls['name'] for cls in classes if cls['abstract']}
    modules = set(abstract_names)
    for cls in classes:
        if not cls['abstract'] and cls['extends'] not in abstract_names:
            modules.add(cls['name'])
    return modules


def _build_concrete_to_abstract(classes):
    """Return dict mapping concrete-alternative names to their abstract parent name."""
    abstract_names = {cls['name'] for cls in classes if cls['abstract']}
    return {
        cls['name']: cls['extends']
        for cls in classes
        if not cls['abstract'] and cls['extends'] in abstract_names
    }
```

- [ ] **Step 4: Run tests to confirm they all pass**

```bash
bin/test/units.bash src/plcc/lang/ext/haskell/validate_test.py -v
```

Expected: all tests pass, 0 failures.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/lang/ext/haskell/validate.py src/plcc/lang/ext/haskell/validate_test.py
git commit -m "feat(haskell): add validate_fragments to detect invalid fragment class names"
```

---

### Task 2: Wire `validate_fragments` into `emit.py`

**Files:**
- Modify: `src/plcc/lang/ext/haskell/emit.py` — add import and call in `emit()`
- Modify: `src/plcc/lang/ext/haskell/emit_test.py` — add one wiring test

**Interfaces:**
- Consumes: `validate_fragments(fragments, classes)` from Task 1.

---

- [ ] **Step 1: Write the failing wiring test**

Add this test to the bottom of `src/plcc/lang/ext/haskell/emit_test.py`:

```python
def test_emit_raises_on_fragment_with_concrete_alternative_name(monkeypatch, tmp_path):
    # NumExpr extends Expr (abstract) in _minimal_model(), so it's a concrete alternative
    model = _model_with_fragments([
        {'class_name': 'NumExpr', 'kind': 'body', 'body': '-- code'}
    ])
    with pytest.raises(SystemExit):
        _run_emit(monkeypatch, tmp_path, model)
```

- [ ] **Step 2: Run the test to confirm it fails**

```bash
bin/test/units.bash src/plcc/lang/ext/haskell/emit_test.py::test_emit_raises_on_fragment_with_concrete_alternative_name -v
```

Expected: FAIL — `emit()` currently drops the fragment silently instead of raising.

- [ ] **Step 3: Add the import and call to `emit.py`**

At the top of `src/plcc/lang/ext/haskell/emit.py`, add the import after the existing local imports:

```python
from .validate import validate_fragments
```

In the `emit()` function, insert the `validate_fragments` call after `fragments_by_class` is built and before the module-writing loop. The modified section of `emit()` looks like:

```python
def emit(model, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    modules = _group_modules(model['classes'])
    _write_cabal(modules, output_dir)
    _copy_token(output_dir)
    section = _find_haskell_section(model)
    all_frags = section.get('fragments', []) if section else []
    fragments_by_class = _group_fragments(all_frags)
    validate_fragments(all_frags, model['classes'])
    start_module = model['start'][0].upper() + model['start'][1:]
    for module_name, module_info in modules.items():
        is_start = (module_name == start_module)
        _write_module(module_name, module_info, fragments_by_class, output_dir, is_start)
    for frag in all_frags:
        if frag['kind'] == 'file':
            (output_dir / f'{frag["class_name"]}.hs').write_text(frag['body'])
    _write_main(start_module, modules, output_dir)
```

- [ ] **Step 4: Run the wiring test to confirm it passes**

```bash
bin/test/units.bash src/plcc/lang/ext/haskell/emit_test.py::test_emit_raises_on_fragment_with_concrete_alternative_name -v
```

Expected: PASS.

- [ ] **Step 5: Run the full unit suite to confirm no regressions**

```bash
bin/test/units.bash
```

Expected: all tests pass, 0 failures.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/lang/ext/haskell/emit.py src/plcc/lang/ext/haskell/emit_test.py
git commit -m "feat(haskell): wire validate_fragments into emit to enforce fragment class name rules"
```
