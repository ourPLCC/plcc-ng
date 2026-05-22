# Issue 015: _Start Default Generated Code Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate a `_Start` class alongside other emitted files so that grammars with no semantics section produce code that compiles and runs without crashing.

**Architecture:** Both `plcc-python-emit` and `plcc-java-emit` detect the start class from `model['start']`, set its `extends` to `'_Start'` before template rendering, and write a fixed `_Start.py` / `_Start.java` to the output directory. The existing class templates already handle a non-null `extends` correctly — no template changes are needed. `_Start` provides a default `_run()` / `$run()` that prints `str(self)` / `this.toString()` to stdout.

**Tech Stack:** Python, Jinja2, pytest, bats, Java

> **Working directory:** All commands run from `.worktrees/015-start-class-default/` unless noted.

---

## Task 1: Python emitter — unit tests and implementation

**Files:**

- Modify: `src/plcc/lang/ext/python/emit.py`
- Modify: `src/plcc/lang/ext/python/emit_test.py`

- [ ] **Step 1: Add `_minimal_model` fixture and four failing tests to `emit_test.py`**

Add after the closing `}` of `_arith_model()` (around line 43):

```python
def _minimal_model():
    return {
        "start": "program",
        "classes": [
            {"name": "Program", "abstract": False, "extends": None,
             "fields": [], "rule_name": "program"},
        ],
        "semantic_sections": [],
    }


def test_emit_generates_start_py(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    assert (tmp_path / '_Start.py').exists()


def test_start_class_extends_start(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    program_py = (tmp_path / 'Program.py').read_text()
    assert 'from _Start import _Start' in program_py
    assert 'class Program(_Start' in program_py


def test_non_start_class_does_not_extend_start(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    term_py = (tmp_path / 'Term.py').read_text()
    assert '_Start' not in term_py


def test_start_class_with_semantics_still_extends_start(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    program_py = (tmp_path / 'Program.py').read_text()
    assert 'from _Start import _Start' in program_py
    assert 'class Program(_Start' in program_py
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
bin/test/units.bash src/plcc/lang/ext/python/emit_test.py -v -k "start"
```

Expected: 4 failures — `_Start.py` not generated, `Program` still extends `_plcc.Node`.

- [ ] **Step 3: Add `_START_PY` constant and update `main()` in `emit.py`**

At module level (after `_DEFAULT_ENTRY_POINT = '_run'`), add:

```python
_START_PY = """\
import runtime.base as _plcc


class _Start(_plcc.Node):
    def _run(self):
        print(str(self))
"""
```

In `main()`, after `classes = model['classes']`, add:

```python
    start_class_name = model['start'][0].upper() + model['start'][1:]
```

In the class loop, replace:

```python
    for cls in classes:
        frags = fragments_by_class.get(cls['name'], [])
```

with:

```python
    for cls in classes:
        cls = dict(cls)
        if cls['name'] == start_class_name and cls['extends'] is None:
            cls['extends'] = '_Start'
        frags = fragments_by_class.get(cls['name'], [])
```

After the class loop (before the file-fragment loop), add:

```python
    (output_dir / '_Start.py').write_text(_START_PY)
```

- [ ] **Step 4: Run all Python emit tests to confirm they pass**

```bash
bin/test/units.bash src/plcc/lang/ext/python/emit_test.py -v
```

Expected: all tests pass, including the 4 new ones.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/lang/ext/python/emit.py src/plcc/lang/ext/python/emit_test.py
git commit -m "$(cat <<'EOF'
feat(python-emit): generate _Start.py and wire start class to extend it

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Java emitter — unit tests and implementation

**Files:**

- Modify: `src/plcc/lang/ext/java/emit.py`
- Modify: `src/plcc/lang/ext/java/emit_test.py`

- [ ] **Step 1: Add `_minimal_model` fixture and four failing tests to `emit_test.py`**

Add after the closing `}` of `_trivial_model()` (around line 32):

```python
def _minimal_model():
    return {
        "start": "program",
        "classes": [
            {"name": "Program", "abstract": False, "extends": None,
             "rule_name": "program", "fields": []},
        ],
        "semantic_sections": [],
    }


def test_emit_generates_start_java(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    assert (tmp_path / '_Start.java').exists()


def test_start_class_extends_start(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    program_java = (tmp_path / 'Program.java').read_text()
    assert 'extends _Start' in program_java


def test_non_start_class_does_not_extend_start(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_trivial_model())))
    run_main([f'--output={tmp_path}'])
    expr_java = (tmp_path / 'Expr.java').read_text()
    assert 'extends _Start' not in expr_java


def test_start_class_with_semantics_still_extends_start(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_trivial_model())))
    run_main([f'--output={tmp_path}'])
    program_java = (tmp_path / 'Program.java').read_text()
    assert 'extends _Start' in program_java
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
bin/test/units.bash src/plcc/lang/ext/java/emit_test.py -v -k "start"
```

Expected: 4 failures — `_Start.java` not generated, `Program` still says `extends runtime.Node`.

- [ ] **Step 3: Add `_START_JAVA` constant and update `main()` in `emit.py`**

At module level (after `_DEFAULT_ENTRY_POINT = '$run'`), add:

```python
_START_JAVA = """\
public abstract class _Start extends runtime.Node {
    public void $run() {
        System.out.println(this.toString());
    }
}
"""
```

In `main()`, after `classes = model['classes']`, add:

```python
    start_class_name = model['start'][0].upper() + model['start'][1:]
```

In the class loop, replace:

```python
    for cls in classes:
        frags = fragments_by_class.get(cls['name'], [])
```

with:

