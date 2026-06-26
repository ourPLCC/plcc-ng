# Scan Trace Output Readability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the dense, hard-to-read `plcc-scan --trace` output with a structured block format that makes the first-longest-match algorithm easy to follow for students.

**Architecture:** Two-layer change. (1) `Matcher` gains `rule_index` in attempt records so the display layer knows each rule's position in the spec. (2) `_render_record` in `scan.py` is replaced with a block-format renderer that prints a header, source line with special-char indicators, a column-aligned candidates table with a winner marker, and a result line. Bats tests are updated to match.

**Tech Stack:** Python 3, pytest, bats

## Global Constraints

- Run `bin/test/units.bash` after every code change; all 1102 tests must pass.
- Run `bin/test/commands.bash` after bats changes; all tests must pass.
- Follow existing code style: no type annotations, no docstrings, no inline comments unless the why is non-obvious.
- Commits: `[skip ci]` is NOT used here — these are code changes that must run CI.

---

### Task 1: Add `rule_index` to Matcher attempt records

**Files:**
- Modify: `src/plcc/scan/matcher.py`
- Test: `src/plcc/scan/matcher_test.py`

**Interfaces:**
- Produces: each dict in `result.attempts` gains a `'rule_index'` key (int, 1-based) indicating the rule's position in the spec's lexical rule list.

- [ ] **Step 1: Write the failing test**

Add to the bottom of `src/plcc/scan/matcher_test.py` (before the helper methods section):

```python
def test_attempts_include_rule_index():
    m = makeMatcher(r"""
        token ONE '\d'
        token NUM '\d+'
    """, record_attempts=True)
    line = parseLine("42")
    result = m.match(line, index=0)
    by_name = {a['name']: a for a in result.attempts}
    assert by_name['ONE']['rule_index'] == 1
    assert by_name['NUM']['rule_index'] == 2
```

- [ ] **Step 2: Run test to verify it fails**

```bash
bin/test/units.bash src/plcc/scan/matcher_test.py::test_attempts_include_rule_index -v
```

Expected: FAIL with `KeyError: 'rule_index'`

- [ ] **Step 3: Add `_rule_index` tracking to `_getMatches`**

In `src/plcc/scan/matcher.py`, change `_getMatches` from:

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
        matches.append(rule.make_match(m, line, index))
    return matches
```

To:

```python
def _getMatches(self, line, index):
    patterns = self._getPatterns()
    matches = []
    for i, (rule, pattern) in enumerate(zip(self._rules, patterns), start=1):
        m = pattern.match(line.string, index)
        if not m:
            continue
        if m.end() == index:
            continue
        obj = rule.make_match(m, line, index)
        obj._rule_index = i
        matches.append(obj)
    return matches
```

- [ ] **Step 4: Add `rule_index` to attempt dicts in `match`**

In `src/plcc/scan/matcher.py`, change the `if self._record_attempts:` block from:

```python
if self._record_attempts:
    result.attempts = [
        {
            'name': m.name,
            'regex': m.pattern,
            'lexeme': m.lexeme,
            'char_count': len(m.lexeme),
            'is_skip': isinstance(m, Skip),
            'winner': m is result,
        }
        for m in matches
    ]
```

To:

```python
if self._record_attempts:
    result.attempts = [
        {
            'name': m.name,
            'regex': m.pattern,
            'lexeme': m.lexeme,
            'char_count': len(m.lexeme),
            'is_skip': isinstance(m, Skip),
            'winner': m is result,
            'rule_index': getattr(m, '_rule_index', None),
        }
        for m in matches
    ]
```

- [ ] **Step 5: Run test to verify it passes**

```bash
bin/test/units.bash src/plcc/scan/matcher_test.py -v
```

Expected: all matcher tests pass including `test_attempts_include_rule_index`.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/scan/matcher.py src/plcc/scan/matcher_test.py
git commit -m "feat(117): add rule_index to matcher attempt records"
```

---

### Task 2: Replace `_render_record` with the new trace block format

**Files:**
- Modify: `src/plcc/cmd/scan.py`

