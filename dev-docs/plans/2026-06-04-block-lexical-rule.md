# Block Lexical Rule Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add block-mode lexical rules so `token` and `skip` rules accept an optional close-pattern, allowing multi-line content to be captured as a single token.

**Architecture:** Replace the `LexicalRule` dataclass with `TokenRule` and `SkipRule` concrete types (plus a `LexicalRule` Protocol), extend the lexical spec parser to parse an optional second pattern, add `BlockOpened`/`UnclosedBlockError` scan types, update `Matcher` to delegate result construction to the rule, and extend `Scanner` with stateful block mode.

**Tech Stack:** Python 3.14, `dataclasses`, `typing.Protocol`, `re`, `pytest` via `bin/test/units.bash`

---

## File Map

**Create:**
- `src/plcc/spec/lexical/TokenRule.py` — `TokenRule` dataclass with `make_match`/`make_block_result`
- `src/plcc/spec/lexical/SkipRule.py` — `SkipRule` dataclass with `make_match`/`make_block_result`
- `src/plcc/scan/BlockOpened.py` — sentinel returned by `Matcher` when a block open wins
- `src/plcc/scan/UnclosedBlockError.py` — error yielded by `Scanner` on EOF in block mode

**Modify:**
- `src/plcc/spec/lexical/LexicalRule.py` — replace dataclass with `typing.Protocol`
- `src/plcc/spec/lexical/LexicalSpec.py` — update `ruleList` type annotation
- `src/plcc/spec/lexical/__init__.py` — export `TokenRule`, `SkipRule`; keep `LexicalRule` (now Protocol)
- `src/plcc/spec/lexical/Parser.py` — emit `TokenRule`/`SkipRule`; parse optional second pattern
- `src/plcc/spec/lexical/parse_lexical_test.py` — update assertions; add block-rule tests
- `src/plcc/scan/matcher.py` — replace `_makeSkipOrToken` with `rule.make_match`
- `src/plcc/scan/matcher_test.py` — add block-open tests
- `src/plcc/scan/scanner.py` — restructure `scan`; add `_scanLine`/`_scanBlock`
- `src/plcc/scan/scanner_test.py` — add block-mode tests
- `src/plcc/scan/__init__.py` — export `BlockOpened`, `UnclosedBlockError`
- `src/plcc/tokens/spec_loader.py` — create `TokenRule`/`SkipRule` instead of `LexicalRule`
- `src/plcc/schemas/spec.schema.json` — add `close_pattern` field

---

### Task 1: Add `TokenRule` and `SkipRule` (single-pattern, no block yet)

**Files:**
- Create: `src/plcc/spec/lexical/TokenRule.py`
- Create: `src/plcc/spec/lexical/SkipRule.py`
- Modify: `src/plcc/spec/lexical/LexicalRule.py`
- Modify: `src/plcc/spec/lexical/LexicalSpec.py`
- Modify: `src/plcc/spec/lexical/__init__.py`
- Modify: `src/plcc/spec/lexical/Parser.py`
- Modify: `src/plcc/spec/lexical/parse_lexical_test.py`

- [ ] **Step 1: Write failing tests for `TokenRule` and `SkipRule`**

Add to `src/plcc/spec/lexical/parse_lexical_test.py`:

```python
from .TokenRule import TokenRule
from .SkipRule import SkipRule

def test_token_rule_produces_TokenRule():
    spec, errors = parseLexicalSpec("token SPACE ' '")
    assert errors == []
    assert isinstance(spec.ruleList[0], TokenRule)

def test_skip_rule_produces_SkipRule():
    spec, errors = parseLexicalSpec("skip SPACE ' '")
    assert errors == []
    assert isinstance(spec.ruleList[0], SkipRule)

def test_implicit_token_produces_TokenRule():
    spec, errors = parseLexicalSpec("SPACE ' '")
    assert errors == []
    assert isinstance(spec.ruleList[0], TokenRule)
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
bin/test/units.bash src/plcc/spec/lexical/parse_lexical_test.py -v -k "TokenRule or SkipRule or implicit_token_produces"
```

Expected: FAIL — `TokenRule` and `SkipRule` not yet defined.

- [ ] **Step 3: Create `TokenRule`**

`src/plcc/spec/lexical/TokenRule.py`:

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ...lines import Line
from ...scan.Token import Token

