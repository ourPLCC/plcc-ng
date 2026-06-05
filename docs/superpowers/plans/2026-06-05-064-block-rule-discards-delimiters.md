# Issue 064 — Block rules discard delimiters: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make block token and skip rule lexemes include the opening and closing delimiter patterns, consistent with how non-block tokens work.

**Architecture:** Three lines change in `Scanner._scanBlock` in `src/plcc/scan/scanner.py`: prepend `opened.lexeme` (the opening match) to the buffer and append `m.group()` (the closing match) when the close delimiter is found. Four existing tests that assert the old (wrong) behavior are updated, and one new test is added.

**Tech Stack:** Python, pytest (via `bin/test/units.bash`)

---

## Files

- Modify: `src/plcc/scan/scanner.py` — fix `_scanBlock` (lines 39, 44, 48)
- Modify: `src/plcc/scan/scanner_test.py` — update 4 tests, add 1 test

---

### Task 1: Update the four existing tests to assert correct (delimiter-inclusive) behavior

These tests currently encode the buggy behavior. Updating them first makes them fail, giving us a red baseline before touching the implementation.

**Files:**
- Modify: `src/plcc/scan/scanner_test.py`

- [ ] **Step 1: Update `test_block_token_single_line`**

In `src/plcc/scan/scanner_test.py`, find `test_block_token_single_line` (around line 110) and change the lexeme assertion:

```python
def test_block_token_single_line():
    """Open and close on the same line emits one Token whose lexeme includes the delimiters."""
    rule = TokenRule(line=None, name='BODY', pattern=r'<<<', close_pattern=r'>>>')
    scanner = Scanner(matcher=makeMatcher([rule]))
    lines = parseLines('<<<hello>>>')
    results = list(scanner.scan(lines))
    assert len(results) == 1
    assert isinstance(results[0], Token)
    assert results[0].name == 'BODY'
    assert results[0].lexeme == '<<<hello>>>'
```

- [ ] **Step 2: Update `test_block_token_multi_line`**

Find `test_block_token_multi_line` and change the lexeme assertion:

```python
def test_block_token_multi_line():
    """Content spanning multiple lines is collected into a single Token including delimiters."""
    rule = TokenRule(line=None, name='BODY', pattern=r'<<<', close_pattern=r'>>>')
    scanner = Scanner(matcher=makeMatcher([rule]))
    lines = parseLines('<<<line1\nline2\n>>>')
    results = list(scanner.scan(lines))
    assert len(results) == 1
    assert isinstance(results[0], Token)
    assert results[0].lexeme == '<<<line1\nline2\n>>>'
```

- [ ] **Step 3: Update `test_block_skip_emits_Skip`**

Find `test_block_skip_emits_Skip` and change the lexeme assertion:

```python
def test_block_skip_emits_Skip():
    """A block skip emits a Skip whose lexeme includes the delimiters."""
    rule = SkipRule(line=None, name='COMMENT', pattern=r'/\*', close_pattern=r'\*/')
    scanner = Scanner(matcher=makeMatcher([rule]))
    lines = parseLines('/* hello */')
    results = list(scanner.scan(lines))
    assert len(results) == 1
    assert isinstance(results[0], Skip)
    assert results[0].name == 'COMMENT'
    assert results[0].lexeme == '/* hello */'
```

- [ ] **Step 4: Update `test_block_token_multi_line_no_doubled_newlines`**

Find `test_block_token_multi_line_no_doubled_newlines` and change the lexeme assertion:

```python
def test_block_token_multi_line_no_doubled_newlines():
    """Regression for issue-061: file-style lines must not produce doubled newlines in the lexeme."""
    from ..lines.parse_from_strings import parse_from_strings
    rule = TokenRule(line=None, name='BODY', pattern=r'<<<', close_pattern=r'>>>')
    ws = SkipRule(line=None, name='WS', pattern=r'\s+')
    scanner = Scanner(matcher=makeMatcher([rule, ws]))
    lines = list(parse_from_strings(['<<<line1\n', 'line2\n', '>>>\n']))
    body_tokens = [r for r in scanner.scan(lines) if isinstance(r, Token) and r.name == 'BODY']
    assert len(body_tokens) == 1
    assert body_tokens[0].lexeme == '<<<line1\nline2\n>>>'
```

- [ ] **Step 5: Add a new test for multi-line block token with delimiters (close on its own line)**

Add this test after `test_block_token_multi_line_no_doubled_newlines`:

```python
def test_block_token_multi_line_close_on_own_line():
    """Multi-line block where the close delimiter is on its own line includes all delimiters."""
    rule = TokenRule(line=None, name='BODY', pattern=r'/\*', close_pattern=r'\*/')
    scanner = Scanner(matcher=makeMatcher([rule]))
    lines = parseLines('/*\nhi\n*/')
    results = list(scanner.scan(lines))
    assert len(results) == 1
    assert isinstance(results[0], Token)
    assert results[0].lexeme == '/*\nhi\n*/'
```

- [ ] **Step 6: Run the tests and confirm they fail**

```bash
bin/test/units.bash src/plcc/scan/scanner_test.py -v --no-header -q
```

Expected: the four updated tests and the new test all FAIL. The other scanner tests should still PASS. A typical failure looks like:

```
AssertionError: assert 'hello' == '<<<hello>>>'
```

---

### Task 2: Fix `_scanBlock` to include the opening and closing delimiters

**Files:**
- Modify: `src/plcc/scan/scanner.py`

- [ ] **Step 1: Apply the fix to `_scanBlock`**

Open `src/plcc/scan/scanner.py`. The full corrected `_scanBlock` method (lines 34–54) is:

```python
def _scanBlock(self, opened, line, start, it):
    close_re = re.compile(opened.rule.close_pattern)
    # Check for close on the opening line (same-line case).
    m = close_re.search(line.string, start)
    if m:
        lexeme = opened.lexeme + line.string[start:m.start()] + m.group()
        yield opened.rule.make_block_result(lexeme, opened.line, opened.column)
        yield from self._scanLine(line, it, start=m.end())
        return
    # Close not on opening line — buffer and consume subsequent lines.
    buffer = opened.lexeme + line.string[start:]
    for next_line in it:
        m = close_re.search(next_line.string)
        if m:
            buffer += next_line.string[:m.start()] + m.group()
            yield opened.rule.make_block_result(buffer, opened.line, opened.column)
            yield from self._scanLine(next_line, it, start=m.end())
            return
        buffer += next_line.string
    # Iterator exhausted without finding close.
    yield UnclosedBlockError(line=opened.line, column=opened.column, rule=opened.rule)
```

- [ ] **Step 2: Run the tests and confirm they all pass**

```bash
bin/test/units.bash src/plcc/scan/scanner_test.py -v --no-header -q
```

Expected: all 16 scanner tests PASS (15 existing + 1 new).

- [ ] **Step 3: Run the full unit suite to check for regressions**

```bash
bin/test/units.bash --no-header -q
```

Expected: all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/scan/scanner.py src/plcc/scan/scanner_test.py
git commit -m "fix(scan): block rules now include opening and closing delimiters in lexeme

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```
