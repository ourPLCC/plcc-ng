# LanguageError In Scope By Default Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Auto-inject a `LanguageError` import into every generated class file for Python, Java, and JavaScript so users never have to import it manually.

**Architecture:** Add one static import line to each language's Jinja class template (`class_file.*.jinja`). No emitter Python code changes. The runtime files already define and export `LanguageError` correctly.

**Tech Stack:** Jinja2 templates, pytest, `bin/test/units.bash`

## Global Constraints

- Haskell is out of scope (blocked on issue 131)
- Do not modify `_Start.py`, `_Start.java`, or `_Start.js` (handwritten scaffold, not class template output)
- Do not modify runtime files (`runtime/base.py`, `runtime/LanguageError.java`, `runtime/base.js`)
- TDD: write failing test first, then implement
- Run `bin/test/units.bash` (not pytest directly) to match the project's TDD inner loop

---

## Task 1: Python — inject `LanguageError` import into generated class files

**Files:**
- Modify: `src/plcc/lang/ext/python/templates/class_file.py.jinja`
- Modify: `src/plcc/lang/ext/python/emit_test.py`

**Interfaces:**
- Produces: every generated `<ClassName>.py` contains `from runtime.base import LanguageError`

- [ ] **Step 1: Write the failing test**

  Open `src/plcc/lang/ext/python/emit_test.py` and add this test after `test_emit_class_file_imports_runtime`:

  ```python
  def test_emit_class_file_imports_language_error(tmp_path, monkeypatch):
      monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
      run_main([f'--output={tmp_path}'])
      program_py = (tmp_path / 'Program.py').read_text()
      assert 'from runtime.base import LanguageError' in program_py
  ```

- [ ] **Step 2: Run test to verify it fails**

  ```bash
  bin/test/units.bash src/plcc/lang/ext/python/emit_test.py::test_emit_class_file_imports_language_error
  ```

  Expected: FAIL — `AssertionError` (the import line is not yet in the generated file)

- [ ] **Step 3: Add the import line to the template**

  Open `src/plcc/lang/ext/python/templates/class_file.py.jinja`. The current lines 3–4 are:

  ```
  import runtime.base as _plcc
  {% if cls.extends %}from {{ cls.extends }} import {{ cls.extends }}
  ```

  Change them to:

  ```
  import runtime.base as _plcc
  from runtime.base import LanguageError
  {% if cls.extends %}from {{ cls.extends }} import {{ cls.extends }}
  ```

- [ ] **Step 4: Run test to verify it passes**

  ```bash
  bin/test/units.bash src/plcc/lang/ext/python/emit_test.py::test_emit_class_file_imports_language_error
  ```

  Expected: PASS

- [ ] **Step 5: Run the full Python emit test suite to check for regressions**

  ```bash
  bin/test/units.bash src/plcc/lang/ext/python/emit_test.py
  ```

  Expected: all tests pass

- [ ] **Step 6: Commit**

  ```bash
  git add src/plcc/lang/ext/python/templates/class_file.py.jinja \
          src/plcc/lang/ext/python/emit_test.py
  git commit -m "feat(python-emit): auto-inject LanguageError import into generated class files"
  ```

---

## Task 2: Java — inject `LanguageError` import into generated class files

**Files:**
- Modify: `src/plcc/lang/ext/java/templates/class_file.java.jinja`
- Modify: `src/plcc/lang/ext/java/emit_test.py`

**Interfaces:**
- Produces: every generated `<ClassName>.java` contains `import runtime.LanguageError;`

- [ ] **Step 1: Write the failing test**

  Open `src/plcc/lang/ext/java/emit_test.py` and add this test (after the existing runtime/import tests, around line 116):

  ```python
  def test_emit_class_file_imports_language_error(tmp_path, monkeypatch):
      monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
      run_main([f'--output={tmp_path}'])
      program_java = (tmp_path / 'Program.java').read_text()
      assert 'import runtime.LanguageError;' in program_java
  ```

