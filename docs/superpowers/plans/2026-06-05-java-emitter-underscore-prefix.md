# Java Emitter Underscore Prefix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename `$run` to `_run` in the Java emitter so it matches the Python emitter's naming convention.

**Architecture:** Mechanical rename across 4 files — the emitter source, its unit tests, a fixture grammar, and an integration test. No structural changes. `Main.java` already passes `entry_point` via Jinja, so changing `_DEFAULT_ENTRY_POINT` is all that's needed on the generation side.

**Tech Stack:** Python (emitter + unit tests), bats (integration tests), Java (generated template code)

**Worktree:** `.worktrees/057-java-emitter-underscore-prefix` — run all commands from that directory.

---

### Task 1: Add a failing test, update the emitter, verify unit tests pass

**Files:**
- Modify: `src/plcc/lang/ext/java/emit_test.py`
- Modify: `src/plcc/lang/ext/java/emit.py:25-33`

- [ ] **Step 1: Add a failing test for `_run` in `_Start.java`**

Open `src/plcc/lang/ext/java/emit_test.py` and add this test after `test_start_class_extends_start` (around line 57):

```python
def test_start_java_uses_underscore_run(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    start_java = (tmp_path / '_Start.java').read_text()
    assert 'public void _run()' in start_java
    assert '$run' not in start_java
```

- [ ] **Step 2: Run the new test to confirm it fails**

```bash
python -m pytest src/plcc/lang/ext/java/emit_test.py::test_start_java_uses_underscore_run -v
```

Expected: FAIL — `AssertionError` because `_Start.java` currently contains `$run`.

- [ ] **Step 3: Update `emit.py` — rename `$run` to `_run`**

In `src/plcc/lang/ext/java/emit.py`, make two changes:

Change line 25:
```python
_DEFAULT_ENTRY_POINT = '_run'
```

Change line 29 (inside `_START_JAVA`):
```python
_START_JAVA = """\
public abstract class _Start extends runtime.Node {
    public void _run() {
        System.out.println(this.toString());
    }
}
"""
```

- [ ] **Step 4: Update the body fragment test data in `emit_test.py`**

In `_trivial_model()` (around line 27), update the fragment body:

```python
{"class_name": "Program", "kind": "body",
 "body": "    public void _run() {\n        System.out.println(expr.toString());\n    }"},
```

- [ ] **Step 5: Run all unit tests to confirm they pass**

```bash
python -m pytest src/plcc/lang/ext/java/emit_test.py -v
```

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/lang/ext/java/emit.py src/plcc/lang/ext/java/emit_test.py
git commit -m "feat(java-emitter): rename \$run to _run to match Python convention"
```

---

### Task 2: Update the fixture grammar and integration test name

**Files:**
- Modify: `tests/fixtures/trivial-java.plcc:8`
- Modify: `tests/bats/integration/java-emit.bats:42`

- [ ] **Step 1: Update the fixture grammar**

In `tests/fixtures/trivial-java.plcc`, change line 8:

```
    public void _run() {
        System.out.println(num.toString());
    }
```

- [ ] **Step 2: Update the bats test name**

In `tests/bats/integration/java-emit.bats`, change the test name on line 42:

```bash
@test "run outputs token lexeme from void _run()" {
```

- [ ] **Step 3: Run the integration tests**

```bash
bin/test/commands.bash 2>&1 | grep -E 'java-emit|PASS|FAIL|ok|not ok' | head -30
```

Expected: All `java-emit` tests pass. (If `javac` is not available, they will be skipped — that is acceptable.)

- [ ] **Step 4: Confirm no `$run` remains in the Java emitter or its tests**

```bash
grep -rn '\$run' src/plcc/lang/ext/java/ tests/fixtures/trivial-java.plcc tests/bats/integration/java-emit.bats
```

Expected: No output.

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/trivial-java.plcc tests/bats/integration/java-emit.bats
git commit -m "test(java-emitter): update fixture and bats test name for _run rename"
```