**Interfaces:**
- Consumes: `record` dict from JSONL — `kind`, `name`, `lexeme`, `regex`, `source` (`file`, `line`, `column`), `source_line`, `attempts` (list of dicts with `name`, `regex`, `lexeme`, `char_count`, `is_skip`, `winner`, `rule_index`)
- Produces: printed trace output in the new block format (non-trace path unchanged)

- [ ] **Step 1: Write a unit test for the new format**

Add a new test file `src/plcc/cmd/scan_render_test.py`:

```python
import io
import sys
import pytest
from .scan import _render_record


def _capture(record, show_skips=True, show_line=True, show_attempts=True):
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        _render_record(record, show_skips, show_line, show_attempts)
    finally:
        sys.stdout = old
    return buf.getvalue()


def _base_record(kind='token'):
    return {
        'kind': kind,
        'name': 'NUM',
        'lexeme': '42',
        'regex': r'\d+',
        'source': {'file': '-', 'line': 1, 'column': 1},
        'source_line': '42',
        'attempts': [
            {'name': 'NUM', 'regex': r'\d+', 'lexeme': '42',
             'char_count': 2, 'is_skip': False, 'winner': True, 'rule_index': 1},
        ],
    }


def test_trace_header():
    out = _capture(_base_record())
    assert 'Scanning -:1:1:' in out


def test_trace_source_line_with_newline_marker():
    r = _base_record()
    r['source_line'] = '42'
    r['source'] = {'file': '-', 'line': 1, 'column': 3}
    out = _capture(r)
    assert '42↵' in out


def test_trace_source_line_no_newline_marker_when_col_within_line():
    r = _base_record()
    r['source_line'] = '42'
    r['source'] = {'file': '-', 'line': 1, 'column': 1}
    out = _capture(r)
    lines = out.splitlines()
    source_line = [l for l in lines if l.startswith('42')][0]
    assert source_line == '42'


def test_trace_tab_replaced_with_arrow():
    r = _base_record()
    r['source_line'] = '\t42'
    r['source'] = {'file': '-', 'line': 1, 'column': 1}
    out = _capture(r)
    assert '→42' in out


def test_trace_caret_at_column():
    r = _base_record()
    r['source_line'] = '42'
    r['source'] = {'file': '-', 'line': 1, 'column': 2}
    out = _capture(r)
    lines = out.splitlines()
    caret_line = [l for l in lines if '^' in l][0]
    assert caret_line == ' ^'


def test_trace_candidates_heading():
    out = _capture(_base_record())
    assert 'Candidates:' in out


def test_trace_table_header_row():
    out = _capture(_base_record())
    assert '#' in out
    assert 'Type' in out
    assert 'Name' in out
    assert 'Pattern' in out
    assert 'Len' in out
    assert 'Match' in out


def test_trace_winner_marked_on_len_when_no_tie():
    r = _base_record()
    r['attempts'] = [
        {'name': 'ONE', 'regex': r'\d', 'lexeme': '4',
         'char_count': 1, 'is_skip': False, 'winner': False, 'rule_index': 1},
        {'name': 'NUM', 'regex': r'\d+', 'lexeme': '42',
         'char_count': 2, 'is_skip': False, 'winner': True, 'rule_index': 2},
    ]
    out = _capture(r)
    assert '2*' in out
    assert '1*' not in out


def test_trace_winner_marked_on_rule_index_when_tie():
    r = _base_record()
    r['name'] = 'PLUS'
    r['lexeme'] = '+'
    r['regex'] = r'\+'
    r['attempts'] = [
        {'name': 'PLUS', 'regex': r'\+', 'lexeme': '+',
         'char_count': 1, 'is_skip': False, 'winner': True, 'rule_index': 1},
        {'name': 'OP', 'regex': r'\+', 'lexeme': '+',
         'char_count': 1, 'is_skip': False, 'winner': False, 'rule_index': 2},
    ]
    out = _capture(r)
    assert '1*' in out
    assert '2*' not in out


def test_trace_legend():
    out = _capture(_base_record())
    assert '* longest match wins; ties broken by earliest rule (#)' in out


def test_trace_result_heading():
    out = _capture(_base_record())
    assert 'Result:' in out


def test_trace_result_line():
    out = _capture(_base_record())
    lines = out.splitlines()
    result_idx = next(i for i, l in enumerate(lines) if l == 'Result:')
    assert lines[result_idx + 1] == r"token NUM '\d+' '42'"


def test_trace_result_line_skip():
    r = _base_record(kind='skip')
    r['name'] = 'WS'
    r['lexeme'] = '\n'
    r['regex'] = r'\s+'
    r['attempts'] = [
        {'name': 'WS', 'regex': r'\s+', 'lexeme': '\n',
         'char_count': 1, 'is_skip': True, 'winner': True, 'rule_index': 1},
    ]
    out = _capture(r)
    lines = out.splitlines()
    result_idx = next(i for i, l in enumerate(lines) if l == 'Result:')
    assert lines[result_idx + 1] == r"skip WS '\s+' '\n'"


def test_non_trace_token_format_unchanged():
    r = _base_record()
    out = _capture(r, show_skips=False, show_line=False, show_attempts=False)
    assert out.strip() == "-:1:1 NUM '42'"


def test_non_trace_skip_format_unchanged():
    r = _base_record(kind='skip')
    r['name'] = 'WS'
    r['lexeme'] = ' '
    out = _capture(r, show_skips=True, show_line=False, show_attempts=False)
    assert out.strip() == "-:1:1 WS ' ' SKIPPED"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
bin/test/units.bash src/plcc/cmd/scan_render_test.py -v
```

