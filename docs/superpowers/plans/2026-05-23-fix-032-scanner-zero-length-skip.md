# Fix 032: Scanner Zero-Length Skip Hang Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the infinite loop in `plcc-scan` that occurs when a `skip` pattern (or any pattern) matches an empty string at the current position.

**Architecture:** One guard added to `Matcher._getMatches` in `matcher.py` — discard any regex match whose end position equals its start position (zero-length match). If all candidates are filtered out, the existing `LexError` path fires naturally. No other production code changes.

**Tech Stack:** Python, pytest, bats

---

## File Map

| File | Action |
| --- | --- |
| `src/plcc/scan/matcher.py` | Modify: add zero-length guard in `_getMatches` |
| `src/plcc/scan/matcher_test.py` | Modify: add two unit tests |
| `src/plcc/scan/scanner_test.py` | Modify: add one integration test |
| `tests/fixtures/zero-length-skip.plcc` | Create: fixture grammar for bats test |
| `tests/bats/commands/plcc-scan.bats` | Modify: add one bats test |

---

## Task 1: Write failing unit tests for zero-length matches in `matcher_test.py`

**Files:**
- Modify: `src/plcc/scan/matcher_test.py`

The two existing helpers `makeMatcher` and `parseLine` at the bottom of the file are all you need.

- [ ] **Step 1: Add two failing tests to `matcher_test.py`**

Append these two tests after the last test in the file (before the `#helper methods` section):

```python
def test_skip_zero_length_match_is_lex_error():
    m = makeMatcher(r"skip WS '\s*'")
    line = parseLine("2")
    result = m.match(line, index=0)
    assert isinstance(result, LexError)


def test_token_zero_length_match_is_lex_error():
    m = makeMatcher(r"token NUM '\d*'")
    line = parseLine("x")
    result = m.match(line, index=0)
    assert isinstance(result, LexError)
```

- [ ] **Step 2: Run tests and confirm they FAIL**

```bash
cd /workspaces/plcc-ng/.worktrees/fix-scanner-empty-match
bin/test/units.bash src/plcc/scan/matcher_test.py::test_skip_zero_length_match_is_lex_error src/plcc/scan/matcher_test.py::test_token_zero_length_match_is_lex_error
```

Expected: both tests FAIL — the current code returns an empty `Skip`/`Token`, not a `LexError`.

---

## Task 2: Implement the fix in `matcher.py`

**Files:**
- Modify: `src/plcc/scan/matcher.py:40-49`

The current `_getMatches` method:

```python
def _getMatches(self, line, index):
    patterns = self._getPatterns()
    matches = []
    for rule, pattern in zip(self._rules, patterns):
        m = pattern.match(line.string, index)
        if not m:
            continue
        sot = self._makeSkipOrToken(m, rule, line, index)
        matches.append(sot)
    return matches
```

- [ ] **Step 1: Add the zero-length guard**

Replace the method body with:

```python
def _getMatches(self, line, index):
    patterns = self._getPatterns()
    matches = []
    for rule, pattern in zip(self._rules, patterns):
        m = pattern.match(line.string, index)
        if not m:
            continue
        if m.end() == index:
            continue
        sot = self._makeSkipOrToken(m, rule, line, index)
        matches.append(sot)
    return matches
```

- [ ] **Step 2: Run the unit tests and confirm they PASS**

```bash
bin/test/units.bash src/plcc/scan/matcher_test.py::test_skip_zero_length_match_is_lex_error src/plcc/scan/matcher_test.py::test_token_zero_length_match_is_lex_error
```

Expected: both tests PASS.

- [ ] **Step 3: Run the full unit suite and confirm nothing is broken**

```bash
bin/test/units.bash
```

Expected: all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/scan/matcher.py src/plcc/scan/matcher_test.py
git commit -m "fix(scan): discard zero-length matches in Matcher to prevent scanner hang

Closes #032"
```

---

## Task 3: Add scanner integration test in `scanner_test.py`

**Files:**
- Modify: `src/plcc/scan/scanner_test.py`

This test uses a real `Matcher` (not a mock) built from a spec string, confirming the scanner produces a `Token` and terminates when the skip pattern can match empty.

- [ ] **Step 1: Add the import at the top of `scanner_test.py`**

The file currently imports:

```python
import pytest

from ..lines import parseLines
from .scanner import Scanner
from .LexError import LexError
from .Skip import Skip
from .Token import Token
```

Add two more imports:

```python
import pytest

from ..lines import parseLines
from ..spec import parseSpec
from . import matcher as matcherModule
from .scanner import Scanner
from .LexError import LexError
from .Skip import Skip
from .Token import Token
```

- [ ] **Step 2: Add the integration test**

Append this test after the last test in the file (before `assertLexErrors`):

```python
def test_scanner_does_not_hang_on_zero_length_skip():
    spec_str = r"skip WS '\s*'" + "\n" + r"token NUM '\d+'"
    spec, _ = parseSpec(spec_str)
    m = matcherModule.Matcher(spec.lexical.ruleList)
    scanner = Scanner(m)
    lines = parseLines("2\n")
    results = list(scanner.scan(lines))
    assert len(results) == 1
    assert isinstance(results[0], Token)
    assert results[0].name == "NUM"
    assert results[0].lexeme == "2"
```

- [ ] **Step 3: Run the test and confirm it PASSES**

```bash
bin/test/units.bash src/plcc/scan/scanner_test.py::test_scanner_does_not_hang_on_zero_length_skip
```

Expected: PASS.

- [ ] **Step 4: Run full unit suite**

```bash
bin/test/units.bash
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/scan/scanner_test.py
git commit -m "test(scan): add scanner integration test for zero-length skip pattern"
```

---

## Task 4: Add fixture and bats commands test

**Files:**
- Create: `tests/fixtures/zero-length-skip.plcc`
- Modify: `tests/bats/commands/plcc-scan.bats`

The fixture is a lexical-only grammar (no `%` section needed — `plcc-scan` only exercises the scanner). The bats test is a regression guard for the exact hang scenario in the issue.

- [ ] **Step 1: Create the fixture file**

Create `tests/fixtures/zero-length-skip.plcc` with this content:

```
skip WHITESPACE '\s*'
token NUM '\d+'
token PERIOD '\.'
```

- [ ] **Step 2: Add the bats test to `plcc-scan.bats`**

Append this test at the end of `tests/bats/commands/plcc-scan.bats`:

```bash
@test "plcc-scan does not hang when skip pattern matches empty string" {
    cp "${FIXTURES}/zero-length-skip.plcc" grammar.plcc
    run bash -c "echo '2' | timeout 5 plcc-scan"
    [ "$status" -eq 0 ]
    [[ "$output" == *"NUM"* ]]
    [[ "$output" == *"2"* ]]
}
```

The `timeout 5` is a safety net — if the fix regresses, the test exits in 5 seconds rather than hanging the suite.

- [ ] **Step 3: Run the commands test suite and confirm PASS**

```bash
bin/test/commands.bash
```

Expected: all tests PASS including the new one.

- [ ] **Step 4: Commit**

```bash
git add tests/fixtures/zero-length-skip.plcc tests/bats/commands/plcc-scan.bats
git commit -m "test(scan): add regression fixture and bats test for issue 032 zero-length skip hang"
```