if TYPE_CHECKING:
    from ...scan.BlockOpened import BlockOpened


@dataclass
class TokenRule:
    line: Line
    name: str
    pattern: str
    close_pattern: str | None = None
    isSkip: bool = field(init=False, default=False, compare=False, repr=False)

    def make_match(self, match, line, index) -> Token | BlockOpened:
        if self.close_pattern is not None:
            from ...scan.BlockOpened import BlockOpened
            return BlockOpened(
                rule=self, lexeme=match.group(), line=line, column=1 + index,
            )
        return Token(
            lexeme=match.group(), name=self.name,
            line=line, column=1 + index, pattern=self.pattern,
        )

    def make_block_result(self, lexeme: str, line: Line, column: int) -> Token:
        return Token(lexeme=lexeme, name=self.name, line=line, column=column, pattern=self.pattern)
```

- [ ] **Step 4: Create `SkipRule`**

`src/plcc/spec/lexical/SkipRule.py`:

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ...lines import Line
from ...scan.Skip import Skip

if TYPE_CHECKING:
    from ...scan.BlockOpened import BlockOpened


@dataclass
class SkipRule:
    line: Line
    name: str
    pattern: str
    close_pattern: str | None = None
    isSkip: bool = field(init=False, default=True, compare=False, repr=False)

    def make_match(self, match, line, index) -> Skip | BlockOpened:
        if self.close_pattern is not None:
            from ...scan.BlockOpened import BlockOpened
            return BlockOpened(
                rule=self, lexeme=match.group(), line=line, column=1 + index,
            )
        return Skip(
            lexeme=match.group(), name=self.name,
            line=line, column=1 + index, pattern=self.pattern,
        )

    def make_block_result(self, lexeme: str, line: Line, column: int) -> Skip:
        return Skip(lexeme=lexeme, name=self.name, line=line, column=column, pattern=self.pattern)
```

- [ ] **Step 5: Replace `LexicalRule` dataclass with a Protocol**

`src/plcc/spec/lexical/LexicalRule.py` (full replacement):

```python
from __future__ import annotations
from typing import Protocol, TYPE_CHECKING

from ...lines import Line
from ...scan.Token import Token
from ...scan.Skip import Skip

if TYPE_CHECKING:
    from ...scan.BlockOpened import BlockOpened


class LexicalRule(Protocol):
    line: Line
    name: str
    pattern: str
    close_pattern: str | None
    isSkip: bool

    def make_match(self, match, line: Line, index: int) -> Token | Skip | BlockOpened: ...
    def make_block_result(self, lexeme: str, line: Line, column: int) -> Token | Skip: ...
```

- [ ] **Step 6: Update `LexicalSpec` type annotation**

`src/plcc/spec/lexical/LexicalSpec.py`:

```python
from dataclasses import dataclass

from .LexicalRule import LexicalRule


@dataclass
class LexicalSpec:
    ruleList: list[LexicalRule]

    def __len__(self):
        return len(self.ruleList)
```

- [ ] **Step 7: Update `Parser` to emit `TokenRule`/`SkipRule`**

In `src/plcc/spec/lexical/Parser.py`, replace the import and the append line:

```python
# Replace:
from .LexicalRule import LexicalRule
# With:
from .TokenRule import TokenRule
from .SkipRule import SkipRule
```

```python
# Replace (near end of _processLine):
        self.ruleList.append(LexicalRule(line=line, isSkip=(type_=='skip'), name=name, pattern=regex))
# With:
        RuleClass = SkipRule if type_ == 'skip' else TokenRule
        self.ruleList.append(RuleClass(line=line, name=name, pattern=regex))
```

- [ ] **Step 8: Update `__init__.py` exports**

`src/plcc/spec/lexical/__init__.py`:

```python
from .DuplicateName import DuplicateName
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

- [ ] **Step 9: Update `parse_lexical_test.py` — fix existing assertions**

The existing tests assert `spec.ruleList[0].isSkip`. These still work because `TokenRule.isSkip = False` and `SkipRule.isSkip = True`. Verify they are unchanged and still pass.

- [ ] **Step 10: Run all unit tests**

```bash
bin/test/units.bash
```

Expected: all 915+ tests pass.

- [ ] **Step 11: Commit**

```bash
git add src/plcc/spec/lexical/TokenRule.py \
        src/plcc/spec/lexical/SkipRule.py \
        src/plcc/spec/lexical/LexicalRule.py \
        src/plcc/spec/lexical/LexicalSpec.py \
        src/plcc/spec/lexical/__init__.py \
        src/plcc/spec/lexical/Parser.py \
        src/plcc/spec/lexical/parse_lexical_test.py
