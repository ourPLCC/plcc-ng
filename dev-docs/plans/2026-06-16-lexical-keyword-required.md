# Lexical Keyword Required Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `token` or `skip` a required keyword in lexical rules; a bare `NAME 'pattern'` line is now a syntax error.

**Architecture:** Add a `KeywordExpected` error class, change one regex in `Parser._processLine` to require the keyword, then update unit tests that relied on implicit token behavior.

**Tech Stack:** Python, pytest (`bin/test/units.bash`)

---

## File Map

| File | Action |
|---|---|
| `src/plcc/spec/lexical/KeywordExpected.py` | Create — new error class |
| `src/plcc/spec/lexical/__init__.py` | Modify — export `KeywordExpected` |
| `src/plcc/spec/lexical/Parser.py` | Modify — require keyword, emit error |
| `src/plcc/spec/lexical/parse_lexical_test.py` | Modify — repurpose implicit-token tests, fix incidental bare-name tests |

---

### Task 1: `KeywordExpected` error class

**Files:**
- Create: `src/plcc/spec/lexical/KeywordExpected.py`
- Modify: `src/plcc/spec/lexical/__init__.py`

- [ ] **Step 1: Write the failing test**

Add to `src/plcc/spec/lexical/parse_lexical_test.py`, at the top of the import block add `KeywordExpected` (alongside existing imports from `.Parser`):

```python
from .Parser import NameExpected, PatternExpected, PatternDelimiterExpected, UnexpectedContent, KeywordExpected
```

Then add this test near the other error-class tests:

```python
def test_keyword_is_required():
    spec, errors = parseLexicalSpec("NUM '\\d+'")
    assert len(errors) == 1
    assert errors[0].__class__ == KeywordExpected
    assert len(spec.ruleList) == 0
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
bin/test/units.bash src/plcc/spec/lexical/parse_lexical_test.py::test_keyword_is_required -v
```

Expected: `ImportError` or `FAILED` — `KeywordExpected` does not exist yet.

- [ ] **Step 3: Create the error class**

Create `src/plcc/spec/lexical/KeywordExpected.py`:

```python
from .LexicalSpecError import LexicalSpecError


class KeywordExpected(LexicalSpecError):
    def __init__(self, line, index=None, column=None):
        super().__init__(line=line, index=index, column=column,
            message="Expected 'token' or 'skip'."
        )
```

- [ ] **Step 4: Export from `__init__.py`**

In `src/plcc/spec/lexical/__init__.py`, add `KeywordExpected` to the imports (insert alphabetically among the existing lines):

```python
from .DuplicateName import DuplicateName
from .KeywordExpected import KeywordExpected
from .LexicalRule import LexicalRule
from .LexicalSpec import LexicalSpec
from .LexicalSpecError import LexicalSpecError
from .NameExpected import NameExpected
from .parseLexicalSpec import parseLexicalSpec
from .PatternCompilationError import PatternCompilationError
from .PatternDelimiterExpected import PatternDelimiterExpected
from .PatternExpected import PatternExpected
from .SkipRule import SkipRule
from .TokenRule import TokenRule
from .UnexpectedContent import UnexpectedContent
```

- [ ] **Step 5: Run test — still fails (parser not changed yet)**

```bash
bin/test/units.bash src/plcc/spec/lexical/parse_lexical_test.py::test_keyword_is_required -v
```

Expected: `FAILED` — `errors` is empty because the parser still accepts implicit tokens. This confirms the class exists but the enforcement is missing.

- [ ] **Step 6: Commit the error class (tests still red)**

```bash
git add src/plcc/spec/lexical/KeywordExpected.py src/plcc/spec/lexical/__init__.py
git commit -m "feat(lexical): add KeywordExpected error class [skip ci]"
```

---

### Task 2: Enforce keyword in the parser

**Files:**
- Modify: `src/plcc/spec/lexical/Parser.py`

- [ ] **Step 1: Import `KeywordExpected` in `Parser.py`**

At the top of `src/plcc/spec/lexical/Parser.py`, add the import (the existing imports are already there; add one line):

```python
import re

from .check_for_duplicate_names import check_for_duplicate_names
from .TokenRule import TokenRule
from .SkipRule import SkipRule
from .LexicalSpec import LexicalSpec
from .KeywordExpected import KeywordExpected
from .NameExpected import NameExpected
from .PatternCompilationError import PatternCompilationError
from .PatternDelimiterExpected import PatternDelimiterExpected
from .PatternExpected import PatternExpected
from .UnexpectedContent import UnexpectedContent
```

- [ ] **Step 2: Replace the optional-keyword match with a required one**

In `Parser._processLine`, find these three lines (around line 38):

```python
        m = re.compile(r'^\s*(token|skip)?').match(string, index)
        type_ = m[1] if m[1] is not None else 'token'
        index += len(m[0])
```

Replace them with:

```python
        m = re.compile(r'^\s*(token|skip)').match(string, index)
        if m is None:
            wsl = self._getLengthOfLeadingWhitespace(string, index)
            self.errors.append(KeywordExpected(line=line, index=index + wsl))
            return
        type_ = m[1]
        index += len(m[0])
```

- [ ] **Step 3: Run the new test — should pass now**

