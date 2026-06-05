# Issue 061 — Line.string Newline Normalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix `Line.string` to always include the trailing `\n` (via `splitlines(keepends=True)` and EOL normalization), so the scanner sees real newline characters for rules like `token NEWLINE '\n'` and so `_scanBlock` stops injecting duplicate newlines.

**Architecture:** Three small production-code changes — `parse_from_string` uses `splitlines(keepends=True)`, `parse_from_strings` normalizes `\r\n`/`\r` to `\n`, and `_scanBlock` removes its manual `'\n'` injection. Existing unit tests are updated to match the new invariant. New regression tests cover the original double-newline bug and `\n`-matching rules.

**Tech Stack:** Python, pytest (`bin/test/units.bash`).

---

## File Map

| File | Change |
|---|---|
| `src/plcc/lines/parse_from_string.py` | `splitlines()` → `splitlines(keepends=True)` |
| `src/plcc/lines/parse_from_strings.py` | normalize `\r\n` / `\r` → `\n` |
| `src/plcc/scan/scanner.py` | remove `'\n' +` injection in `_scanBlock` |
| `src/plcc/lines/parse_from_string_test.py` | update `Line` expectations to include `\n` |
| `src/plcc/scan/scanner_test.py` | trim trailing `\n` from block-test inputs; fix LexError slice indices; fix token count; add regression tests |

---

### Task 1: Update `parseLines` tests to expect `\n` in `Line.string`

These tests will go red immediately; Task 2 makes them green.

**Files:**
- Modify: `src/plcc/lines/parse_from_string_test.py`

- [ ] **Step 1: Update the test expectations**

Replace the five affected tests in `src/plcc/lines/parse_from_string_test.py` with the versions below. (The three tests not shown — `test_None_yields_nothing`, `test_empty_yields_nothing`, `test_one_line_without_eol_yields_single_line`, `test_strings`, `test_TypeError`, `test_file` — are unchanged.)

```python
def test_eol_yields_single_empty_line():
    assert list(parseLines('\n')) == [Line('\n', 1, None)]


def test_one_line_with_eol_yields_single_line():
    assert list(parseLines('one\n')) == [Line('one\n', 1, None)]


def test_multiple_lines():
    assert list(parseLines('one\ntwo')) == [Line('one\n', 1, None), Line('two', 2, None)]


def test_set_start_of_numbering():
    assert list(parseLines('one\ntwo', startLineNumber=3)) == [Line('one\n', 3, None), Line('two', 4, None)]


def test_set_file():
    assert list(parseLines('one\ntwo', file='/f')) == [Line('one\n', 1, '/f'), Line('two', 2, '/f')]
```

- [ ] **Step 2: Confirm the tests fail**

```
bin/test/units.bash src/plcc/lines/parse_from_string_test.py
```

Expected: 5 failures — `AssertionError` because `Line('one', ...)` ≠ `Line('one\n', ...)`.

---

### Task 2: Fix `parse_from_string` to preserve `\n`

**Files:**
- Modify: `src/plcc/lines/parse_from_string.py`

- [ ] **Step 1: Change `splitlines()` to `splitlines(keepends=True)`**

Replace the full content of `src/plcc/lines/parse_from_string.py`:

```python
from .parse_from_strings import parse_from_strings


def parse_from_string(string, file=None, startLineNumber=1):
    return parse_from_strings(string.splitlines(keepends=True), file=file, startLineNumber=startLineNumber)
```

- [ ] **Step 2: Confirm `parseLines` tests pass**

```
bin/test/units.bash src/plcc/lines/parse_from_string_test.py
```

Expected: all pass.

- [ ] **Step 3: Commit**

```bash
git add src/plcc/lines/parse_from_string.py src/plcc/lines/parse_from_string_test.py
git commit -m "fix(lines): preserve trailing newline in parse_from_string via splitlines(keepends=True)"
```

---

### Task 3: Update scanner tests broken by `keepends=True`

Now that `Line.string` includes `\n`, several scanner tests break because the scanner tries to match `\n` after close delimiters (no matching rule → `LexError`), or because LexError result-slices counted characters without `\n`. Fix each.

**Files:**
- Modify: `src/plcc/scan/scanner_test.py`

- [ ] **Step 1: Confirm the scanner tests currently fail**

```
bin/test/units.bash src/plcc/scan/scanner_test.py
```

Expected failures:
- `test_block_token_single_line` — `AssertionError: assert 2 == 1` (extra LexError for `\n`)
- `test_block_token_multi_line` — `AssertionError: assert 2 == 1`
- `test_block_token_open_line_column` — `AssertionError: assert 3 == 2`
- `test_block_skip_emits_Skip` — `AssertionError: assert 2 == 1`
- `test_LexError_at_start_goes_through_whole_line_one_character_at_a_time` — wrong lineNumber on slice
- `test_can_match_multiple_tokens` — `AssertionError: assert 7 == 6`

