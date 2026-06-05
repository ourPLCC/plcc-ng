# Remove Lexical Second Pattern Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the optional second ("close") pattern from lexical token/skip rules, eliminating the block-scanning subsystem entirely.

**Architecture:** Work layer by layer — lexical data model first, then parser, then scanner, then tokens CLI, then schema and bats. Each task keeps tests green before committing. `plcc-scan`'s EOF-submit mode is intentionally preserved.

**Tech Stack:** Python, pytest (`bin/test/units.bash`), bats (`bin/test/commands.bash`)

---

### Task 1: Remove `close_pattern` from TokenRule and SkipRule

**Files:**
- Modify: `src/plcc/spec/lexical/TokenRule.py`
- Modify: `src/plcc/spec/lexical/SkipRule.py`
- Modify: `src/plcc/spec/lexical/TokenRule_test.py`
- Modify: `src/plcc/spec/lexical/SkipRule_test.py`

- [ ] **Step 1: Update `TokenRule_test.py`**

Replace the entire file with:

```python
import re

from ...lines import Line
from ...scan.Token import Token
from .TokenRule import TokenRule


def make_line(string='hello', number=1):
    return Line(string=string, number=number)


def make_rule(name='WORD', pattern=r'\w+'):
    return TokenRule(line=make_line(), name=name, pattern=pattern)


def test_make_match_returns_token():
    rule = make_rule(name='NUM', pattern=r'\d+')
    line = make_line(string='42 rest', number=3)
    m = re.match(r'\d+', '42 rest')
    result = rule.make_match(m, line, 0)
    assert isinstance(result, Token)
    assert result.lexeme == '42'
    assert result.name == 'NUM'
    assert result.line is line
    assert result.column == 1
    assert result.pattern == r'\d+'


def test_make_match_column_uses_index_offset():
    rule = make_rule(name='WORD', pattern=r'\w+')
    line = make_line(string='   abc', number=7)
    m = re.match(r'\w+', 'abc')
    result = rule.make_match(m, line, 3)
    assert result.column == 4
```

- [ ] **Step 2: Update `SkipRule_test.py`**

Replace the entire file with:

```python
import re

from ...lines import Line
from ...scan.Skip import Skip
from .SkipRule import SkipRule


def make_line(string='hello', number=1):
    return Line(string=string, number=number)


def make_rule(name='SPACE', pattern=r'\s+'):
    return SkipRule(line=make_line(), name=name, pattern=pattern)


def test_make_match_returns_skip():
    rule = make_rule(name='SPACE', pattern=r'\s+')
    line = make_line(string='   abc', number=5)
    m = re.match(r'\s+', '   abc')
    result = rule.make_match(m, line, 0)
    assert isinstance(result, Skip)
    assert result.lexeme == '   '
    assert result.name == 'SPACE'
    assert result.line is line
    assert result.column == 1
    assert result.pattern == r'\s+'


def test_make_match_column_uses_index_offset():
    rule = make_rule(name='WS', pattern=r'\s+')
    line = make_line(string='x   y', number=2)
    m = re.match(r'\s+', '   y')
    result = rule.make_match(m, line, 1)
    assert result.column == 2
```

- [ ] **Step 3: Run tests — expect failures from removed `close_pattern` field**

```bash
bin/test/units.bash -x 2>&1 | tail -20
```

Expected: failures in `TokenRule_test.py` and `SkipRule_test.py` because `close_pattern` kwarg still exists on the dataclasses. The test file changes compile fine; the failures come from tests that call `make_rule(close_pattern=...)` elsewhere — but those are already removed. The failures should actually be in `parse_lexical_test.py` and other places that still pass `close_pattern`. That's OK — we're building toward green.

