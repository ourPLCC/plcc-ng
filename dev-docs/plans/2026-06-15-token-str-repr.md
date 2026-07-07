# Token `__str__` and `__repr__` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `__str__` and `__repr__` to the Python runtime `Token` class so that string conversion returns the lexeme.

**Architecture:** Single edit to `runtime/base.py` — add two one-line methods to the existing `Token` class. Tests go in the co-located `base_test.py`. No template changes, no Java changes (Java already has `toString()` returning `lexeme`).

**Tech Stack:** Python, pytest (via `bin/test/units.bash`)

---

### Task 1: Add `__str__` to `Token`

**Files:**
- Modify: `src/plcc/lang/ext/python/runtime/base_test.py`
- Modify: `src/plcc/lang/ext/python/runtime/base.py`

- [ ] **Step 1: Write the failing test**

Add to `src/plcc/lang/ext/python/runtime/base_test.py`:

```python
def test_token_str_returns_lexeme():
    t = Token(kind='NUM', lexeme='42')
    assert str(t) == '42'
```

- [ ] **Step 2: Run the test to confirm it fails**

```bash
bin/test/units.bash src/plcc/lang/ext/python/runtime/base_test.py::test_token_str_returns_lexeme -v
```

Expected: FAIL — `str(t)` returns something like `<runtime.base.Token object at 0x...>`, not `'42'`.

- [ ] **Step 3: Add `__str__` to `Token`**

Edit `src/plcc/lang/ext/python/runtime/base.py` so the class reads:

```python
class Token:
    def __init__(self, kind, lexeme):
        self.kind = kind
        self.lexeme = lexeme

    def __str__(self):
        return self.lexeme
```

- [ ] **Step 4: Run the test to confirm it passes**

```bash
bin/test/units.bash src/plcc/lang/ext/python/runtime/base_test.py::test_token_str_returns_lexeme -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/lang/ext/python/runtime/base.py src/plcc/lang/ext/python/runtime/base_test.py
git commit -m "feat(086): Token.__str__ returns lexeme"
```

---

### Task 2: Add `__repr__` to `Token`

**Files:**
- Modify: `src/plcc/lang/ext/python/runtime/base_test.py`
- Modify: `src/plcc/lang/ext/python/runtime/base.py`

- [ ] **Step 1: Write the failing test**

Add to `src/plcc/lang/ext/python/runtime/base_test.py`:

```python
def test_token_repr_returns_lexeme():
    t = Token(kind='NUM', lexeme='42')
    assert repr(t) == '42'
```

- [ ] **Step 2: Run the test to confirm it fails**

```bash
bin/test/units.bash src/plcc/lang/ext/python/runtime/base_test.py::test_token_repr_returns_lexeme -v
```

Expected: FAIL — `repr(t)` returns something like `<runtime.base.Token object at 0x...>`, not `'42'`.

- [ ] **Step 3: Add `__repr__` to `Token`**

Edit `src/plcc/lang/ext/python/runtime/base.py` so the class reads:

```python
class Token:
    def __init__(self, kind, lexeme):
        self.kind = kind
        self.lexeme = lexeme

    def __str__(self):
        return self.lexeme

    def __repr__(self):
        return self.lexeme
```

- [ ] **Step 4: Run the test to confirm it passes**

```bash
bin/test/units.bash src/plcc/lang/ext/python/runtime/base_test.py::test_token_repr_returns_lexeme -v
```

Expected: PASS.

- [ ] **Step 5: Run the full unit suite**

```bash
bin/test/units.bash
```

Expected: all tests pass (was 981 at baseline), output clean.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/lang/ext/python/runtime/base.py src/plcc/lang/ext/python/runtime/base_test.py
git commit -m "feat(086): Token.__repr__ returns lexeme"
```