git commit -m "refactor(lexical): replace LexicalRule dataclass with TokenRule/SkipRule + Protocol"
```

---

### Task 2: Add `BlockOpened` and `UnclosedBlockError`

**Files:**
- Create: `src/plcc/scan/BlockOpened.py`
- Create: `src/plcc/scan/UnclosedBlockError.py`
- Modify: `src/plcc/scan/__init__.py`

- [ ] **Step 1: Create `BlockOpened`**

`src/plcc/scan/BlockOpened.py`:

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ..lines import Line

if TYPE_CHECKING:
    from ..spec.lexical.TokenRule import TokenRule
    from ..spec.lexical.SkipRule import SkipRule


@dataclass
class BlockOpened:
    rule: TokenRule | SkipRule
    lexeme: str
    line: Line
    column: int
    attempts: list = field(default_factory=list, compare=False)

    @property
    def name(self) -> str:
        return self.rule.name

    @property
    def pattern(self) -> str:
        return self.rule.pattern
```

- [ ] **Step 2: Create `UnclosedBlockError`**

`src/plcc/scan/UnclosedBlockError.py`:

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..lines import Line

if TYPE_CHECKING:
    from ..spec.lexical.TokenRule import TokenRule
    from ..spec.lexical.SkipRule import SkipRule


@dataclass
class UnclosedBlockError:
    line: Line
    column: int
    rule: TokenRule | SkipRule
```

- [ ] **Step 3: Export from `src/plcc/scan/__init__.py`**

Check if `src/plcc/scan/__init__.py` exists and has content:

```bash
cat src/plcc/scan/__init__.py
```

If empty or absent, create/append:

```python
from .BlockOpened import BlockOpened
from .UnclosedBlockError import UnclosedBlockError
```

- [ ] **Step 4: Run all unit tests**

```bash
bin/test/units.bash
```

Expected: all tests pass (no behavior change yet).

- [ ] **Step 5: Commit**

```bash
git add src/plcc/scan/BlockOpened.py \
        src/plcc/scan/UnclosedBlockError.py \
        src/plcc/scan/__init__.py
git commit -m "feat(scan): add BlockOpened sentinel and UnclosedBlockError"
```

---

### Task 3: Update `Matcher` to use `rule.make_match`

**Files:**
- Modify: `src/plcc/scan/matcher.py`
- Modify: `src/plcc/scan/matcher_test.py`

- [ ] **Step 1: Write a failing test for block-open result from `Matcher`**

Add to `src/plcc/scan/matcher_test.py`:

```python
from .BlockOpened import BlockOpened
from ..spec.lexical.TokenRule import TokenRule
from ..spec.lexical.SkipRule import SkipRule

def test_block_token_open_returns_BlockOpened():
    rule = TokenRule(line=None, name='BODY', pattern=r'<<<', close_pattern=r'>>>')
    m = matcher.Matcher([rule])
    line = parseLine('<<<content')
    result = m.match(line, index=0)
    assert isinstance(result, BlockOpened)
    assert result.lexeme == '<<<'
    assert result.rule is rule
    assert result.column == 1

def test_block_skip_open_returns_BlockOpened():
    rule = SkipRule(line=None, name='COMMENT', pattern=r'/\*', close_pattern=r'\*/')
    m = matcher.Matcher([rule])
    line = parseLine('/* comment')
    result = m.match(line, index=0)
    assert isinstance(result, BlockOpened)
    assert result.lexeme == '/*'
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
bin/test/units.bash src/plcc/scan/matcher_test.py -v -k "block"
```

Expected: FAIL — `Matcher` still uses `_makeSkipOrToken` which checks `rule.isSkip`.

- [ ] **Step 3: Update `Matcher._makeSkipOrToken` to delegate to `rule.make_match`**

In `src/plcc/scan/matcher.py`, replace the method:

```python
    def _makeSkipOrToken(self, match, rule, line, index):
        return rule.make_match(match, line, index)