Actually: the *updated* tests in this task should *pass* now (they don't use `close_pattern`). Run to confirm just these two files pass:

```bash
bin/test/units.bash src/plcc/spec/lexical/TokenRule_test.py src/plcc/spec/lexical/SkipRule_test.py 2>&1 | tail -5
```

Expected: all pass.

- [ ] **Step 4: Replace `TokenRule.py`**

```python
from __future__ import annotations
import re
from dataclasses import dataclass, field

from ...lines import Line
from ...scan.Token import Token


@dataclass
class TokenRule:
    line: Line | None
    name: str
    pattern: str
    isSkip: bool = field(init=False, default=False, compare=False, repr=False)

    def make_match(self, match: re.Match[str], line, index) -> Token:
        return Token(
            lexeme=match.group(), name=self.name,
            line=line, column=1 + index, pattern=self.pattern,
        )
```

- [ ] **Step 5: Replace `SkipRule.py`**

```python
from __future__ import annotations
import re
from dataclasses import dataclass, field

from ...lines import Line
from ...scan.Skip import Skip


@dataclass
class SkipRule:
    line: Line | None
    name: str
    pattern: str
    isSkip: bool = field(init=False, default=True, compare=False, repr=False)

    def make_match(self, match: re.Match[str], line, index) -> Skip:
        return Skip(
            lexeme=match.group(), name=self.name,
            line=line, column=1 + index, pattern=self.pattern,
        )
```

- [ ] **Step 6: Run the two test files — expect pass**

```bash
bin/test/units.bash src/plcc/spec/lexical/TokenRule_test.py src/plcc/spec/lexical/SkipRule_test.py 2>&1 | tail -5
```

Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add src/plcc/spec/lexical/TokenRule.py src/plcc/spec/lexical/SkipRule.py \
        src/plcc/spec/lexical/TokenRule_test.py src/plcc/spec/lexical/SkipRule_test.py
git commit -m "feat(lexical): remove close_pattern from TokenRule and SkipRule"
```

---

### Task 2: Update LexicalRule protocol

**Files:**
- Modify: `src/plcc/spec/lexical/LexicalRule.py`

- [ ] **Step 1: Replace `LexicalRule.py`**

```python
from __future__ import annotations
from typing import Protocol

from ...lines import Line
from ...scan.Token import Token
from ...scan.Skip import Skip


class LexicalRule(Protocol):
    line: Line | None
    name: str
    pattern: str
    isSkip: bool

    def make_match(self, match, line: Line, index: int) -> Token | Skip: ...
```

- [ ] **Step 2: Run units — expect pass**

```bash
bin/test/units.bash src/plcc/spec/lexical/ 2>&1 | tail -5
```

Expected: all lexical tests pass (some other test files outside this directory may still fail due to `close_pattern` usages not yet removed — that's fine).

- [ ] **Step 3: Commit**

```bash
git add src/plcc/spec/lexical/LexicalRule.py
git commit -m "feat(lexical): remove close_pattern and make_block_result from LexicalRule protocol"
```

---

### Task 3: Remove `_parseOptionalPattern` from Parser

**Files:**
- Modify: `src/plcc/spec/lexical/Parser.py`
- Modify: `src/plcc/spec/lexical/parse_lexical_test.py`

- [ ] **Step 1: Remove block tests from `parse_lexical_test.py`**

Delete these five test functions entirely:
- `test_block_token_rule`
- `test_block_skip_rule`
- `test_block_rule_close_pattern_must_compile`
- `test_block_rule_close_delimiter_required`
- `test_block_rule_no_extra_content_after_close_pattern`

Also update `test_junk_at_the_end_of_a_line` — it currently expects `PatternDelimiterExpected` (because junk was parsed as a malformed second pattern). After this task, junk triggers `UnexpectedContent`. Change it to:

```python
def test_junk_at_the_end_of_a_line():
    spec, errors = parseLexicalSpec('''
        SPACE ' ' junk
    ''')
    assert len(errors) == 1
    assert errors[0].__class__ == UnexpectedContent
    assert len(spec.ruleList) == 0
```

- [ ] **Step 2: Replace `_processLine` in `Parser.py` and remove `_parseOptionalPattern`**

Replace `_processLine` with:

```python
def _processLine(self, line):
    string = line.string
    index = 0

    m = re.compile(r'^\s*(token|skip)?').match(string, index)
    type_ = m[1] if m[1] is not None else 'token'
    index += len(m[0])

    m = re.compile(r'\s*([A-Z_][A-Z0-9_]*)').match(string, index)
    if m is None:
        wsl = self._getLengthOfLeadingWhitespace(string, index)
        self.errors.append(NameExpected(line=line, index=index+wsl))
        return
    name = m[1]
    index += len(m[0])

    regex, index = self._parsePattern(line, string, index)
    if regex is None:
        return

    m = re.compile(r'\s*(?:#.*)?$').match(string, index)
    if not m:
        wsl = self._getLengthOfLeadingWhitespace(string, index)
        self.errors.append(UnexpectedContent(line=line, index=index+wsl))
        return

    RuleClass = SkipRule if type_ == 'skip' else TokenRule
    self.ruleList.append(RuleClass(line=line, name=name, pattern=regex))
```

Delete the `_parseOptionalPattern` method entirely.

- [ ] **Step 3: Run lexical tests — expect pass**

```bash
bin/test/units.bash src/plcc/spec/lexical/ 2>&1 | tail -5
```

Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/spec/lexical/Parser.py src/plcc/spec/lexical/parse_lexical_test.py
git commit -m "feat(lexical): remove optional second pattern from Parser"
```

---

### Task 4: Remove block scanning from Scanner; delete BlockOpened and UnclosedBlockError

**Files:**
- Modify: `src/plcc/scan/scanner.py`
- Modify: `src/plcc/scan/scanner_test.py`
- Modify: `src/plcc/scan/matcher_test.py`
- Modify: `src/plcc/scan/__init__.py`
- Delete: `src/plcc/scan/BlockOpened.py`
- Delete: `src/plcc/scan/BlockOpened_test.py`
- Delete: `src/plcc/scan/UnclosedBlockError.py`
- Delete: `src/plcc/scan/UnclosedBlockError_test.py`

- [ ] **Step 1: Remove block tests from `scanner_test.py`**

Remove these imports from the top of the file:
```python
from .BlockOpened import BlockOpened
from .UnclosedBlockError import UnclosedBlockError
```

Remove these test functions:
- `test_block_token_single_line`
- `test_block_token_multi_line`
- `test_block_token_open_line_column`
- `test_block_skip_emits_Skip`
- `test_block_token_tail_of_close_line_scanned`
- `test_unclosed_block_emits_UnclosedBlockError`
- `test_block_token_multi_line_no_doubled_newlines`
- `test_block_token_multi_line_close_on_own_line`

`TokenRule` and `SkipRule` are imported at lines 5–6 and used only in the block tests — remove those imports too.

- [ ] **Step 2: Remove block tests from `matcher_test.py`**

Remove this import:
```python
from .BlockOpened import BlockOpened
```

Remove these test functions:
- `test_block_token_open_returns_BlockOpened`
- `test_block_skip_open_returns_BlockOpened`

Remove `TokenRule` and `SkipRule` imports (lines 3–4) — they are only used in those two block tests.

- [ ] **Step 3: Replace `scanner.py`**

```python
from .LexError import LexError


class Scanner:
    def __init__(self, matcher):
        self.matcher = matcher

    def scan(self, lines):
        if lines is None:
            return
        for line in lines:
            yield from self._scanLine(line)

    def _scanLine(self, line, start=0):
        index = start
        while index < len(line.string):
            result = self.matcher.match(line, index)
            if isinstance(result, LexError):
                yield result
                index += 1
            else:
                index += len(result.lexeme)
                yield result
```

- [ ] **Step 4: Empty `scan/__init__.py`**

Replace the entire file with an empty file (zero bytes). In practice, write a file with no content:

```bash
> src/plcc/scan/__init__.py
```

Or simply delete both lines from the file so it is empty.

- [ ] **Step 5: Delete the four block files**

```bash
rm src/plcc/scan/BlockOpened.py \
   src/plcc/scan/BlockOpened_test.py \
   src/plcc/scan/UnclosedBlockError.py \
   src/plcc/scan/UnclosedBlockError_test.py
```

- [ ] **Step 6: Run scan tests — expect pass**

```bash
bin/test/units.bash src/plcc/scan/ 2>&1 | tail -5
```

Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add src/plcc/scan/scanner.py src/plcc/scan/scanner_test.py \
        src/plcc/scan/matcher_test.py src/plcc/scan/__init__.py
git rm src/plcc/scan/BlockOpened.py src/plcc/scan/BlockOpened_test.py \
       src/plcc/scan/UnclosedBlockError.py src/plcc/scan/UnclosedBlockError_test.py
git commit -m "feat(scan): remove block scanning; delete BlockOpened and UnclosedBlockError"
```

---

### Task 5: Remove block handling from tokens layer

**Files:**
- Modify: `src/plcc/tokens/spec_loader.py`
- Modify: `src/plcc/tokens/jsonl_formatter.py`
- Modify: `src/plcc/tokens/jsonl_formatter_test.py`
- Modify: `src/plcc/tokens/tokens_cli.py`
- Modify: `src/plcc/tokens/tokens_cli_test.py`

- [ ] **Step 1: Remove block tests from `jsonl_formatter_test.py`**

Remove these imports from the top:
```python
from ..scan.UnclosedBlockError import UnclosedBlockError
from ..spec.lexical.TokenRule import TokenRule
```
(Keep the existing `format_record, format_error_record` import; remove `format_unclosed_block_error_record` from the same import line.)

The import line changes from:
```python
from .jsonl_formatter import format_record, format_error_record, format_unclosed_block_error_record
```
to:
```python
from .jsonl_formatter import format_record, format_error_record
```

Delete these from the test file:
- `_unclosed_block_error` helper function (lines ~138–141)
- `test_format_unclosed_block_error_record_fields`
- `test_format_unclosed_block_error_record_rejects_non_unclosed_block`

- [ ] **Step 2: Remove block test from `tokens_cli_test.py`**

Delete the `_SPEC_WITH_BLOCK` dict and `test_unclosed_block_emits_error_record` function.

- [ ] **Step 3: Replace `spec_loader.py`**

```python
"""Load lexical rules from a spec JSON file for use by plcc-tokens."""

import json

from ..spec.lexical.TokenRule import TokenRule
from ..spec.lexical.SkipRule import SkipRule


def load_lexical_rules(spec_json_path):
    """Return a list of TokenRule/SkipRule objects from a spec JSON file."""
    with open(spec_json_path) as f:
        data = json.load(f)
    rules = []
    for r in data['lexical']['ruleList']:
        RuleClass = SkipRule if r['isSkip'] else TokenRule
        rules.append(RuleClass(
            name=r['name'],
            pattern=r['pattern'],
            line=None,
        ))
    return rules
```

- [ ] **Step 4: Update `jsonl_formatter.py`**

Remove the `UnclosedBlockError` import and the entire `format_unclosed_block_error_record` function. The file after editing:

```python
"""JSONL formatter for plcc-tokens output."""

import json

from ..scan.Token import Token
from ..scan.Skip import Skip
from ..scan.LexError import LexError


def format_record(obj, show_all=False):
    if isinstance(obj, (Token, Skip)):
        kind = 'skip' if isinstance(obj, Skip) else 'token'
        record = {
            'kind': kind,
            'name': obj.name,
            'lexeme': obj.lexeme,
            'source': {
                'file': obj.line.file,
                'line': obj.line.number,
                'column': obj.column,
            },
        }
        if show_all:
            record['regex'] = obj.pattern
            record['source_line'] = obj.line.string.rstrip('\n')
            if obj.attempts:
                record['attempts'] = obj.attempts
        return json.dumps(record)
    raise TypeError(f'Unexpected type: {type(obj)}')


def format_error_record(obj):
    if not isinstance(obj, LexError):
        raise TypeError(f'Unexpected type: {type(obj)}')
    char = obj.line.string[obj.column - 1]
    return json.dumps({
        'kind': 'error',
        'stage': 'plcc-tokens',
        'severity': 'error',
        'source': {
            'file': obj.line.file,
            'line': obj.line.number,
            'column': obj.column,
        },
        'lexeme': char,
        'message': f"unrecognized character {char!r}",
    })
```

- [ ] **Step 5: Update `tokens_cli.py`**

Remove these two imports:
```python
from ..scan.UnclosedBlockError import UnclosedBlockError
from .jsonl_formatter import format_record, format_error_record, format_unclosed_block_error_record
```

Replace with:
```python
from .jsonl_formatter import format_record, format_error_record
```

Remove the `UnclosedBlockError` dispatch block from the `for obj in scanner.scan(lines):` loop:
```python
        if isinstance(obj, UnclosedBlockError):
            print(format_unclosed_block_error_record(obj), flush=True)
            continue
```

- [ ] **Step 6: Run tokens tests — expect pass**

```bash
bin/test/units.bash src/plcc/tokens/ 2>&1 | tail -5
```

Expected: all pass.

- [ ] **Step 7: Run full unit suite — expect pass**

```bash
bin/test/units.bash 2>&1 | tail -5
```

Expected: all pass. This is the first clean full-suite run.

- [ ] **Step 8: Commit**

```bash
git add src/plcc/tokens/spec_loader.py src/plcc/tokens/jsonl_formatter.py \
        src/plcc/tokens/jsonl_formatter_test.py src/plcc/tokens/tokens_cli.py \
        src/plcc/tokens/tokens_cli_test.py
git commit -m "feat(tokens): remove UnclosedBlockError handling and close_pattern from spec_loader"
```

---

### Task 6: Remove `close_pattern` from schema and bats

**Files:**
- Modify: `src/plcc/schemas/spec.schema.json`
- Modify: `tests/bats/commands/plcc-scan.bats`

- [ ] **Step 1: Remove `close_pattern` from `spec.schema.json`**

In the `lexical.ruleList.items.properties` object, delete the `close_pattern` property:

```json
"close_pattern": { "type": ["string", "null"] }
```

The `properties` block for a rule item should end up as:

```json
"properties": {
  "name":    { "type": "string" },
  "pattern": { "type": "string" },
  "isSkip":  { "type": "boolean" }
}
```

- [ ] **Step 2: Remove the block bats test from `plcc-scan.bats`**

Delete this test (line 168–172):

```bash
@test "plcc-scan --trace adds blank line after each block" {
    cp "${FIXTURES}/scan-verbosity.plcc" grammar.plcc
    run bash -c "echo '42 99' | plcc-scan --trace"
    [ "$status" -eq 0 ]
    [[ "$output" =~ $'\n\n' ]]
}
```

- [ ] **Step 3: Run commands tests**

```bash
bin/test/commands.bash 2>&1 | tail -20
```

Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/schemas/spec.schema.json tests/bats/commands/plcc-scan.bats
git commit -m "feat(schema): remove close_pattern; remove block bats test"
```