- [ ] **Step 2: Fix the four block-token tests — trim trailing `\n` from inputs**

The existing block-token tests aren't testing newline handling; trim the `\n` so the scanner has nothing left to match after the close delimiter.

In `src/plcc/scan/scanner_test.py`, make these targeted changes:

```python
# test_block_token_single_line
lines = parseLines('<<<hello>>>')          # was '<<<hello>>>\n'

# test_block_token_multi_line
lines = parseLines('<<<line1\nline2\n>>>')  # was '<<<line1\nline2\n>>>\n'

# test_block_token_open_line_column
lines = parseLines('abc<<<stuff>>>')       # was 'abc<<<stuff>>>\n'

# test_block_skip_emits_Skip
lines = parseLines('/* hello */')          # was '/* hello */\n'
```

- [ ] **Step 3: Fix LexError slice indices**

In `test_LexError_at_start_goes_through_whole_line_one_character_at_a_time`, `Line.string` is now 11 characters (`'0123456789\n'`), not 10. The slice boundary moves from 10 to 11:

```python
# was:
assertLexErrors(results[0:10], lineNumber=1, startColumn=1)
assertLexErrors(results[10:], lineNumber=2, startColumn=1)

# becomes:
assertLexErrors(results[0:11], lineNumber=1, startColumn=1)
assertLexErrors(results[11:], lineNumber=2, startColumn=1)
```

- [ ] **Step 4: Fix the token count in `test_can_match_multiple_tokens`**

`Line.string` for `'12345123451234512345\n'` is now 21 characters, so the 5-character matcher picks up the trailing `\n` as an extra 1-character token. Update the assertion:

```python
assert len(results) == 7   # was 6
```

- [ ] **Step 5: Confirm all scanner tests pass**

```
bin/test/units.bash src/plcc/scan/scanner_test.py
```

Expected: all pass.

- [ ] **Step 6: Run the full unit suite to confirm nothing else regressed**

```
bin/test/units.bash
```

Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add src/plcc/scan/scanner_test.py
git commit -m "test(scan): update scanner tests for Line.string keepends invariant"
```

---

### Task 4: Regression test + fix `_scanBlock` double-newline bug

Write a test that exercises the original production bug (file-style lines where `Line.string` already ends with `\n`), confirm it fails with the current `_scanBlock`, then remove the injection.

**Files:**
- Modify: `src/plcc/scan/scanner_test.py`
- Modify: `src/plcc/scan/scanner.py`

- [ ] **Step 1: Add the regression test**

Add this test to `src/plcc/scan/scanner_test.py` (after the existing block tests, before `makeMatcher`):

```python
def test_block_token_multi_line_no_doubled_newlines():
    """Regression for issue-061: file-style lines (string includes \\n) must not produce doubled newlines in the lexeme."""
    from ..lines.parse_from_strings import parse_from_strings
    rule = TokenRule(line=None, name='BODY', pattern=r'<<<', close_pattern=r'>>>')
    ws = SkipRule(line=None, name='WS', pattern=r'\s+')
    scanner = Scanner(matcher=makeMatcher([rule, ws]))
    lines = list(parse_from_strings(['<<<line1\n', 'line2\n', '>>>\n']))
    body_tokens = [r for r in scanner.scan(lines) if isinstance(r, Token) and r.name == 'BODY']
    assert len(body_tokens) == 1
    assert body_tokens[0].lexeme == 'line1\nline2\n'
```

- [ ] **Step 2: Confirm the test fails**

```
bin/test/units.bash src/plcc/scan/scanner_test.py::test_block_token_multi_line_no_doubled_newlines
```

Expected: FAIL — `AssertionError` because the actual lexeme is `'line1\n\nline2\n\n'` (doubled newlines from the old injection).

- [ ] **Step 3: Remove `'\n'` injection from `_scanBlock`**

In `src/plcc/scan/scanner.py`, update `_scanBlock` — remove the `'\n' +` from both buffer-accumulation lines:

```python
def _scanBlock(self, opened, line, start, it):
    close_re = re.compile(opened.rule.close_pattern)
    # Check for close on the opening line (same-line case).
    m = close_re.search(line.string, start)
    if m:
        lexeme = line.string[start:m.start()]
        yield opened.rule.make_block_result(lexeme, opened.line, opened.column)
        yield from self._scanLine(line, it, start=m.end())
        return
    # Close not on opening line — buffer and consume subsequent lines.
    buffer = line.string[start:]
    for next_line in it:
        m = close_re.search(next_line.string)
        if m:
            buffer += next_line.string[:m.start()]
            yield opened.rule.make_block_result(buffer, opened.line, opened.column)
            yield from self._scanLine(next_line, it, start=m.end())
            return
        buffer += next_line.string
    # Iterator exhausted without finding close.
    yield UnclosedBlockError(line=opened.line, column=opened.column, rule=opened.rule)