```

Delete `_makeSkip` and `_makeToken` — they are no longer called.

- [ ] **Step 4: Run all unit tests**

```bash
bin/test/units.bash
```

Expected: all tests pass including the new block-open tests.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/scan/matcher.py src/plcc/scan/matcher_test.py
git commit -m "refactor(scan): matcher delegates result construction to rule.make_match"
```

---

### Task 4: Update `spec_loader` and JSON schema

**Files:**
- Modify: `src/plcc/tokens/spec_loader.py`
- Modify: `src/plcc/schemas/spec.schema.json`

- [ ] **Step 1: Update `spec_loader.py` to emit `TokenRule`/`SkipRule`**

`src/plcc/tokens/spec_loader.py` (full replacement):

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
            close_pattern=r.get('close_pattern'),
            line=None,
        ))
    return rules
```

- [ ] **Step 2: Update `spec.schema.json` to add `close_pattern`**

In `src/plcc/schemas/spec.schema.json`, find the `ruleList items` object and add `close_pattern`:

```json
"properties": {
  "name":          { "type": "string" },
  "pattern":       { "type": "string" },
  "isSkip":        { "type": "boolean" },
  "close_pattern": { "type": ["string", "null"] }
}
```

(`close_pattern` is not added to `required` — it is optional.)

- [ ] **Step 3: Run all unit tests**

```bash
bin/test/units.bash
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/tokens/spec_loader.py src/plcc/schemas/spec.schema.json
git commit -m "feat(tokens): spec_loader emits TokenRule/SkipRule; schema adds close_pattern"
```

---

### Task 5: Parse optional second pattern in `Parser`

**Files:**
- Modify: `src/plcc/spec/lexical/Parser.py`
- Modify: `src/plcc/spec/lexical/parse_lexical_test.py`

- [ ] **Step 1: Write failing tests for block rules in the lexical parser**

Add to `src/plcc/spec/lexical/parse_lexical_test.py`:

```python
def test_block_token_rule():
    spec, errors = parseLexicalSpec("token BODY '<<<' '>>>'")
    assert errors == []
    assert len(spec.ruleList) == 1
    r = spec.ruleList[0]
    assert isinstance(r, TokenRule)
    assert r.name == 'BODY'
    assert r.pattern == '<<<'
    assert r.close_pattern == '>>>'

def test_block_skip_rule():
    spec, errors = parseLexicalSpec(r"skip COMMENT '/\*' '\*/'")
    assert errors == []
    r = spec.ruleList[0]
    assert isinstance(r, SkipRule)
    assert r.pattern == r'/\*'
    assert r.close_pattern == r'\*/'

def test_block_rule_close_pattern_must_compile():
    spec, errors = parseLexicalSpec("token BODY '<<<' '>>>[' ")
    assert len(errors) == 1
    assert isinstance(errors[0], PatternCompilationError)

def test_block_rule_close_delimiter_required():
    spec, errors = parseLexicalSpec("token BODY '<<<' '>>>")
    assert len(errors) == 1
    assert isinstance(errors[0], PatternDelimiterExpected)

def test_block_rule_no_extra_content_after_close_pattern():
    spec, errors = parseLexicalSpec("token BODY '<<<' '>>>' extra")
    assert len(errors) == 1
    assert isinstance(errors[0], UnexpectedContent)
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
bin/test/units.bash src/plcc/spec/lexical/parse_lexical_test.py -v -k "block"
```

Expected: FAIL — `Parser` does not yet handle a second pattern.

- [ ] **Step 3: Extend `Parser._processLine` to parse optional second pattern**

In `src/plcc/spec/lexical/Parser.py`, replace `_processLine` with:

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

        close_pattern, index = self._parseOptionalPattern(line, string, index)
        if close_pattern is None and index is None:
            return  # error already recorded

        m = re.compile(r'\s*(?:#.*)?$').match(string, index)
        if not m:
            wsl = self._getLengthOfLeadingWhitespace(string, index)
            self.errors.append(UnexpectedContent(line=line, index=index+wsl))
            return

        RuleClass = SkipRule if type_ == 'skip' else TokenRule
        self.ruleList.append(RuleClass(line=line, name=name, pattern=regex, close_pattern=close_pattern))

    def _parsePattern(self, line, string, index):
        """Parse a delimited pattern. Returns (regex, new_index) or (None, None) on error."""
        m = re.compile(r'\s*(\S)').match(string, index)
        if not m:
            wsl = self._getLengthOfLeadingWhitespace(string, index)
            self.errors.append(PatternExpected(line=line, index=index+wsl))
            return None, None
        delimiter = m[1]
        delimiter_escaped = re.escape(delimiter)
        index += len(m[0])

        m = re.compile(f'(?:(?!{delimiter_escaped}).)*').match(string, index)
        regex = m[0]
        index += len(m[0])

        try:
            re.compile(regex)
        except re.error as e:
            self.errors.append(PatternCompilationError(line=line, index=index-len(m[0])+e.pos, error=e))
            return None, None

        m = re.compile(f'{delimiter_escaped}').match(string, index)
        if not m:
            self.errors.append(PatternDelimiterExpected(line=line, index=index, delimiter=delimiter))
            return None, None
        index += len(m[0])
        return regex, index

    def _parseOptionalPattern(self, line, string, index):
        """Parse a second delimited pattern if present. Returns (regex, new_index) or (None, index) if absent, or (None, None) on error."""
        m = re.compile(r'\s*(?:#.*)?$').match(string, index)
        if m:
            return None, index  # no second pattern — that's fine
        return self._parsePattern(line, string, index)
```

