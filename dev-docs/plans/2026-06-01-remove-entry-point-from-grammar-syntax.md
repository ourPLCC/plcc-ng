# Remove entry_point from Grammar Syntax Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the `entry_point` field from the PLCC grammar divider syntax and all layers that carry it, replacing custom entry point lookup in emitters with a direct reference to `_DEFAULT_ENTRY_POINT`, and raising a parse error when a divider line contains a third token.

**Architecture:** The `entry_point` value flows through five layers: divider parsing → `Divider` dataclass → `SemanticSpec` dataclass → model dict → emitters. Tasks strip it layer by layer from the outside in, keeping tests green at every commit. The parse error for extra tokens is added first so nothing new can introduce the field going forward.

**Tech Stack:** Python, pytest (`bin/test/units.bash`), bats (`bin/test/integration.bash`)

---

### Task 1: Add parse error for extra tokens on a divider line

This introduces `TooManyDividerTokensError` and tightens the `toolLanguage` regex to detect — and reject — a third token. Old tests that asserted the field was captured are deleted; a new test asserts the error is raised.

**Files:**
- Create: `src/plcc/spec/rough/TooManyDividerTokensError.py`
- Modify: `src/plcc/spec/rough/parse_dividers.py`
- Modify: `src/plcc/spec/rough/__init__.py`
- Modify: `src/plcc/spec/rough/parse_dividers_test.py`

- [ ] **Step 1: Write the failing test**

Add to `src/plcc/spec/rough/parse_dividers_test.py`:

```python
from pytest import raises
from .TooManyDividerTokensError import TooManyDividerTokensError

def test_divider_with_three_tokens_is_an_error():
    with raises(TooManyDividerTokensError):
        list(parse_dividers(list(lines.parseLines('% java python evaluate'))))
```

- [ ] **Step 2: Run test to verify it fails**

```bash
bin/test/units.bash src/plcc/spec/rough/parse_dividers_test.py::test_divider_with_three_tokens_is_an_error -v
```

Expected: FAIL — `TooManyDividerTokensError` does not exist.

- [ ] **Step 3: Create the error class**

Create `src/plcc/spec/rough/TooManyDividerTokensError.py`:

```python
from ..SpecError import SpecError


class TooManyDividerTokensError(SpecError):
    ...
```

- [ ] **Step 4: Run test to verify it still fails (import passes, but not raised yet)**

```bash
bin/test/units.bash src/plcc/spec/rough/parse_dividers_test.py::test_divider_with_three_tokens_is_an_error -v
```

Expected: FAIL — error is not raised.

- [ ] **Step 5: Update `parse_dividers.py` to detect and raise the error**

Replace the `_compilePatternDictionary`, `_getEntryPoint`, `_parseDivider`, and `_createDivider` methods, and add the import. Full updated file:

```python
import re

from ...lines import Line
from .Divider import Divider
from .TooManyDividerTokensError import TooManyDividerTokensError


def parse_dividers(lines):
    return DividerParser().parse(lines)


class DividerParser:
    def __init__(self):
        self.lines = None
        self.defaultToolPath = "Java"
        self.defaultLanguage = "Java"
        self.patterns = self._compilePatternDictionary()

    def parse(self, lines):
        self.lines = lines
        if not self.lines:
            return
        for line in self.lines:
            if self._isLine(line) and self._isDivider(line.string):
                yield self._parseDivider(line)
            else:
                yield line

    def _parseDivider(self, line):
        matchToolLanguage = self._matchToolLanguage(line.string)
        matchToolOnly = self._matchToolOnly(line.string)
        tool = self._getTool(matchToolLanguage, matchToolOnly)
        language = self._getLanguage(matchToolLanguage, matchToolOnly)
        if matchToolLanguage and matchToolLanguage['extra']:
            col = line.string.index(matchToolLanguage['extra']) + 1
            raise TooManyDividerTokensError(
                line=line,
                column=col,
                message=f"unexpected token '{matchToolLanguage['extra']}' on divider line",
            )
        return self._createDivider(tool, language, line)

    def _getTool(self, matchToolLanguage, matchToolOnly):
        if matchToolLanguage:
            return matchToolLanguage['tool']
        elif matchToolOnly:
            return matchToolOnly['tool']
        else:
            return self.defaultToolPath

    def _getLanguage(self, matchToolLanguage, matchToolOnly):
        if matchToolLanguage:
            return matchToolLanguage['language']
        elif matchToolOnly:
            return matchToolOnly['tool']
        else:
            return self.defaultLanguage

    def _isLine(self, line):
        return isinstance(line, Line)

    def _isDivider(self, string):
        return bool(self.patterns['divider'].match(string))

    def _matchToolLanguage(self, string):
        return self.patterns['toolLanguage'].match(string)

    def _matchToolOnly(self, string):
        return self.patterns['toolOnly'].match(string)

    def _createDivider(self, toolName, languageName, line):
        return Divider(tool=toolName, language=languageName, line=line)

    def _compilePatternDictionary(self):
        return {
            'divider': re.compile(r'^%(?:\s.*)?$'),
            'toolLanguage': re.compile(r'^%\s*(?P<tool>\S+)\s+(?P<language>\S+)(?:\s+(?P<extra>\S+))?.*$'),
            'toolOnly': re.compile(r'^%\s*(?P<tool>\S+)\s*$')
        }
```