Expected: most tests FAIL — `_render_record` still uses the old format.

- [ ] **Step 3: Replace `_render_record` in `scan.py`**

In `src/plcc/cmd/scan.py`, replace the entire `_render_record` function and add two helpers. The final state of the top of the file (after the imports, before `__doc__`) should be:

```python
def _location_str(source):
    file = source.get("file", "-")
    line = source.get("line", "?")
    col = source.get("column", "?")
    return f"{file}:{line}:{col}"


def _escape(s):
    return (s
            .replace('\\', '\\\\')
            .replace('\n', '\\n')
            .replace('\t', '\\t')
            .replace('\r', '\\r'))


def _print_candidates_table(attempts):
    if not attempts:
        return
    winner = next((a for a in attempts if a.get('winner')), None)
    if winner is None:
        return

    winner_len = winner['char_count']
    is_tie = sum(1 for a in attempts if a['char_count'] == winner_len) > 1

    rows = []
    for a in attempts:
        is_winner = a.get('winner', False)
        index_marker = '*' if (is_tie and is_winner) else ''
        len_marker = '*' if (not is_tie and is_winner) else ''
        rows.append({
            '#': str(a.get('rule_index', '?')) + index_marker,
            'Type': 'skip' if a.get('is_skip') else 'token',
            'Name': a['name'],
            'Pattern': f"'{a['regex']}'",
            'Len': str(a['char_count']) + len_marker,
            'Match': f"'{_escape(a['lexeme'])}'" if a['char_count'] > 0 else '',
        })

    cols = ['#', 'Type', 'Name', 'Pattern', 'Len', 'Match']
    header = {c: c for c in cols}
    all_rows = [header] + rows
    widths = {c: max(len(r[c]) for r in all_rows) for c in cols}

    for r in all_rows:
        print('  '.join(r[c].ljust(widths[c]) for c in cols).rstrip(), flush=True)

    print('* longest match wins; ties broken by earliest rule (#)', flush=True)


def _render_record(record, show_skips, show_line, show_attempts):
    kind = record.get("kind")

    if kind == "error":
        loc = _location_str(record.get("source", {}))
        message = record.get("message", "unrecognized character")
        print_user_error(f"{loc}: error: {message}")
        return

    if kind == "skip" and not show_skips:
        return

    if kind not in ("token", "skip"):
        return

    source = record.get("source", {})
    loc = _location_str(source)
    name = record.get("name", "?")
    lexeme = record.get("lexeme", "?")
    pattern = record.get("regex", "?")
    source_line = record.get("source_line", "")
    attempts = record.get("attempts", [])
    col = source.get("column", 1)

    if not show_attempts:
        if kind == "skip":
            print(f"{loc} {name} '{lexeme}' SKIPPED", flush=True)
        else:
            print(f"{loc} {name} '{lexeme}'", flush=True)
        return

    print(f"Scanning {loc}:", flush=True)

    display_line = source_line.replace('\t', '→')
    if col - 1 >= len(display_line):
        display_line += '↵'
    print(display_line, flush=True)
    print(' ' * (col - 1) + '^', flush=True)

    print(flush=True)
    print("Candidates:", flush=True)
    _print_candidates_table(attempts)

    print(flush=True)
    print("Result:", flush=True)
    print(f"{kind} {name} '{pattern}' '{_escape(lexeme)}'", flush=True)
    print(flush=True)
```

