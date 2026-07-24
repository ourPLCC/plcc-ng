# Reserved-Word Field Name Rejection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject, at emit time, any grammar field name (explicit `:fieldname` or auto-derived) that collides with a reserved word of the target semantic-implementation language, instead of silently emitting code that fails only when loaded/compiled (e.g. `<VAR>` auto-naming field `var`, which breaks JavaScript's `constructor(var)`).

**Architecture:** A "plugin interface" of one `RESERVED_WORDS` frozenset per language target (`src/plcc/lang/ext/<lang>/reserved_words.py`), consumed by one shared check-and-reject function (`src/plcc/lang/reserved_words.py`). Each of the four `plcc-<lang>-emit` commands (`src/plcc/lang/ext/{javascript,java,python,haskell}/emit.py`) wires in the shared function with two lines, immediately after reading the model and before creating any output. `plcc-lang-emit` (`src/plcc/lang/emit.py`) is untouched — it's a pure subprocess dispatcher that pipes `stdin` straight through and never parses the model itself.

**Tech Stack:** Python 3, pytest, bats (e2e tests). No new dependencies (Python's list is sourced from the stdlib `keyword` module).

## Global Constraints

- Follow CONTRIBUTING.md's TDD loop: write the failing test, confirm the failure, write the minimal fix, confirm the pass, commit.
- Run `bin/test/units.bash <path>` to scope pytest runs to the file(s) touched in each task; run the full `bin/test/units.bash` before the final commit of the branch. Baseline (before this plan): 1191 passed, 3 skipped.
- No auto-renaming/mangling of field names, and no change to the shared language-neutral model (`src/plcc/model/build_model.py`) — the field name a grammar author sees is exactly what's checked.
- Arbno/list fields (`varList`) never need special-casing — `build_model.py` always appends `List` to their name, so they never collide with a bare reserved word.
- This is not a breaking change: every word in every `RESERVED_WORDS` set is a genuine reserved word in that target language, so any grammar this newly rejects was already producing code that would fail to load/compile — it just failed later and less clearly. Plain `fix(...):` commits, no `BREAKING CHANGE:` footer.
- Design of record: `dev-docs/specs/2026-07-24-163-js-var-field-reserved-word-design.md`. If anything here seems to contradict it, the spec wins — stop and reconcile before continuing.

---

### Task 1: Shared reserved-word check-and-reject module

**Files:**
- Create: `src/plcc/lang/reserved_words.py`
- Test: `src/plcc/lang/reserved_words_test.py`

**Interfaces:**
- Consumes: `classes` — the same list-of-dicts shape `build_model.py` produces and every `plcc-<lang>-emit` already reads from `model['classes']`: `[{'name': str, 'abstract': bool, 'extends': str|None, 'fields': [{'name': str, 'type': str, 'is_list': bool}, ...], 'rule_name': str}, ...]`.
- Produces: `check_reserved_field_names(classes, language, reserved_words) -> list[str]` and `reject_reserved_field_names(classes, language, reserved_words, stage) -> None` (may call `sys.exit(1)`). Every later task imports both of these from `plcc.lang.reserved_words`.

- [ ] **Step 1: Write the failing tests**

Create `src/plcc/lang/reserved_words_test.py`:

```python
import pytest

from plcc.lang.reserved_words import check_reserved_field_names, reject_reserved_field_names


def _class(name, fields, abstract=False, extends=None):
    return {
        'name': name,
        'abstract': abstract,
        'extends': extends,
        'fields': fields,
        'rule_name': name,
    }


def test_check_reserved_field_names_reports_a_collision():
    classes = [_class('VarExp', [{'name': 'var', 'type': 'Token', 'is_list': False}])]
    errors = check_reserved_field_names(classes, 'javascript', frozenset({'var'}))
    assert len(errors) == 1
    assert "class 'VarExp'" in errors[0]
    assert "field 'var'" in errors[0]
    assert "javascript reserved word 'var'" in errors[0]


def test_check_reserved_field_names_ignores_non_colliding_fields():
    classes = [_class('VarExp', [{'name': 'name', 'type': 'Token', 'is_list': False}])]
    errors = check_reserved_field_names(classes, 'javascript', frozenset({'var'}))
    assert errors == []


def test_check_reserved_field_names_ignores_list_suffixed_fields():
    classes = [_class('Words', [{'name': 'varList', 'type': 'Token', 'is_list': True}])]
    errors = check_reserved_field_names(classes, 'javascript', frozenset({'var'}))
    assert errors == []


def test_check_reserved_field_names_reports_one_message_per_collision():
    classes = [_class('Pair', [
        {'name': 'var', 'type': 'Token', 'is_list': False},
        {'name': 'class', 'type': 'Token', 'is_list': False},
    ])]
    errors = check_reserved_field_names(classes, 'javascript', frozenset({'var', 'class'}))
    assert len(errors) == 2


def test_reject_reserved_field_names_exits_1_and_prints_stage_prefixed_error(capsys):
    classes = [_class('VarExp', [{'name': 'var', 'type': 'Token', 'is_list': False}])]
    with pytest.raises(SystemExit) as exc_info:
        reject_reserved_field_names(
            classes, 'javascript', frozenset({'var'}), stage='plcc-javascript-emit'
        )
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert captured.err.startswith('plcc-javascript-emit: error:')
    assert "field 'var'" in captured.err


def test_reject_reserved_field_names_is_a_noop_when_clean(capsys):
    classes = [_class('VarExp', [{'name': 'name', 'type': 'Token', 'is_list': False}])]
    reject_reserved_field_names(
        classes, 'javascript', frozenset({'var'}), stage='plcc-javascript-emit'
    )
    captured = capsys.readouterr()
    assert captured.err == ''
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `bin/test/units.bash src/plcc/lang/reserved_words_test.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'plcc.lang.reserved_words'` (or `ImportError`).

- [ ] **Step 3: Write the implementation**

Create `src/plcc/lang/reserved_words.py`:

```python
import sys


def check_reserved_field_names(classes, language, reserved_words):
    """Return one message per field whose name collides with reserved_words."""
    errors = []
    for cls in classes:
        for field in cls['fields']:
            name = field['name']
            if name in reserved_words:
                errors.append(
                    f"class '{cls['name']}' field '{name}' collides with "
                    f"the {language} reserved word '{name}' — rename the "
                    f"capture, e.g. <{name.upper()}:name>"
                )
    return errors


def reject_reserved_field_names(classes, language, reserved_words, stage):
    """Print each collision to stderr and exit(1) if any are found."""
    errors = check_reserved_field_names(classes, language, reserved_words)
    if errors:
        for error in errors:
            print(f"{stage}: error: {error}", file=sys.stderr)
        sys.exit(1)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `bin/test/units.bash src/plcc/lang/reserved_words_test.py -v`
Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/lang/reserved_words.py src/plcc/lang/reserved_words_test.py
git commit -m "feat(lang): add shared reserved-word field-name check"
```

---

### Task 2: Wire the check into `plcc-javascript-emit`

**Files:**
- Create: `src/plcc/lang/ext/javascript/reserved_words.py`
- Modify: `src/plcc/lang/ext/javascript/emit.py:1-59`
- Modify: `docs/language-guide/languages/javascript.md:211-216` ("Restrictions" section)
- Test: `src/plcc/lang/ext/javascript/emit_test.py`

**Interfaces:**
- Consumes: `check_reserved_field_names`/`reject_reserved_field_names` from Task 1 (`plcc.lang.reserved_words`).
- Produces: `RESERVED_WORDS: frozenset[str]` in `plcc.lang.ext.javascript.reserved_words`, consumed only by this task's `emit.py`.

- [ ] **Step 1: Write the failing test**

Add to `src/plcc/lang/ext/javascript/emit_test.py`, after `test_emit_class_file_imports_language_error` (end of file):

```python


def test_emit_rejects_field_name_colliding_with_reserved_word(tmp_path, monkeypatch, capsys):
    model = _minimal_model()
    model['classes'][0]['fields'] = [{"name": "var", "type": "Token"}]
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    with pytest.raises(SystemExit) as exc_info:
        run_main([f'--output={tmp_path}'])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert 'plcc-javascript-emit: error:' in captured.err
    assert "field 'var'" in captured.err
    assert list(tmp_path.iterdir()) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bin/test/units.bash src/plcc/lang/ext/javascript/emit_test.py -v`
Expected: `test_emit_rejects_field_name_colliding_with_reserved_word` FAILS — no `SystemExit` is raised (emit succeeds and writes `Program.js`, so `list(tmp_path.iterdir())` is non-empty and the assertion on it fails, or the `pytest.raises` block fails outright). All other tests still PASS.

- [ ] **Step 3: Create the reserved-word list**

Create `src/plcc/lang/ext/javascript/reserved_words.py`:

```python
# ECMA-262 keywords, plus the words reserved in strict mode (generated
# JavaScript class bodies are always strict) and the `enum` future-reserved
# word.
RESERVED_WORDS = frozenset({
    'break', 'case', 'catch', 'class', 'const', 'continue', 'debugger',
    'default', 'delete', 'do', 'else', 'enum', 'export', 'extends',
    'false', 'finally', 'for', 'function', 'if', 'implements', 'import',
    'in', 'instanceof', 'interface', 'let', 'new', 'null', 'package',
    'private', 'protected', 'public', 'return', 'static', 'super',
    'switch', 'this', 'throw', 'true', 'try', 'typeof', 'var', 'void',
    'while', 'with', 'yield',
})
```

- [ ] **Step 4: Wire it into `emit.py`**

Current code (`src/plcc/lang/ext/javascript/emit.py:18-23,45-58`):

```python
import jinja2
from plcc.cli import parse_args

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = __doc__ + VERBOSE_OPTIONS
```

```python
def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-javascript-emit", Events, args)
    output_dir = Path(args['--output'])
    verbose.emit(Events.STARTED, message=f'emitting to {output_dir}')

    model = json.load(sys.stdin)
    output_dir.mkdir(parents=True, exist_ok=True)

    _copy_runtime(output_dir)

    classes = model['classes']
    start_class_name = model['start'][0].upper() + model['start'][1:]
```

Change to:

```python
import jinja2
from plcc.cli import parse_args

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from plcc.lang.reserved_words import reject_reserved_field_names

from .reserved_words import RESERVED_WORDS

__doc__ = __doc__ + VERBOSE_OPTIONS
```

```python
def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-javascript-emit", Events, args)
    output_dir = Path(args['--output'])
    verbose.emit(Events.STARTED, message=f'emitting to {output_dir}')

    model = json.load(sys.stdin)
    classes = model['classes']
    reject_reserved_field_names(classes, 'javascript', RESERVED_WORDS, stage='plcc-javascript-emit')

    output_dir.mkdir(parents=True, exist_ok=True)

    _copy_runtime(output_dir)

    start_class_name = model['start'][0].upper() + model['start'][1:]
```

(Only the position of `classes = model['classes']` and the new check call move; every other line keeps its place.)

- [ ] **Step 5: Run test to verify it passes**

Run: `bin/test/units.bash src/plcc/lang/ext/javascript/emit_test.py -v`
Expected: all tests PASS, including the new one.

- [ ] **Step 6: Document the restriction**

Current text (`docs/language-guide/languages/javascript.md:211-216`):

```markdown
## Restrictions

- No `class` hook (unlike Java and Python). There is no equivalent in JavaScript.
- Generated code uses CommonJS (`require` / `module.exports`). ESM (`import` / `export`) is not supported.
- All output files are overwritten on every emit run — do not edit them directly.
- Sibling generated classes are not automatically in scope; require them explicitly with an `import` fragment.
```

Change to:

```markdown
## Restrictions

- No `class` hook (unlike Java and Python). There is no equivalent in JavaScript.
- Generated code uses CommonJS (`require` / `module.exports`). ESM (`import` / `export`) is not supported.
- All output files are overwritten on every emit run — do not edit them directly.
- Sibling generated classes are not automatically in scope; require them explicitly with an `import` fragment.
- A field name that becomes a JavaScript reserved word (e.g. `<VAR>` auto-naming field `var`) is rejected by `plcc-javascript-emit` — rename the capture, e.g. `<VAR:name>`. See [Reserved words](../syntactic.md#reserved-words) for details.
```

- [ ] **Step 7: Commit**

```bash
git add src/plcc/lang/ext/javascript/reserved_words.py src/plcc/lang/ext/javascript/emit.py \
        src/plcc/lang/ext/javascript/emit_test.py docs/language-guide/languages/javascript.md
git commit -m "fix(javascript): reject field names colliding with JS reserved words"
```

---

### Task 3: Wire the check into `plcc-java-emit`

**Files:**
- Create: `src/plcc/lang/ext/java/reserved_words.py`
- Modify: `src/plcc/lang/ext/java/emit.py:18-23,41-54`
- Modify: `docs/language-guide/languages/java.md:208-212` ("Restrictions" section)
- Test: `src/plcc/lang/ext/java/emit_test.py`

**Interfaces:**
- Consumes: `check_reserved_field_names`/`reject_reserved_field_names` from Task 1.
- Produces: `RESERVED_WORDS: frozenset[str]` in `plcc.lang.ext.java.reserved_words`.

Note: `var` is deliberately **excluded** here (unlike javascript's list). Per JLS 3.9, `var` is a reserved *type name* only in local-variable-type-inference contexts, not a keyword — it remains a legal identifier in a field declaration, which is exactly how `class_file.java.jinja:15` uses `field.name` (`public {{field.type}} {{field.name}};`, not a constructor parameter).

- [ ] **Step 1: Write the failing test**

Add to `src/plcc/lang/ext/java/emit_test.py`, directly after `test_main_java_validates_non_null_result` (the last test in the file, starting at line 303):

```python


def test_emit_rejects_field_name_colliding_with_reserved_word(tmp_path, monkeypatch, capsys):
    model = _minimal_model()
    model['classes'][0]['fields'] = [{"name": "class", "type": "runtime.Token", "is_list": False}]
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    with pytest.raises(SystemExit) as exc_info:
        run_main([f'--output={tmp_path}'])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert 'plcc-java-emit: error:' in captured.err
    assert "field 'class'" in captured.err
    assert list(tmp_path.iterdir()) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bin/test/units.bash src/plcc/lang/ext/java/emit_test.py -v`
Expected: `test_emit_rejects_field_name_colliding_with_reserved_word` FAILS (emit succeeds and writes `Program.java`; no `SystemExit`). All other tests still PASS.

- [ ] **Step 3: Create the reserved-word list**

Create `src/plcc/lang/ext/java/reserved_words.py`:

```python
# JLS 3.9 "reserved words": keywords plus the true/false/null reserved
# literals. `var` is deliberately excluded — it's a reserved *type name*
# only in local-variable-type-inference contexts, not in a field
# declaration (how field.name is used in class_file.java.jinja).
RESERVED_WORDS = frozenset({
    'abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch',
    'char', 'class', 'const', 'continue', 'default', 'do', 'double',
    'else', 'enum', 'extends', 'false', 'final', 'finally', 'float',
    'for', 'goto', 'if', 'implements', 'import', 'instanceof', 'int',
    'interface', 'long', 'native', 'new', 'null', 'package', 'private',
    'protected', 'public', 'return', 'short', 'static', 'strictfp',
    'super', 'switch', 'synchronized', 'this', 'throw', 'throws',
    'transient', 'true', 'try', 'void', 'volatile', 'while',
})
```

- [ ] **Step 4: Wire it into `emit.py`**

Current code (`src/plcc/lang/ext/java/emit.py:18-23,41-54`):

```python
import jinja2
from plcc.cli import parse_args

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = __doc__ + VERBOSE_OPTIONS
```

```python
def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-java-emit", Events, args)
    output_dir = Path(args['--output'])
    verbose.emit(Events.STARTED, message=f'emitting to {output_dir}')

    model = json.load(sys.stdin)
    output_dir.mkdir(parents=True, exist_ok=True)

    _copy_runtime(output_dir)

    classes = model['classes']
    start_class_name = model['start'][0].upper() + model['start'][1:]
```

Change to:

```python
import jinja2
from plcc.cli import parse_args

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from plcc.lang.reserved_words import reject_reserved_field_names

from .reserved_words import RESERVED_WORDS

__doc__ = __doc__ + VERBOSE_OPTIONS
```

```python
def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-java-emit", Events, args)
    output_dir = Path(args['--output'])
    verbose.emit(Events.STARTED, message=f'emitting to {output_dir}')

    model = json.load(sys.stdin)
    classes = model['classes']
    reject_reserved_field_names(classes, 'java', RESERVED_WORDS, stage='plcc-java-emit')

    output_dir.mkdir(parents=True, exist_ok=True)

    _copy_runtime(output_dir)

    start_class_name = model['start'][0].upper() + model['start'][1:]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `bin/test/units.bash src/plcc/lang/ext/java/emit_test.py -v`
Expected: all tests PASS, including the new one.

- [ ] **Step 6: Document the restriction**

Current text (`docs/language-guide/languages/java.md:208-212`):

```markdown
## Restrictions

- Requires Java JDK 21 or later for both building and running.
- All generated source files are overwritten on every emit run — do not edit them directly.
- Abstract classes need abstract method declarations added via `body` fragments if you want the compiler to enforce them on subclasses.
```

Change to:

```markdown
## Restrictions

- Requires Java JDK 21 or later for both building and running.
- All generated source files are overwritten on every emit run — do not edit them directly.
- Abstract classes need abstract method declarations added via `body` fragments if you want the compiler to enforce them on subclasses.
- A field name that becomes a Java reserved word (e.g. `class`, `new`) is rejected by `plcc-java-emit` — rename the capture. `var` is fine (it's only reserved for local-variable type inference, not field declarations). See [Reserved words](../syntactic.md#reserved-words) for details.
```

- [ ] **Step 7: Commit**

```bash
git add src/plcc/lang/ext/java/reserved_words.py src/plcc/lang/ext/java/emit.py \
        src/plcc/lang/ext/java/emit_test.py docs/language-guide/languages/java.md
git commit -m "fix(java): reject field names colliding with Java reserved words"
```

---

### Task 4: Wire the check into `plcc-python-emit`

**Files:**
- Create: `src/plcc/lang/ext/python/reserved_words.py`
- Modify: `src/plcc/lang/ext/python/emit.py:18-23,42-55`
- Modify: `docs/language-guide/languages/python.md:190-193` ("Restrictions" section)
- Test: `src/plcc/lang/ext/python/emit_test.py`

**Interfaces:**
- Consumes: `check_reserved_field_names`/`reject_reserved_field_names` from Task 1.
- Produces: `RESERVED_WORDS: frozenset[str]` in `plcc.lang.ext.python.reserved_words`, sourced live from `keyword.kwlist` (hard keywords only — `keyword.softkwlist` like `match`/`case`/`type`/`_` remain legal parameter names, so they're deliberately not included).

- [ ] **Step 1: Write the failing test**

Add to `src/plcc/lang/ext/python/emit_test.py`, directly after `test_emit_generated_main_non_string_return_is_specification_error` (the last test in the file, starting at line 328):

```python


def test_emit_rejects_field_name_colliding_with_reserved_word(tmp_path, monkeypatch, capsys):
    model = _minimal_model()
    model['classes'][0]['fields'] = [{"name": "class", "type": "Token"}]
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    with pytest.raises(SystemExit) as exc_info:
        run_main([f'--output={tmp_path}'])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert 'plcc-python-emit: error:' in captured.err
    assert "field 'class'" in captured.err
    assert list(tmp_path.iterdir()) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bin/test/units.bash src/plcc/lang/ext/python/emit_test.py -v`
Expected: `test_emit_rejects_field_name_colliding_with_reserved_word` FAILS (emit succeeds and writes `Program.py`; no `SystemExit`). All other tests still PASS.

- [ ] **Step 3: Create the reserved-word list**

Create `src/plcc/lang/ext/python/reserved_words.py`:

```python
import keyword

# Sourced from the running interpreter's own stdlib so it can never drift
# from the Python version actually executing plcc-ng. Deliberately uses
# kwlist (hard keywords), not softkwlist — `match`, `case`, `type`, `_`
# remain legal parameter names.
RESERVED_WORDS = frozenset(keyword.kwlist)
```

- [ ] **Step 4: Wire it into `emit.py`**

Current code (`src/plcc/lang/ext/python/emit.py:18-23,42-55`):

```python
import jinja2
from plcc.cli import parse_args

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = __doc__ + VERBOSE_OPTIONS
```

```python
def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-python-emit", Events, args)
    output_dir = Path(args['--output'])
    verbose.emit(Events.STARTED, message=f'emitting to {output_dir}')

    model = json.load(sys.stdin)
    output_dir.mkdir(parents=True, exist_ok=True)

    _copy_runtime(output_dir)

    classes = model['classes']
    start_class_name = model['start'][0].upper() + model['start'][1:]
```

Change to:

```python
import jinja2
from plcc.cli import parse_args

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from plcc.lang.reserved_words import reject_reserved_field_names

from .reserved_words import RESERVED_WORDS

__doc__ = __doc__ + VERBOSE_OPTIONS
```

```python
def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-python-emit", Events, args)
    output_dir = Path(args['--output'])
    verbose.emit(Events.STARTED, message=f'emitting to {output_dir}')

    model = json.load(sys.stdin)
    classes = model['classes']
    reject_reserved_field_names(classes, 'python', RESERVED_WORDS, stage='plcc-python-emit')

    output_dir.mkdir(parents=True, exist_ok=True)

    _copy_runtime(output_dir)

    start_class_name = model['start'][0].upper() + model['start'][1:]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `bin/test/units.bash src/plcc/lang/ext/python/emit_test.py -v`
Expected: all tests PASS, including the new one.

- [ ] **Step 6: Document the restriction**

Current text (`docs/language-guide/languages/python.md:190-193`):

```markdown
## Restrictions

- Requires Python 3.12 or later.
- Generated files are overwritten on every emit run — do not edit them directly.
- Sibling generated classes are not automatically in scope; import them explicitly with an `import` fragment.
```

Change to:

```markdown
## Restrictions

- Requires Python 3.12 or later.
- Generated files are overwritten on every emit run — do not edit them directly.
- Sibling generated classes are not automatically in scope; import them explicitly with an `import` fragment.
- A field name that becomes a Python keyword (e.g. `class`, `import`, `is`) is rejected by `plcc-python-emit` — rename the capture. See [Reserved words](../syntactic.md#reserved-words) for details.
```

- [ ] **Step 7: Commit**

```bash
git add src/plcc/lang/ext/python/reserved_words.py src/plcc/lang/ext/python/emit.py \
        src/plcc/lang/ext/python/emit_test.py docs/language-guide/languages/python.md
git commit -m "fix(python): reject field names colliding with Python keywords"
```

---

### Task 5: Wire the check into `plcc-haskell-emit`

**Files:**
- Create: `src/plcc/lang/ext/haskell/reserved_words.py`
- Modify: `src/plcc/lang/ext/haskell/emit.py:43-46`
- Modify: `docs/language-guide/languages/haskell.md:193-198` ("Restrictions" section)
- Test: `src/plcc/lang/ext/haskell/emit_test.py`

**Interfaces:**
- Consumes: `check_reserved_field_names`/`reject_reserved_field_names` from Task 1.
- Produces: `RESERVED_WORDS: frozenset[str]` in `plcc.lang.ext.haskell.reserved_words`.

Note: unlike the other three languages, Haskell's `emit.py` has an `emit(model, output_dir)` function (not `main`'s body directly) that does the work — `main()` just calls it. The wiring point is the top of `emit()`.

- [ ] **Step 1: Write the failing test**

Add to `src/plcc/lang/ext/haskell/emit_test.py`, directly after `test_write_main_contains_specification_error` (the last test in the file, starting at line 362). Reuse the `_run_emit(monkeypatch, tmp_path, model)` helper already defined at the top of this file:

```python


def test_emit_rejects_field_name_colliding_with_reserved_word(tmp_path, monkeypatch, capsys):
    model = _minimal_model()
    model['classes'][0]['fields'] = [{"name": "type", "type": "Token", "is_list": False}]
    with pytest.raises(SystemExit) as exc_info:
        _run_emit(monkeypatch, tmp_path, model)
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert 'plcc-haskell-emit: error:' in captured.err
    assert "field 'type'" in captured.err
    assert list(tmp_path.iterdir()) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bin/test/units.bash src/plcc/lang/ext/haskell/emit_test.py -v`
Expected: `test_emit_rejects_field_name_colliding_with_reserved_word` FAILS (emit succeeds and writes `interpreter.cabal`; no `SystemExit`). All other tests still PASS.

- [ ] **Step 3: Create the reserved-word list**

Create `src/plcc/lang/ext/haskell/reserved_words.py`:

```python
# Haskell 2010 Report §2.4 reserved identifiers. The generated .cabal
# file pins `default-language: Haskell2010` (see _write_cabal in
# emit.py), so GHC-extension-only keywords (mdo, family, forall, ...)
# are deliberately excluded.
RESERVED_WORDS = frozenset({
    'case', 'class', 'data', 'default', 'deriving', 'do', 'else',
    'foreign', 'if', 'import', 'in', 'infix', 'infixl', 'infixr',
    'instance', 'let', 'module', 'newtype', 'of', 'then', 'type',
    'where', '_',
})
```

- [ ] **Step 4: Wire it into `emit.py`**

Current code (`src/plcc/lang/ext/haskell/emit.py:18-21,43-46`):

```python
from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from .validate import validate_fragments

__doc__ = __doc__ + VERBOSE_OPTIONS
```

```python
def emit(model, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    modules = _group_modules(model['classes'])
    _write_cabal(modules, output_dir)
```

Change to:

```python
from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from plcc.lang.reserved_words import reject_reserved_field_names
from .validate import validate_fragments
from .reserved_words import RESERVED_WORDS

__doc__ = __doc__ + VERBOSE_OPTIONS
```

```python
def emit(model, output_dir):
    classes = model['classes']
    reject_reserved_field_names(classes, 'haskell', RESERVED_WORDS, stage='plcc-haskell-emit')

    output_dir.mkdir(parents=True, exist_ok=True)
    modules = _group_modules(classes)
    _write_cabal(modules, output_dir)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `bin/test/units.bash src/plcc/lang/ext/haskell/emit_test.py -v`
Expected: all tests PASS, including the new one.

- [ ] **Step 6: Document the restriction**

Current text (`docs/language-guide/languages/haskell.md:193-198`):

```markdown
## Restrictions

- Requires GHC 9.4 or later and cabal 3.0 or later on `PATH`.
- Fragment class names must be module names (abstract rules or lone concretes) — using a concrete alternative name is a fatal error.
- No `init` or `class` fragment hooks.
- Generated files are overwritten on every emit run — do not edit them directly.
- One module per abstract rule: all concrete alternatives share the abstract rule's `.hs` file.
```

Change to:

```markdown
## Restrictions

- Requires GHC 9.4 or later and cabal 3.0 or later on `PATH`.
- Fragment class names must be module names (abstract rules or lone concretes) — using a concrete alternative name is a fatal error.
- No `init` or `class` fragment hooks.
- Generated files are overwritten on every emit run — do not edit them directly.
- One module per abstract rule: all concrete alternatives share the abstract rule's `.hs` file.
- A field name that becomes a Haskell reserved word (e.g. `type`, `data`, `where`) is rejected by `plcc-haskell-emit` — rename the capture. See [Reserved words](../syntactic.md#reserved-words) for details.
```

- [ ] **Step 7: Commit**

```bash
git add src/plcc/lang/ext/haskell/reserved_words.py src/plcc/lang/ext/haskell/emit.py \
        src/plcc/lang/ext/haskell/emit_test.py docs/language-guide/languages/haskell.md
git commit -m "fix(haskell): reject field names colliding with Haskell reserved words"
```

---

### Task 6: General field-naming documentation in the language guide

**Files:**
- Modify: `docs/language-guide/syntactic.md:129-132`

**Interfaces:** None — documentation only.

- [ ] **Step 1: Insert the new subsection**

Current text (`docs/language-guide/syntactic.md:129-132`):

```markdown
The type of a capture nonterminal field is the class with the same name
as the nonterminal.

### Alternative rules and subclasses
```

Change to:

```markdown
The type of a capture nonterminal field is the class with the same name
as the nonterminal.

### Reserved words

A field name — whether explicit (`:fieldname`) or auto-derived — must not
become an identifier that collides with a reserved word of the semantic
implementation language you're targeting (e.g. `<VAR>` auto-naming field
`var`, which is reserved in JavaScript).

This is enforced per target language, so it is only detected when you
attempt to evaluate the semantics for that language — via `plcc-rep`, or
an explicit `plcc-<lang>-emit` — not during grammar validation
(`plcc-scan`, `plcc-parse`, `plcc-validate-*`), which is language-neutral
and doesn't know which target you'll eventually emit for. A grammar can
therefore pass validation cleanly and still be rejected later, per
target, at emit time.

See each language's guide page ("Restrictions" section) for its exact
reserved-word list.

### Alternative rules and subclasses
```

- [ ] **Step 2: Verify the change**

Run: `grep -n "^### Reserved words" docs/language-guide/syntactic.md`
Expected: one match, between "Capturing nonterminals" and "Alternative rules and subclasses".

- [ ] **Step 3: Commit**

```bash
git add docs/language-guide/syntactic.md
git commit -m "docs(language-guide): document reserved-word field-name restriction"
```

---

### Task 7: End-to-end regression test reproducing issue 163

**Files:**
- Create: `tests/fixtures/js-var-field-reserved-word.plcc`
- Modify: `tests/bats/e2e/plcc-rep.bats`

**Interfaces:**
- Consumes: the fix from Task 2 (this task has no unit-level interface of its own — it's a black-box proof that `plcc-rep` produces a friendly rejection, end-to-end, using this issue's own repro grammar).

- [ ] **Step 1: Create the fixture**

Create `tests/fixtures/js-var-field-reserved-word.plcc`, mirroring issue 163's own repro (`token VAR '[A-Za-z]\w*'` and `<Exp:VarExp> ::= <VAR>`, no explicit field name):

```
token VAR '[A-Za-z]\w*'
skip WS '\s+'
%
<Exp:VarExp> ::= <VAR>
%
javascript
```

- [ ] **Step 2: Add the bats case**

In `tests/bats/e2e/plcc-rep.bats`, add at the end of the file (after the existing `@test "plcc-rep evaluates bare multi-word nonterminal capture field (issue 168)"` case):

```bash

@test "plcc-rep rejects a field name colliding with a JS reserved word (issue 163)" {
    run --separate-stderr bash -c "echo 'x' | plcc-rep --spec='${FIXTURES}/js-var-field-reserved-word.plcc'"
    [ "$status" -ne 0 ]
    [[ "$stderr" == *"plcc-javascript-emit: error:"* ]]
    [[ "$stderr" == *"field 'var'"* ]]
}
```

- [ ] **Step 3: Run the new bats case to verify it passes**

Run: `bin/test/e2e.bash tests/bats/e2e/plcc-rep.bats`
Expected: all cases in the file PASS, including `plcc-rep rejects a field name colliding with a JS reserved word (issue 163)`.

- [ ] **Step 4: Run the full unit suite as a final check**

Run: `bin/test/units.bash`
Expected: all tests PASS (same or greater count than the pre-work baseline of 1191 passed, 3 skipped), 0 failures.

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/js-var-field-reserved-word.plcc tests/bats/e2e/plcc-rep.bats
git commit -m "test(e2e): add regression case for issue 163 (JS reserved-word field name)"
```

---

## After this plan

Issue 163 can be closed as the final commit of this branch, per CLAUDE.md's issue-closing convention:

```bash
bin/issues/close.bash 163
```

This moves `dev-docs/issues/done/163-js-var-field-reserved-word.md` to `dev-docs/issues/done/` and updates `dev-docs/roadmap.md`. Verify with `bin/issues/check.bash` afterward.