The imports (`from .SkipRule import SkipRule`, `from .TokenRule import TokenRule`) and the removal of `from .LexicalRule import LexicalRule` were already done in Task 1. No import changes needed here.

- [ ] **Step 4: Run all unit tests**

```bash
bin/test/units.bash
```

Expected: all tests pass including the new block-rule parser tests.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/spec/lexical/Parser.py \
        src/plcc/spec/lexical/parse_lexical_test.py
git commit -m "feat(lexical): parse optional second pattern for block token/skip rules"
```

---

### Task 6: Extend `Scanner` with block mode

**Files:**
- Modify: `src/plcc/scan/scanner.py`
- Modify: `src/plcc/scan/scanner_test.py`

- [ ] **Step 1: Write failing tests for block scanning**

Add to `src/plcc/scan/scanner_test.py`:

```python
from ..spec.lexical.TokenRule import TokenRule
from ..spec.lexical.SkipRule import SkipRule
from .BlockOpened import BlockOpened
from .UnclosedBlockError import UnclosedBlockError


def test_block_token_single_line():
    """Open and close on the same line emits one Token with content between delimiters."""
    rule = TokenRule(line=None, name='BODY', pattern=r'<<<', close_pattern=r'>>>')
    scanner = Scanner(matcher=makeMatcher([rule]))
    lines = parseLines('<<<hello>>>\n')
    results = list(scanner.scan(lines))
    assert len(results) == 1
    assert isinstance(results[0], Token)
    assert results[0].name == 'BODY'
    assert results[0].lexeme == 'hello'


def test_block_token_multi_line():
    """Content spanning multiple lines is collected into a single Token."""
    rule = TokenRule(line=None, name='BODY', pattern=r'<<<', close_pattern=r'>>>')
    scanner = Scanner(matcher=makeMatcher([rule]))
    lines = parseLines('<<<line1\nline2\n>>>\n')
    results = list(scanner.scan(lines))
    assert len(results) == 1
    assert isinstance(results[0], Token)
    assert results[0].lexeme == 'line1\nline2\n'


def test_block_token_open_line_column():
    """Token carries the opening delimiter's line and column."""
    rule = TokenRule(line=None, name='BODY', pattern=r'<<<', close_pattern=r'>>>')
    other = TokenRule(line=None, name='WORD', pattern=r'\w+')
    scanner = Scanner(matcher=makeMatcher([rule, other]))
    lines = parseLines('abc<<<stuff>>>\n')
    results = list(scanner.scan(lines))
    block_tok = next(r for r in results if r.name == 'BODY')
    assert block_tok.column == 4   # '<<<' starts at column 4


def test_block_skip_emits_Skip():
    """A block skip emits a Skip, not a Token."""
    rule = SkipRule(line=None, name='COMMENT', pattern=r'/\*', close_pattern=r'\*/')
    scanner = Scanner(matcher=makeMatcher([rule]))
    lines = parseLines('/* hello */\n')
    results = list(scanner.scan(lines))
    assert len(results) == 1
    assert isinstance(results[0], Skip)
    assert results[0].name == 'COMMENT'
    assert results[0].lexeme == ' hello '


