# Language Case Normalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make language matching in the Python and Java emitters case-insensitive so that `% HiPy python`, `% HiPy Python`, and `% HiPy PYTHON` all produce working output.

**Architecture:** Normalize the `language` field to lowercase in `build_model.py` (the boundary between raw spec and the language-neutral model). Update both emitters' section-finder functions to compare against the lowercase canonical form. Note: `.title()` was considered but rejected because `'PlantUML'.title()` → `'Plantuml'` — `.lower()` avoids that problem entirely.

**Tech Stack:** Python, pytest

---

### Task 1: Normalize language to lowercase in build_model

**Files:**
- Modify: `src/plcc/model/build_model.py:119`
- Modify: `src/plcc/model/build_model_test.py`

- [ ] **Step 1: Write the failing test**

Open `src/plcc/model/build_model_test.py` and add this test at the bottom:

```python
def test_semantic_section_language_normalized_to_lowercase():
    spec = {
        "lexical": {"ruleList": []},
        "syntax": {"rules": []},
        "semantics": [{"language": "PYTHON", "tool": "calc", "codeFragmentList": []}]
    }
    model = build_model(spec)
    assert model['semantic_sections'][0]['language'] == 'python'
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
pytest src/plcc/model/build_model_test.py::test_semantic_section_language_normalized_to_lowercase -v
```

Expected: FAIL — `assert 'PYTHON' == 'python'`

- [ ] **Step 3: Implement the normalization**

In `src/plcc/model/build_model.py`, find `_build_semantic_sections` (around line 112). Change the `'language'` line from:

```python
        sections.append({
            'language': s['language'],
```

to:

```python
        sections.append({
            'language': s['language'].lower(),
```

- [ ] **Step 4: Run the new test to verify it passes**

```bash
pytest src/plcc/model/build_model_test.py::test_semantic_section_language_normalized_to_lowercase -v
```

Expected: PASS

- [ ] **Step 5: Update the existing assertion that expected mixed-case `'PlantUML'`**

In `src/plcc/model/build_model_test.py`, find `test_semantic_sections_present`. The fixture `_TRIVIAL_SPEC` has `"language": "PlantUML"`. After normalization, the model will have `"plantuml"`. Update the assertion:

```python
def test_semantic_sections_present():
    model = build_model(_TRIVIAL_SPEC)
    sections = model['semantic_sections']
    assert any(s['tool'] == 'diagram' and s['language'] == 'plantuml' for s in sections)
```

- [ ] **Step 6: Run the full build_model test suite**

```bash
pytest src/plcc/model/build_model_test.py -v
```

Expected: all tests pass

- [ ] **Step 7: Commit**

```bash
git add src/plcc/model/build_model.py src/plcc/model/build_model_test.py
git commit -m "fix(model): normalize language field to lowercase in build_model"
```

---

### Task 2: Fix Python emitter to match lowercase language

**Files:**
- Modify: `src/plcc/lang/ext/python/emit.py:104-108`
- Modify: `src/plcc/lang/ext/python/emit_test.py`

- [ ] **Step 1: Write the failing test**

Open `src/plcc/lang/ext/python/emit_test.py`. The model fixture `_arith_model()` currently has `"language": "Python"`. We need to verify the emitter works when the model language is lowercase (as build_model now produces). Add this test:

```python
def test_emit_class_file_contains_body_fragment_when_language_is_lowercase(tmp_path, monkeypatch):
    model = _arith_model()
    model['semantic_sections'][0]['language'] = 'python'
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    term_py = (tmp_path / 'Term.py').read_text()
    assert 'def eval(self):' in term_py
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
pytest src/plcc/lang/ext/python/emit_test.py::test_emit_class_file_contains_body_fragment_when_language_is_lowercase -v
```

Expected: FAIL — `assert 'def eval(self):' in <content without fragments>`

- [ ] **Step 3: Fix `_find_python_section` to compare lowercase**

In `src/plcc/lang/ext/python/emit.py`, find `_find_python_section` (around line 104). Change:

```python
def _find_python_section(model):
    for s in model.get('semantic_sections', []):
        if s.get('language') == 'Python':
            return s
    return None
```

to:

```python
def _find_python_section(model):
    for s in model.get('semantic_sections', []):
        if s.get('language', '').lower() == 'python':
            return s
    return None
```

- [ ] **Step 4: Run the new test to verify it passes**

```bash
pytest src/plcc/lang/ext/python/emit_test.py::test_emit_class_file_contains_body_fragment_when_language_is_lowercase -v
```

Expected: PASS

- [ ] **Step 5: Run the full Python emit test suite**

```bash
pytest src/plcc/lang/ext/python/emit_test.py -v
```

Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add src/plcc/lang/ext/python/emit.py src/plcc/lang/ext/python/emit_test.py
git commit -m "fix(python-emit): match language case-insensitively in section lookup"
```

---

### Task 3: Fix Java emitter to match lowercase language

**Files:**
- Modify: `src/plcc/lang/ext/java/emit.py:106-110`
- Modify: `src/plcc/lang/ext/java/emit_test.py`

- [ ] **Step 1: Write the failing test**

Open `src/plcc/lang/ext/java/emit_test.py`. Add this test:

```python
def test_body_fragment_pasted_into_class_when_language_is_lowercase(tmp_path, monkeypatch):
    model = _trivial_model()
    model['semantic_sections'][0]['language'] = 'java'
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    program_java = (tmp_path / 'Program.java').read_text()
    assert 'System.out.println(expr.toString())' in program_java
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
pytest src/plcc/lang/ext/java/emit_test.py::test_body_fragment_pasted_into_class_when_language_is_lowercase -v
```

Expected: FAIL — `assert 'System.out.println(expr.toString())' in <content without fragment>`

- [ ] **Step 3: Fix `_find_java_section` to compare lowercase**

In `src/plcc/lang/ext/java/emit.py`, find `_find_java_section` (around line 106). Change:

```python
def _find_java_section(model):
    for s in model.get('semantic_sections', []):
        if s.get('language') == 'Java':
            return s
    return None
```

to:

```python
def _find_java_section(model):
    for s in model.get('semantic_sections', []):
        if s.get('language', '').lower() == 'java':
            return s
    return None
```

- [ ] **Step 4: Run the new test to verify it passes**

```bash
pytest src/plcc/lang/ext/java/emit_test.py::test_body_fragment_pasted_into_class_when_language_is_lowercase -v
```

Expected: PASS

- [ ] **Step 5: Run the full Java emit test suite**

```bash
pytest src/plcc/lang/ext/java/emit_test.py -v
```

Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add src/plcc/lang/ext/java/emit.py src/plcc/lang/ext/java/emit_test.py
git commit -m "fix(java-emit): match language case-insensitively in section lookup"
```

---

### Task 4: Full test suite verification

- [ ] **Step 1: Run all unit tests**

```bash
bash bin/test/units.bash
```

Expected: all 742+ tests pass (0 failures)

- [ ] **Step 2: Commit if any cleanup was needed; otherwise done**

If tests pass with no further changes, the feature is complete.