```python
    for cls in classes:
        cls = dict(cls)
        if cls['name'] == start_class_name and cls['extends'] is None:
            cls['extends'] = '_Start'
        frags = fragments_by_class.get(cls['name'], [])
```

After the class loop (before the file-fragment loop), add:

```python
    (output_dir / '_Start.java').write_text(_START_JAVA)
```

- [ ] **Step 4: Run all Java emit tests to confirm they pass**

```bash
bin/test/units.bash src/plcc/lang/ext/java/emit_test.py -v
```

Expected: all tests pass, including the 4 new ones.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/lang/ext/java/emit.py src/plcc/lang/ext/java/emit_test.py
git commit -m "$(cat <<'EOF'
feat(java-emit): generate _Start.java and wire start class to extend it

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Python integration test — no-semantics grammar emits and runs

**Files:**

- Modify: `tests/bats/integration/python-emit.bats`

The fixture `tests/fixtures/trivial.plcc` has no semantics section and is used here as the no-semantics grammar. Its `setup()` sets `FIXTURES` so tests in this file can reference it directly.

- [ ] **Step 1: Add three tests at the end of `python-emit.bats`**

```bash
@test "no-semantics grammar generates _Start.py" {
    NO_SEM_DIR="$(mktemp -d)"
    trap "rm -rf '${NO_SEM_DIR}'" EXIT
    plcc-spec "${FIXTURES}/trivial.plcc" | plcc-model | plcc-python-emit --output="${NO_SEM_DIR}"
    [ -f "${NO_SEM_DIR}/_Start.py" ]
}

@test "no-semantics grammar: start class extends _Start" {
    NO_SEM_DIR="$(mktemp -d)"
    trap "rm -rf '${NO_SEM_DIR}'" EXIT
    plcc-spec "${FIXTURES}/trivial.plcc" | plcc-model | plcc-python-emit --output="${NO_SEM_DIR}"
    grep 'class Program(_Start' "${NO_SEM_DIR}/Program.py"
}

@test "no-semantics grammar: main.py exits 0 on empty input" {
    NO_SEM_DIR="$(mktemp -d)"
    trap "rm -rf '${NO_SEM_DIR}'" EXIT
    plcc-spec "${FIXTURES}/trivial.plcc" | plcc-model | plcc-python-emit --output="${NO_SEM_DIR}"
    run python3 "${NO_SEM_DIR}/main.py" <<< ""
    [ "$status" -eq 0 ]
}
```

- [ ] **Step 2: Run the full python-emit integration suite (includes the new tests)**

```bash
bats tests/bats/integration/python-emit.bats
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add tests/bats/integration/python-emit.bats
git commit -m "$(cat <<'EOF'
test(integration): verify no-semantics grammar emits and runs for Python

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Java integration test — no-semantics grammar emits, compiles, and runs

**Files:**

- Modify: `tests/bats/integration/java-emit.bats`

`setup()` in this file already skips all tests when `javac` is unavailable, so the new tests do not need their own JDK check. `FIXTURES` is available from `setup()`.

- [ ] **Step 1: Add three tests at the end of `java-emit.bats`**

```bash
@test "no-semantics grammar generates _Start.java" {
    NO_SEM_DIR="$(mktemp -d)"
    trap "rm -rf '${NO_SEM_DIR}'" EXIT
    plcc-spec "${FIXTURES}/trivial.plcc" | plcc-model | plcc-java-emit --output="${NO_SEM_DIR}"
    [ -f "${NO_SEM_DIR}/_Start.java" ]
}

@test "no-semantics grammar: start class extends _Start" {
    NO_SEM_DIR="$(mktemp -d)"
    trap "rm -rf '${NO_SEM_DIR}'" EXIT
    plcc-spec "${FIXTURES}/trivial.plcc" | plcc-model | plcc-java-emit --output="${NO_SEM_DIR}"
    grep 'extends _Start' "${NO_SEM_DIR}/Program.java"
}

@test "no-semantics grammar: compiles and runs on empty input" {
    NO_SEM_DIR="$(mktemp -d)"
    trap "rm -rf '${NO_SEM_DIR}'" EXIT
    plcc-spec "${FIXTURES}/trivial.plcc" | plcc-model | plcc-java-emit --output="${NO_SEM_DIR}"
    plcc-java-build --output="${NO_SEM_DIR}"
    run bash -c "echo '' | plcc-java-run --output='${NO_SEM_DIR}'"
    [ "$status" -eq 0 ]
}
```

- [ ] **Step 2: Run the new tests**

```bash
bin/test/integration.bash --filter "no-semantics" tests/bats/integration/java-emit.bats
```

Expected: 3 tests pass (or skipped if JDK unavailable).

- [ ] **Step 3: Run the full java-emit integration suite to check for regressions**

```bash
bin/test/integration.bash tests/bats/integration/java-emit.bats
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add tests/bats/integration/java-emit.bats
git commit -m "$(cat <<'EOF'
test(integration): verify no-semantics grammar emits and runs for Java

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Mark issue done and run full functional suite

**Files:**

- Move: `docs/issues/015-default-generated-code-should-run.md` → `docs/issues/done/015-default-generated-code-should-run.md`

- [ ] **Step 1: Run the full functional test suite**

```bash
bin/test/functional.bash
```

Expected: all tests pass.

- [ ] **Step 2: Move the issue file to done**

```bash
git mv docs/issues/015-default-generated-code-should-run.md docs/issues/done/015-default-generated-code-should-run.md
```

- [ ] **Step 3: Commit**

```bash
git commit -m "$(cat <<'EOF'
docs(issues): move issue 015 to done [skip ci]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```