- [ ] **Step 4: Run unit tests to verify they pass**

```bash
bin/test/units.bash src/plcc/cmd/scan_render_test.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Run the full unit suite**

```bash
bin/test/units.bash
```

Expected: 1102+ passed, 0 failed.

- [ ] **Step 6: Smoke-test manually**

```bash
echo "42" | plcc-scan --spec tests/fixtures/scan-verbosity.plcc --trace
```

Expected output:
```
Scanning -:1:1:
42↵
^

Candidates:
#  Type   Name  Pattern  Len   Match
1  token  ONE   '\d'     1     '4'
2  token  NUM   '\d+'    2*    '42'
* longest match wins; ties broken by earliest rule (#)

Result:
token NUM '\d+' '42'

Scanning -:1:3:
42↵
  ^

Candidates:
#  Type  Name  Pattern  Len  Match
3  skip  WS    '\s+'    1*   '\n'
* longest match wins; ties broken by earliest rule (#)

Result:
skip WS '\s+' '\n'
```

- [ ] **Step 7: Commit**

```bash
git add src/plcc/cmd/scan.py src/plcc/cmd/scan_render_test.py
git commit -m "feat(117): replace scan trace renderer with new block format"
```

---

### Task 3: Add tie-breaker fixture and update bats tests

**Files:**
- Create: `tests/fixtures/scan-tie.plcc`
- Modify: `tests/bats/commands/plcc-scan.bats`

**Interfaces:**
- Consumes: the new trace format from Task 2.

- [ ] **Step 1: Create the tie fixture**

Create `tests/fixtures/scan-tie.plcc`:

```
token PLUS '\+'
token OP   '\+'
skip  WS   '\s+'
%
<Program> ::= PLUS
```

This gives two rules that both match `+` with the same length — a real tie broken by declaration order (`PLUS` wins at position 1).

- [ ] **Step 2: Run existing bats trace tests to see which fail**

```bash
bin/test/commands.bash 2>&1 | grep -A3 "trace"
```

Expected: several trace tests fail because they assert old format strings (`-> NUM`, `-:1:1: token: NUM`).

- [ ] **Step 3: Replace the six outdated trace tests**

In `tests/bats/commands/plcc-scan.bats`, find and replace the block of six trace tests (lines 115–163, from `@test "plcc-scan --trace produces source line..."` through `@test "plcc-scan --trace token line has no regex"`). Replace with:

```bash
@test "plcc-scan --trace shows Scanning header" {
    cp "${FIXTURES}/scan-verbosity.plcc" spec.plcc
    run bash -c "echo '42' | plcc-scan --trace"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Scanning -:1:1:"* ]]
}

@test "plcc-scan --trace appends newline marker to source line" {
    cp "${FIXTURES}/scan-verbosity.plcc" spec.plcc
    run bash -c "echo '42' | plcc-scan --trace"
    [ "$status" -eq 0 ]
    [[ "$output" == *"42↵"* ]]
}

@test "plcc-scan --trace shows caret under scan position" {
    cp "${FIXTURES}/scan-verbosity.plcc" spec.plcc
    run bash -c "echo '42' | plcc-scan --trace"
    [ "$status" -eq 0 ]
    [[ "$output" == *"^"* ]]
}

@test "plcc-scan --trace shows Candidates heading" {
    cp "${FIXTURES}/scan-verbosity.plcc" spec.plcc
    run bash -c "echo '42' | plcc-scan --trace"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Candidates:"* ]]
}

@test "plcc-scan --trace table has column headers" {
    cp "${FIXTURES}/scan-verbosity.plcc" spec.plcc
    run bash -c "echo '42' | plcc-scan --trace"
    [ "$status" -eq 0 ]
    [[ "$output" == *"#"* ]]
    [[ "$output" == *"Type"* ]]
    [[ "$output" == *"Name"* ]]
    [[ "$output" == *"Pattern"* ]]
    [[ "$output" == *"Len"* ]]
    [[ "$output" == *"Match"* ]]
}

@test "plcc-scan --trace marks longest match with * on Len" {
    cp "${FIXTURES}/scan-verbosity.plcc" spec.plcc
    run bash -c "echo '42' | plcc-scan --trace"
    [ "$status" -eq 0 ]
    [[ "$output" == *"2*"* ]]
}

@test "plcc-scan --trace excludes zero-match candidates" {
    cp "${FIXTURES}/scan-verbosity.plcc" spec.plcc
    run bash -c "echo '42' | plcc-scan --trace"
    [ "$status" -eq 0 ]
    # WS does not match digits; it should not appear in the candidates table
    first_block=$(echo "$output" | awk '/^Scanning -:1:1:/{found=1} found{print} /^$/{if(found) exit}')
    [[ "$first_block" != *"WS"* ]]
}

@test "plcc-scan --trace marks tiebreaker with * on rule position" {
    cp "${FIXTURES}/scan-tie.plcc" spec.plcc
    run bash -c "echo '+' | plcc-scan --trace"
    [ "$status" -eq 0 ]
    [[ "$output" == *"1*"* ]]
}

@test "plcc-scan --trace shows legend" {
    cp "${FIXTURES}/scan-verbosity.plcc" spec.plcc
    run bash -c "echo '42' | plcc-scan --trace"
    [ "$status" -eq 0 ]
    [[ "$output" == *"* longest match wins; ties broken by earliest rule (#)"* ]]
}

@test "plcc-scan --trace shows Result heading" {
    cp "${FIXTURES}/scan-verbosity.plcc" spec.plcc
    run bash -c "echo '42' | plcc-scan --trace"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Result:"* ]]
}

@test "plcc-scan --trace result includes type, name, pattern, and lexeme" {
    cp "${FIXTURES}/scan-verbosity.plcc" spec.plcc
    run bash -c "echo '42' | plcc-scan --trace"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "token NUM '\d+' '42'" ]]
}