- [ ] **Step 6: Run test to verify the new test passes**

```bash
bin/test/units.bash src/plcc/spec/rough/parse_dividers_test.py::test_divider_with_three_tokens_is_an_error -v
```

Expected: PASS.

- [ ] **Step 7: Export the new error from `__init__.py`**

In `src/plcc/spec/rough/__init__.py`, add:

```python
from .TooManyDividerTokensError import TooManyDividerTokensError
```

- [ ] **Step 8: Delete the old entry_point tests and clean up `make_divider`**

In `src/plcc/spec/rough/parse_dividers_test.py`:

- Delete `test_one_divider_with_entry_point`
- Delete `test_one_divider_without_entry_point_has_null`
- Remove the `entry_point=None` default parameter from `make_divider` and remove it from the `Divider(...)` call inside `make_divider`

Updated `make_divider`:

```python
def make_divider(tool, language, line):
    return Divider(tool=tool, language=language, line=line)
```

Update every call to `make_divider` in the test file that previously passed no `entry_point` to drop the now-absent parameter (they already don't pass it, so the calls are fine once the signature changes).

- [ ] **Step 9: Run the full parse_dividers test file**

```bash
bin/test/units.bash src/plcc/spec/rough/parse_dividers_test.py -v
```

Expected: all pass.

- [ ] **Step 10: Commit**

```bash
git add src/plcc/spec/rough/TooManyDividerTokensError.py \
        src/plcc/spec/rough/parse_dividers.py \
        src/plcc/spec/rough/__init__.py \
        src/plcc/spec/rough/parse_dividers_test.py
git commit -m "feat(rough): raise error for extra token on divider line; remove entry_point parsing"
```

---

### Task 2: Remove `entry_point` from `Divider` and `SemanticSpec` dataclasses

`Divider._createDivider` no longer passes `entry_point` (Task 1), so the field is always absent. Now remove it from both dataclasses and from `parse_semantic_spec`.

**Files:**
- Modify: `src/plcc/spec/rough/Divider.py`
- Modify: `src/plcc/spec/semantics/SemanticSpec.py`
- Modify: `src/plcc/spec/semantics/parse_semantic_spec.py`

- [ ] **Step 1: Remove `entry_point` from `Divider`**

Replace `src/plcc/spec/rough/Divider.py` content:

```python
from dataclasses import dataclass

from ...lines import Line


@dataclass
class Divider:
    tool: str
    language: str
    line: Line
```

- [ ] **Step 2: Remove `entry_point` from `SemanticSpec`**

Replace `src/plcc/spec/semantics/SemanticSpec.py` content:

```python
from dataclasses import dataclass

from .CodeFragment import CodeFragment


@dataclass
class SemanticSpec:
    language: str
    tool: str
    codeFragmentList: list[CodeFragment]
```

- [ ] **Step 3: Remove `entry_point` from `parse_semantic_spec`**

Replace `src/plcc/spec/semantics/parse_semantic_spec.py` content:

```python
from ...lines import Line
from ..rough import Block, Divider
from .parse_code_fragments import parse_code_fragments
from .SemanticSpec import SemanticSpec


def parse_semantic_spec(semantic_spec: list[Divider | Line | Block]) -> SemanticSpec:
    divider = semantic_spec[0]
    codeFragmentList = parse_code_fragments(semantic_spec[1:])
    return SemanticSpec(
        language=divider.language,
        tool=divider.tool,
        codeFragmentList=codeFragmentList,
    )
```

- [ ] **Step 4: Run unit tests**

```bash
bin/test/units.bash -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/spec/rough/Divider.py \
        src/plcc/spec/semantics/SemanticSpec.py \
        src/plcc/spec/semantics/parse_semantic_spec.py
git commit -m "refactor(spec): remove entry_point from Divider and SemanticSpec"
```

---

### Task 3: Remove `entry_point` from `build_model`

The model dict no longer needs to carry `entry_point`. Remove it from `_build_semantic_sections` and delete the two tests that verified pass-through behavior.

**Files:**
- Modify: `src/plcc/model/build_model.py`
- Modify: `src/plcc/model/build_model_test.py`

- [ ] **Step 1: Delete the two entry_point tests from `build_model_test.py`**

Remove `test_semantic_section_entry_point_null_when_absent` and `test_semantic_section_entry_point_when_present` (and their `# ---- entry_point pass-through ----` comment block).

- [ ] **Step 2: Run unit tests to confirm no other tests broke**

```bash
bin/test/units.bash src/plcc/model/build_model_test.py -v
```

Expected: all pass (the two deleted tests no longer run).

- [ ] **Step 3: Remove `entry_point` from `_build_semantic_sections` in `build_model.py`**

In `src/plcc/model/build_model.py`, find `_build_semantic_sections`. Change the `sections.append` dict from:

```python
        sections.append({
            'language': s['language'].lower(),
            'tool': s['tool'],
            'entry_point': s.get('entry_point'),
            'fragments': fragments,
        })
```

to:

```python
        sections.append({
            'language': s['language'].lower(),
            'tool': s['tool'],
            'fragments': fragments,
        })
```

- [ ] **Step 4: Run unit tests**

```bash
bin/test/units.bash src/plcc/model/build_model_test.py -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/model/build_model.py \
        src/plcc/model/build_model_test.py
git commit -m "refactor(model): remove entry_point from semantic section model dict"
```

---

### Task 4: Simplify the Python emitter

Replace the `(section.get('entry_point') if section else None) or _DEFAULT_ENTRY_POINT` expression with `_DEFAULT_ENTRY_POINT` directly, remove `entry_point` from the model fixture, and delete the two now-redundant tests.

**Files:**
- Modify: `src/plcc/lang/ext/python/emit.py`
- Modify: `src/plcc/lang/ext/python/emit_test.py`

- [ ] **Step 1: Delete the two entry_point tests from `emit_test.py`**

Remove `test_emit_main_py_contains_entry_point` and `test_emit_main_py_entry_point_defaults_to_run_when_null`.

- [ ] **Step 2: Remove `entry_point` key from `_arith_model()` fixture**

In `_arith_model()`, inside `semantic_sections`, change:

```python
        {
            "language": "Python",
            "tool": "calculate",
            "entry_point": "_run",
            "fragments": [ ... ]
        }
```

to:

```python
        {
            "language": "Python",
            "tool": "calculate",
            "fragments": [ ... ]
        }
```

- [ ] **Step 3: Run emit tests to confirm no failures**

```bash
bin/test/units.bash src/plcc/lang/ext/python/emit_test.py -v
```

Expected: all pass.

- [ ] **Step 4: Simplify `emit.py`**

In `src/plcc/lang/ext/python/emit.py`, replace:

```python
    entry_point = (section.get('entry_point') if section else None) or _DEFAULT_ENTRY_POINT
```

with:

```python
    entry_point = _DEFAULT_ENTRY_POINT
```

- [ ] **Step 5: Run emit tests**

```bash
bin/test/units.bash src/plcc/lang/ext/python/emit_test.py -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/lang/ext/python/emit.py \
        src/plcc/lang/ext/python/emit_test.py
git commit -m "refactor(python-emit): use _DEFAULT_ENTRY_POINT directly; remove entry_point tests"
```

---

### Task 5: Simplify the Java emitter

Same as Task 4 but for the Java emitter.

**Files:**
- Modify: `src/plcc/lang/ext/java/emit.py`
- Modify: `src/plcc/lang/ext/java/emit_test.py`

- [ ] **Step 1: Delete the two entry_point tests from `emit_test.py`**

Remove `test_entry_point_defaults_to_dollar_run_when_null` and `test_declared_entry_point_is_used`.

- [ ] **Step 2: Remove `entry_point` key from `_trivial_model()` fixture**

In `_trivial_model()`, inside `semantic_sections`, change:

```python
        {
            "language": "Java",
            "tool": "Java",
            "entry_point": "$run",
            "fragments": [ ... ]
        }
```

to:

```python
        {
            "language": "Java",
            "tool": "Java",
            "fragments": [ ... ]
        }
```

- [ ] **Step 3: Run emit tests to confirm no failures**

```bash
bin/test/units.bash src/plcc/lang/ext/java/emit_test.py -v
```

Expected: all pass.

- [ ] **Step 4: Simplify `emit.py`**

In `src/plcc/lang/ext/java/emit.py`, replace:

```python
    entry_point = (section.get('entry_point') if section else None) or _DEFAULT_ENTRY_POINT
```

with:

```python
    entry_point = _DEFAULT_ENTRY_POINT
```

- [ ] **Step 5: Run emit tests**

```bash
bin/test/units.bash src/plcc/lang/ext/java/emit_test.py -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/lang/ext/java/emit.py \
        src/plcc/lang/ext/java/emit_test.py
git commit -m "refactor(java-emit): use _DEFAULT_ENTRY_POINT directly; remove entry_point tests"
```

---

### Task 6: Remove the bats integration test for null entry_point

**Files:**
- Modify: `tests/bats/integration/python-emit.bats`

- [ ] **Step 1: Delete the test**

In `tests/bats/integration/python-emit.bats`, remove the entire `@test "null entry_point in model generates main.py calling _run"` block (including the closing `}`).

- [ ] **Step 2: Run the integration suite**

```bash
bin/test/integration.bash
```

Expected: all pass.

- [ ] **Step 3: Commit**

```bash
git add tests/bats/integration/python-emit.bats
git commit -m "test(integration): remove obsolete null entry_point bats test"
```

---

### Task 7: Full functional test run

- [ ] **Step 1: Run the full functional suite**

```bash
bin/test/functional.bash
```

Expected: all pass.

- [ ] **Step 2: If any failures, investigate and fix before declaring done**