```

- [ ] **Step 4: Confirm all scanner tests pass**

```
bin/test/units.bash src/plcc/scan/scanner_test.py
```

Expected: all pass.

- [ ] **Step 5: Run full unit suite**

```
bin/test/units.bash
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/scan/scanner.py src/plcc/scan/scanner_test.py
git commit -m "fix(scan): remove manual newline injection from _scanBlock; newlines come from Line.string"
```

---

### Task 5: Normalize `\r\n` / `\r` in `parse_from_strings`

**Files:**
- Modify: `src/plcc/lines/parse_from_strings.py`
- Modify: `src/plcc/lines/parse_from_string_test.py`

- [ ] **Step 1: Add normalization tests**

Add these tests to `src/plcc/lines/parse_from_string_test.py`:

```python
def test_crlf_line_ending_normalized_to_lf():
    assert list(parseLines('one\r\ntwo\r\n')) == [Line('one\n', 1, None), Line('two\n', 2, None)]


def test_bare_cr_line_ending_normalized_to_lf():
    assert list(parseLines('one\rtwo\r')) == [Line('one\n', 1, None), Line('two\n', 2, None)]
```

- [ ] **Step 2: Confirm the tests fail**

```
bin/test/units.bash src/plcc/lines/parse_from_string_test.py::test_crlf_line_ending_normalized_to_lf src/plcc/lines/parse_from_string_test.py::test_bare_cr_line_ending_normalized_to_lf
```

Expected: FAIL — `Line('one\r\n', ...)` or `Line('one\r', ...)` ≠ `Line('one\n', ...)`.

- [ ] **Step 3: Add normalization to `parse_from_strings`**

Replace the full content of `src/plcc/lines/parse_from_strings.py`:

```python
from .Line import Line


def parse_from_strings(strings, file=None, startLineNumber=1):
    for i, string in enumerate(strings, start=startLineNumber):
        if string.endswith('\r\n'):
            string = string[:-2] + '\n'
        elif string.endswith('\r'):
            string = string[:-1] + '\n'
        yield Line(string=string, file=file, number=i)
```

- [ ] **Step 4: Confirm the new tests pass**

```
bin/test/units.bash src/plcc/lines/parse_from_string_test.py
```

Expected: all pass.

- [ ] **Step 5: Run full unit suite**

```
bin/test/units.bash
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/lines/parse_from_strings.py src/plcc/lines/parse_from_string_test.py
git commit -m "fix(lines): normalize CRLF and bare CR line endings to LF in parse_from_strings"
```

---

### Task 6: Test that `token NEWLINE '\n'` matches line endings

Verify that the new invariant enables real newline-matching rules. No production code changes are needed — this task confirms the design is complete and documents the behavior.

**Files:**
- Modify: `src/plcc/scan/scanner_test.py`

- [ ] **Step 1: Add the newline-matching test**

Add this test to `src/plcc/scan/scanner_test.py` (after the regression test from Task 4, before `makeMatcher`):

```python
def test_newline_token_rule_matches_line_endings():
    """token NEWLINE '\\n' can match each line ending when Line.string includes the trailing newline."""
    from ..lines.parse_from_strings import parse_from_strings
    nl_rule = TokenRule(line=None, name='NL', pattern=r'\n')
    word_rule = TokenRule(line=None, name='WORD', pattern=r'\w+')
    scanner = Scanner(matcher=makeMatcher([nl_rule, word_rule]))
    lines = list(parse_from_strings(['hello\n', 'world\n']))
    results = list(scanner.scan(lines))
    token_names = [r.name for r in results if isinstance(r, Token)]
    assert token_names == ['WORD', 'NL', 'WORD', 'NL']
```

- [ ] **Step 2: Confirm the test passes without any code change**

```
bin/test/units.bash src/plcc/scan/scanner_test.py::test_newline_token_rule_matches_line_endings
```

Expected: PASS. (If it fails, debug before committing.)

- [ ] **Step 3: Run full unit suite**

```
bin/test/units.bash
```

Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/scan/scanner_test.py
git commit -m "test(scan): verify token NEWLINE rule matches line endings via Line.string invariant"
```