- [ ] **Step 2: Run test to verify it fails**

  ```bash
  bin/test/units.bash src/plcc/lang/ext/java/emit_test.py::test_emit_class_file_imports_language_error
  ```

  Expected: FAIL — `AssertionError`

- [ ] **Step 3: Add the import line to the template**

  Open `src/plcc/lang/ext/java/templates/class_file.java.jinja`. The current lines 3–6 are:

  ```
  import java.util.List;
  import java.util.Map;
  import runtime.Token;
  ```

  Change them to:

  ```
  import java.util.List;
  import java.util.Map;
  import runtime.Token;
  import runtime.LanguageError;
  ```

- [ ] **Step 4: Run test to verify it passes**

  ```bash
  bin/test/units.bash src/plcc/lang/ext/java/emit_test.py::test_emit_class_file_imports_language_error
  ```

  Expected: PASS

- [ ] **Step 5: Run the full Java emit test suite to check for regressions**

  ```bash
  bin/test/units.bash src/plcc/lang/ext/java/emit_test.py
  ```

  Expected: all tests pass

- [ ] **Step 6: Commit**

  ```bash
  git add src/plcc/lang/ext/java/templates/class_file.java.jinja \
          src/plcc/lang/ext/java/emit_test.py
  git commit -m "feat(java-emit): auto-inject LanguageError import into generated class files"
  ```

---

## Task 3: JavaScript — inject `LanguageError` into the runtime base destructure

**Files:**
- Modify: `src/plcc/lang/ext/javascript/templates/class_file.js.jinja`
- Modify: `src/plcc/lang/ext/javascript/emit_test.py`

**Interfaces:**
- Produces: every generated `<ClassName>.js` contains `LanguageError` in the `require('./runtime/base')` destructure

- [ ] **Step 1: Write the failing test**

  Open `src/plcc/lang/ext/javascript/emit_test.py` and add this test (after `test_emit_copies_runtime_directory`, around line 122):

  ```python
  def test_emit_class_file_imports_language_error(tmp_path, monkeypatch):
      monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
      run_main([f'--output={tmp_path}'])
      program_js = (tmp_path / 'Program.js').read_text()
      assert "{ Node, Token, LanguageError } = require('./runtime/base')" in program_js
  ```

- [ ] **Step 2: Run test to verify it fails**

  ```bash
  bin/test/units.bash src/plcc/lang/ext/javascript/emit_test.py::test_emit_class_file_imports_language_error
  ```

  Expected: FAIL — `AssertionError`

- [ ] **Step 3: Update the destructure in the template**

  Open `src/plcc/lang/ext/javascript/templates/class_file.js.jinja`. Line 2 currently reads:

  ```
  {% endfor %}const { Node, Token } = require('./runtime/base');
  ```

  Change it to:

  ```
  {% endfor %}const { Node, Token, LanguageError } = require('./runtime/base');
  ```

- [ ] **Step 4: Run test to verify it passes**

  ```bash
  bin/test/units.bash src/plcc/lang/ext/javascript/emit_test.py::test_emit_class_file_imports_language_error
  ```

  Expected: PASS

- [ ] **Step 5: Run the full JavaScript emit test suite to check for regressions**

  ```bash
  bin/test/units.bash src/plcc/lang/ext/javascript/emit_test.py
  ```

  Expected: all tests pass

- [ ] **Step 6: Commit**

  ```bash
  git add src/plcc/lang/ext/javascript/templates/class_file.js.jinja \
          src/plcc/lang/ext/javascript/emit_test.py
  git commit -m "feat(javascript-emit): auto-inject LanguageError import into generated class files"
  ```

---

## Task 4: Full test suite verification

- [ ] **Step 1: Run all unit tests**

  ```bash
  bin/test/units.bash
  ```

  Expected: all tests pass (1165+ passed, 0 failed)

- [ ] **Step 2: Run command-level bats tests**

  ```bash
  bin/test/commands.bash
  ```

  Expected: all tests pass

- [ ] **Step 3: If both pass, the feature is complete**

  No further tasks. Haskell support is tracked in issue 131.