def test_block_token_tail_of_close_line_scanned():
    """Content after the close delimiter on the same line is scanned normally."""
    rule = TokenRule(line=None, name='BODY', pattern=r'<<<', close_pattern=r'>>>')
    num = TokenRule(line=None, name='NUM', pattern=r'\d+')
    ws = SkipRule(line=None, name='WS', pattern=r'\s+')
    scanner = Scanner(matcher=makeMatcher([rule, num, ws]))
    lines = parseLines('<<<stuff>>> 42\n')
    results = [r for r in scanner.scan(lines) if not isinstance(r, Skip)]
    assert len(results) == 2
    assert results[0].name == 'BODY'
    assert results[1].name == 'NUM'
    assert results[1].lexeme == '42'


def test_unclosed_block_emits_UnclosedBlockError():
    """EOF before the close delimiter yields an UnclosedBlockError."""
    rule = TokenRule(line=None, name='BODY', pattern=r'<<<', close_pattern=r'>>>')
    scanner = Scanner(matcher=makeMatcher([rule]))
    lines = parseLines('<<<no close here\n')
    results = list(scanner.scan(lines))
    assert len(results) == 1
    assert isinstance(results[0], UnclosedBlockError)
    assert results[0].column == 1


def makeMatcher(rules):
    from .matcher import Matcher
    return Matcher(rules)
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
bin/test/units.bash src/plcc/scan/scanner_test.py -v -k "block"
```

Expected: FAIL — `Scanner` does not yet handle `BlockOpened`.

- [ ] **Step 3: Rewrite `Scanner` with block mode**

`src/plcc/scan/scanner.py` (full replacement):

```python
import re

from .BlockOpened import BlockOpened
from .LexError import LexError
from .UnclosedBlockError import UnclosedBlockError


class Scanner:
    def __init__(self, matcher):
        self.matcher = matcher

    def scan(self, lines):
        if lines is None:
            return
        it = iter(lines)
        for line in it:
            yield from self._scanLine(line, it)

    def _scanLine(self, line, it, start=0):
        index = start
        while index < len(line.string):
            result = self.matcher.match(line, index)
            if isinstance(result, BlockOpened):
                open_end = index + len(result.lexeme)
                yield from self._scanBlock(result, line, open_end, it)
                return
            elif isinstance(result, LexError):
                yield result
                index += 1
            else:
                index += len(result.lexeme)
                yield result

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
                buffer += '\n' + next_line.string[:m.start()]
                yield opened.rule.make_block_result(buffer, opened.line, opened.column)
                yield from self._scanLine(next_line, it, start=m.end())
                return
            buffer += '\n' + next_line.string
        # Iterator exhausted without finding close.
        yield UnclosedBlockError(line=opened.line, column=opened.column, rule=opened.rule)
```

- [ ] **Step 4: Run all unit tests**

```bash
bin/test/units.bash
```

Expected: all tests pass including the new block-mode scanner tests.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/scan/scanner.py src/plcc/scan/scanner_test.py
git commit -m "feat(scan): scanner block mode for token/skip rules with close_pattern"
```

---

### Task 7: Update `spec/__init__.py` exports

**Files:**
- Modify: `src/plcc/spec/__init__.py`

- [ ] **Step 1: Add `TokenRule` and `SkipRule` to spec package exports**

Replace the `from .lexical import (...)` block in `src/plcc/spec/__init__.py` with:

```python
from .lexical import (
    DuplicateName,
    LexicalRule,
    LexicalSpec,
    LexicalSpecError,
    NameExpected,
    Parser,
    PatternCompilationError,
    PatternDelimiterExpected,
    PatternExpected,
    SkipRule,
    TokenRule,
)
```

Note: `scan.UnclosedBlockError` is intentionally NOT exported here — `spec/__init__.py` already exports a different `UnclosedBlockError` from `.rough` (for unclosed `%%%` blocks in spec files). Callers needing the scan error import it directly from `plcc.scan`.

- [ ] **Step 2: Run all unit tests**

```bash
bin/test/units.bash
```

Expected: all tests pass.

- [ ] **Step 3: Run functional tests**

```bash
bin/test/functional.bash
```

Expected: all tiers pass.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/spec/__init__.py
git commit -m "feat(spec): export TokenRule and SkipRule from spec package"
```