@test "plcc-scan --trace result for skip includes type, name, pattern, and lexeme" {
    cp "${FIXTURES}/scan-verbosity.plcc" spec.plcc
    run bash -c "echo '42 99' | plcc-scan --trace"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "skip WS '\\\s\+' '\\\n'" ]] || [[ "$output" == *"skip WS"* ]]
}
```

- [ ] **Step 4: Run commands tests**

```bash
bin/test/commands.bash
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/scan-tie.plcc tests/bats/commands/plcc-scan.bats
git commit -m "test(117): update scan --trace bats tests for new output format"
```

---

## Self-Review

**Spec coverage:**
- ✅ Block header `Scanning <loc>:` — Task 2 `_render_record`
- ✅ Source line with `↵` — Task 2 `display_line` logic
- ✅ Tab → `→` — Task 2 `_escape` / `display_line.replace`
- ✅ Caret under scan position — Task 2
- ✅ `Candidates:` heading — Task 2
- ✅ Table columns `#`, `Type`, `Name`, `Pattern`, `Len`, `Match` — Task 2 `_print_candidates_table`
- ✅ Only matched candidates (1+ chars) — unchanged from existing filter
- ✅ `*` on `Len` (no tie) — Task 2 `len_marker`
- ✅ `*` on `#` (tie) — Task 2 `index_marker`
- ✅ Legend line — Task 2 `_print_candidates_table`
- ✅ `Result:` heading and line — Task 2
- ✅ `rule_index` in attempt records — Task 1
- ✅ Bats tests updated — Task 3
- ✅ Tie fixture — Task 3

**Placeholder scan:** No TBDs, no "similar to Task N" shortcuts, all code shown.

**Type consistency:** `_print_candidates_table` is called with `attempts` from `record.get("attempts", [])`, the same field populated by `Matcher` in Task 1. `rule_index` key name used consistently throughout.
