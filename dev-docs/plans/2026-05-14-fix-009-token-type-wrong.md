# Fix 009 — Token Type Wrong Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix single-character uppercase token names (e.g. `A`) being misclassified as non-terminals, causing the model generator to emit `"type": "A"` instead of `"type": "Token"`.

**Architecture:** One-character regex change in `_parseCapturing` fixes the root cause. Two unit tests are added alongside the fix to cover the regression and the alt-name path.

**Tech Stack:** Python, pytest (`bin/test/units.bash`)

---

### Task 1: Regression tests for single-char capturing terminal

**Files:**
- Modify: `src/plcc/spec/syntax/parse_syntactic_spec_test.py` (insert after line 184, after `test_capturing_terminal`)

- [ ] **Step 1: Write two failing tests**

Insert the following two tests immediately after `test_capturing_terminal` (after line 184):

```python
def test_single_char_capturing_terminal():
    single_char = makeLine("<noun> ::= <A>")
    lines = [makeDivider(), single_char]
    expected = [
        makeStandardSyntacticRule(
            single_char,
            makeLhsNonTerminal("noun"),
            [makeCapturingTerminal("A")],
        )
    ]
    assert list(parse_syntactic_spec(lines)) == expected


def test_single_char_capturing_terminal_with_altname():
    single_char_alt = makeLine("<noun> ::= <A>:b")
    lines = [makeDivider(), single_char_alt]
    expected = [
        makeStandardSyntacticRule(
            single_char_alt,
            makeLhsNonTerminal("noun"),
            [makeCapturingTerminal("A", "b")],
        )
    ]
    assert list(parse_syntactic_spec(lines)) == expected
```

- [ ] **Step 2: Run the tests to confirm they fail**

```bash
cd .worktrees/fix-009-token-type
bin/test/units.bash src/plcc/spec/syntax/parse_syntactic_spec_test.py::test_single_char_capturing_terminal src/plcc/spec/syntax/parse_syntactic_spec_test.py::test_single_char_capturing_terminal_with_altname -v
```

Expected: both tests **FAIL** — `AssertionError` because `A` is currently classified as `RhsNonTerminal` instead of `CapturingTerminal`.

---

### Task 2: Fix the regex in `_parseCapturing`

**Files:**
- Modify: `src/plcc/spec/syntax/parse_syntactic_spec.py:92`

- [ ] **Step 1: Apply the fix**

Change line 92 from:

```python
        terminal = re.match(r"[A-Z][A-Z_]+", name)
```

to:

```python
        terminal = re.fullmatch(r"[A-Z_][A-Z0-9_]*", name)
```

- [ ] **Step 2: Run the two new tests to confirm they pass**

```bash
bin/test/units.bash src/plcc/spec/syntax/parse_syntactic_spec_test.py::test_single_char_capturing_terminal src/plcc/spec/syntax/parse_syntactic_spec_test.py::test_single_char_capturing_terminal_with_altname -v
```

Expected: both tests **PASS**.

- [ ] **Step 3: Run the full unit suite to confirm no regressions**

```bash
bin/test/units.bash
```

Expected: all tests **PASS**.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/spec/syntax/parse_syntactic_spec_test.py src/plcc/spec/syntax/parse_syntactic_spec.py
git commit -m "fix(parse-syntactic-spec): single-char token names now classified as terminals"
```