```bash
bin/test/units.bash src/plcc/spec/lexical/parse_lexical_test.py::test_keyword_is_required -v
```

Expected: `PASSED`

- [ ] **Step 4: Run the full unit suite — expect failures in the old implicit-token tests**

```bash
bin/test/units.bash -v 2>&1 | grep FAILED
```

Expected failures (tests that used bare `NAME 'pattern'` input):
- `test_implicit_token_rule`
- `test_implicit_token_produces_TokenRule`
- `test_choice_of_pattern_delimiter`
- `test_trailing_comment`
- `test_no_leading_space_required`
- `test_names_start_with_uppercase_or_underscore_and_may_contain_numbers`
- `test_two_duplicate_names`
- `test_multiple_of_same_duplication`

No other failures should appear.

- [ ] **Step 5: Commit the parser change (some tests still red)**

```bash
git add src/plcc/spec/lexical/Parser.py
git commit -m "feat(lexical): require token or skip keyword in lexical rules [skip ci]"
```

---

### Task 3: Fix tests that used implicit token syntax

**Files:**
- Modify: `src/plcc/spec/lexical/parse_lexical_test.py`

Apply all of these edits to `src/plcc/spec/lexical/parse_lexical_test.py`.

- [ ] **Step 1: Repurpose `test_implicit_token_rule`**

The test already exists. Replace its body so it tests the new error instead of the old silent behavior:

Old:
```python
def test_implicit_token_rule():
    spec, errors = parseLexicalSpec('''
        SPACE ' '
    ''')
    assert errors == []
    assert len(spec.ruleList) == 1
    assert not spec.ruleList[0].isSkip
```

New (same function name is fine, but rename for clarity):
```python
def test_implicit_token_rule():
    spec, errors = parseLexicalSpec('''
        SPACE ' '
    ''')
    assert len(errors) == 1
    assert errors[0].__class__ == KeywordExpected
    assert len(spec.ruleList) == 0
```

- [ ] **Step 2: Remove `test_implicit_token_produces_TokenRule`**

Delete this entire test — it is redundant with `test_keyword_is_required` and the updated `test_implicit_token_rule`:

```python
def test_implicit_token_produces_TokenRule():
    spec, errors = parseLexicalSpec("SPACE ' '")
    assert errors == []
    assert isinstance(spec.ruleList[0], TokenRule)
```

- [ ] **Step 3: Fix `test_choice_of_pattern_delimiter`**

Add `token` keyword:

```python
def test_choice_of_pattern_delimiter():
    spec, errors = parseLexicalSpec('''
        token SPACE [ [
    ''')
    assert errors == []
    assert len(spec.ruleList) == 1
    assert not spec.ruleList[0].isSkip
```

- [ ] **Step 4: Fix `test_trailing_comment`**

```python
def test_trailing_comment():
    spec, errors = parseLexicalSpec('''
        token SPACE ' ' # comment
    ''')
    assert errors == []
    assert len(spec.ruleList) == 1
    assert not spec.ruleList[0].isSkip
```

- [ ] **Step 5: Fix `test_no_leading_space_required`**

```python
def test_no_leading_space_required():
    spec, errors = parseLexicalSpec('''
token HASH '#'
    ''')
    assert len(errors) == 0
    assert len(spec.ruleList) == 1
```

- [ ] **Step 6: Fix `test_names_start_with_uppercase_or_underscore_and_may_contain_numbers`**

```python
def test_names_start_with_uppercase_or_underscore_and_may_contain_numbers():
    spec, errors = parseLexicalSpec('''
        token SPACE_3 ' '
    ''')
    assert errors == []
    assert len(spec.ruleList) == 1
    assert not spec.ruleList[0].isSkip

    spec, errors = parseLexicalSpec('''
        token _SPACE3_ ' '
    ''')
    assert errors == []
    assert len(spec.ruleList) == 1
    assert not spec.ruleList[0].isSkip
```

- [ ] **Step 7: Fix `test_two_duplicate_names`**

```python
def test_two_duplicate_names():
    spec, errors = parseLexicalSpec('''
        token ONE 'one1'
        token TWO 'two1'
        token NOT 'duplicate'
        token ONE 'one2'
        token TWO 'two2'
    ''')
    assert len(errors) == 2
    assert errors[0].__class__ == DuplicateName
    assert errors[1].__class__ == DuplicateName
    assert len(spec.ruleList) == 5
```

- [ ] **Step 8: Fix `test_multiple_of_same_duplication`**

```python
def test_multiple_of_same_duplication():
    spec, errors = parseLexicalSpec('''
        token ONE 'one1'
        token ONE 'one2'
        token ONE 'one3'
    ''')
    assert len(errors) == 2
    assert errors[0].__class__ == DuplicateName
    assert errors[1].__class__ == DuplicateName
    assert len(spec.ruleList) == 3
```

- [ ] **Step 9: Run the full unit suite — all should pass**

```bash
bin/test/units.bash
```

Expected: previously-failing tests now pass; pre-existing `test_grammar_file_not_found_prints_error` failure in `diagram_test.py` is unrelated to this work and was present before this branch.

- [ ] **Step 10: Commit**

```bash
git add src/plcc/spec/lexical/parse_lexical_test.py
git commit -m "test(lexical): update tests for required token/skip keyword"
```
