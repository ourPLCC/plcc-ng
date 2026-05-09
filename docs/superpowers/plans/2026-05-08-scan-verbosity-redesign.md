# Scan Verbosity Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split `-v` (stderr diagnostics) from new `--show-*` flags (stdout richness), eliminate `plcc-scan`'s stderr capture/reformat machinery, and add `--show-skips`, `--show-line`, `--show-regex`, `--show-attempts`, `--show-all` to `plcc-scan`.

**Architecture:** `plcc-tokens --show-all` emits enriched JSONL records carrying `regex`, `source_line`, and `attempts`; `plcc-scan` passes that flag to `plcc-tokens` whenever any of its own enrichment flags are set, then selectively renders the richer fields. Children inherit stderr rather than having it captured, so `plcc-scan` no longer needs threading or the `parse_child_events`/`reformat_child_events` machinery.

**Tech Stack:** Python 3, dataclasses, docopt-ng, pytest, pyfakefs, bats

---

## File map

| File | Change |
|---|---|
| `src/plcc/scan/Token.py` | Add `pattern` and `attempts` fields |
| `src/plcc/scan/Skip.py` | Same as Token |
| `src/plcc/scan/matcher.py` | Always set `pattern`; optionally build `attempts` |
| `src/plcc/tokens/jsonl_formatter.py` | Handle Skip; emit enriched fields when `show_all=True` |
| `src/plcc/tokens/tokens_cli.py` | Add `--show-all`, `SCANNING_FILE` event, per-file verbose, emit skips |
| `src/plcc/cmd/scan.py` | Remove stderr capture, add enrichment flags, new renderer, TTY hint |
| `src/plcc/schemas/token.schema.json` | Add `SkipRecord` branch; optional enrichment fields |
| `tests/fixtures/scan-verbosity.plcc` | New grammar fixture with two token rules and a skip rule |
| `tests/bats/commands/plcc-tokens.bats` | New: `--show-all` enrichment, `-v` per-file events |
| `tests/bats/commands/plcc-scan.bats` | New: all `--show-*` flags, verbose levels, TTY hint |

**Tests live alongside source code** (`src/plcc/scan/matcher_test.py`, etc.) per repo convention.

---

## Task 1: Enrich Token and Skip data carriers

**Files:**
- Modify: `src/plcc/scan/Token.py`
- Modify: `src/plcc/scan/Skip.py`
- Test: `src/plcc/scan/matcher_test.py` (regression — existing tests must still pass)

`compare=False` on both new fields is critical. Without it, every existing `assert result == Token(lexeme=..., name=..., line=..., column=...)` assertion breaks because the equality check would require callers to supply `pattern` and `attempts`.

- [ ] **Step 1: Open matcher_test.py and confirm the baseline passes**

```bash
bin/test/units.bash src/plcc/scan/matcher_test.py -v
```
Expected: all tests PASS (baseline captured before changes).

- [ ] **Step 2: Edit Token.py**

Replace the entire file:

```python
from dataclasses import dataclass, field
from ..lines import Line

@dataclass
class Token:
    lexeme: str
    name: str
    line: Line
    column: int
    pattern: str = field(default="", compare=False)
    attempts: list = field(default_factory=list, compare=False)
```

- [ ] **Step 3: Edit Skip.py**

Replace the entire file:

```python
from dataclasses import dataclass, field
from ..lines import Line

@dataclass
class Skip:
    lexeme: str
    name: str
    line: Line
    column: int
    pattern: str = field(default="", compare=False)
    attempts: list = field(default_factory=list, compare=False)
```

- [ ] **Step 4: Run the regression suite to confirm `compare=False` works**

```bash
bin/test/units.bash src/plcc/scan/matcher_test.py src/plcc/scan/scanner_test.py -v
```
Expected: all tests PASS — new fields are invisible to equality comparisons.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/scan/Token.py src/plcc/scan/Skip.py
git commit -m "feat(scan): add pattern and attempts fields to Token and Skip"
```

---

## Task 2: Matcher — always populate `pattern`, optionally build `attempts`

**Files:**
- Modify: `src/plcc/scan/matcher.py`
- Test: `src/plcc/scan/matcher_test.py`

The matcher must:
1. Always write `rule.pattern` into the returned object's `.pattern` field.
2. When `record_attempts=True`, capture the full `_getMatches` list *before any filtering* and attach it as `.attempts` on the returned object. Each entry is a dict. The winner is identified by object identity (`m is result`), which works because `_getLongestMatch` and the skip short-circuit both return one of the original objects from `_getMatches`.

- [ ] **Step 1: Write failing tests**

Add to `src/plcc/scan/matcher_test.py`:

```python
def test_pattern_always_set_on_token():
    m = makeMatcher(r"token NUM '\d+'")
    line = parseLine("42")
    result = m.match(line, index=0)
    assert isinstance(result, Token)
    assert result.pattern == r'\d+'

def test_pattern_always_set_on_skip():
    m = makeMatcher(r"skip WS '\s+'")
    line = parseLine(" ")
    result = m.match(line, index=0)
    assert isinstance(result, Skip)
    assert result.pattern == r'\s+'

def test_attempts_empty_by_default():
    m = makeMatcher(r"token NUM '\d+'")
    line = parseLine("42")
    result = m.match(line, index=0)
    assert result.attempts == []

def test_record_attempts_token_win():
    m = makeMatcher(r"""
        token ONE '\d'
        token NUM '\d+'
    """, record_attempts=True)
    line = parseLine("42")
    result = m.match(line, index=0)
    assert isinstance(result, Token)
    assert result.name == "NUM"
    assert len(result.attempts) == 2
    winners = [a for a in result.attempts if a['winner']]
    assert len(winners) == 1
    assert winners[0]['name'] == "NUM"
    losers = [a for a in result.attempts if not a['winner']]
    assert len(losers) == 1
    assert losers[0]['name'] == "ONE"

def test_record_attempts_skip_win_includes_token_candidates():
    m = makeMatcher(r"""
        skip WS '\s+'
        token NUM '\d+'
    """, record_attempts=True)
    line = parseLine(" 42")
    result = m.match(line, index=0)
    assert isinstance(result, Skip)
    # WS wins (first in definition order); NUM also matched the space? No —
    # NUM '\d+' does NOT match a space. Only WS matches here.
    assert len(result.attempts) == 1
    assert result.attempts[0]['winner'] is True
    assert result.attempts[0]['name'] == "WS"
    assert result.attempts[0]['is_skip'] is True

def test_record_attempts_token_wins_over_later_skip():
    # TOKEN appears before SKIP in definition order, so short-circuit does
    # not fire. SKIP should still appear in attempts as non-winner.
    m = makeMatcher(r"""
        token NUM '\d+'
        skip  WS  '\d'
    """, record_attempts=True)
    line = parseLine("42")
    result = m.match(line, index=0)
    assert isinstance(result, Token)
    names = [a['name'] for a in result.attempts]
    assert 'NUM' in names
    assert 'WS' in names
    winner = next(a for a in result.attempts if a['winner'])
    assert winner['name'] == 'NUM'

def test_attempts_entry_fields():
    m = makeMatcher(r"token NUM '\d+'", record_attempts=True)
    line = parseLine("42")
    result = m.match(line, index=0)
    a = result.attempts[0]
    assert a['name'] == 'NUM'
    assert a['regex'] == r'\d+'
    assert a['lexeme'] == '42'
    assert a['char_count'] == 2
    assert a['is_skip'] is False
    assert a['winner'] is True
```

Also update `makeMatcher` helper to accept `record_attempts`:

```python
def makeMatcher(spec, record_attempts=False):
    if isinstance(spec, str):
        spec, errors = parseSpec(spec)
        return matcher.Matcher(spec.lexical.ruleList, record_attempts=record_attempts)
    else:
        return matcher.Matcher(spec, record_attempts=record_attempts)
```

- [ ] **Step 2: Run to confirm failures**

```bash
bin/test/units.bash src/plcc/scan/matcher_test.py -v -k "test_pattern or test_attempts or test_record"
```
Expected: FAIL — `Matcher.__init__` doesn't accept `record_attempts`, `token.pattern` is not set.

- [ ] **Step 3: Implement**

Replace `src/plcc/scan/matcher.py`:

```python
from .Token import Token
from .LexError import LexError
from .Skip import Skip
import re


class Matcher:
    def __init__(self, rules, record_attempts=False):
        self._rules = rules
        self._patterns = None
        self._record_attempts = record_attempts

    def match(self, line, index):
        matches = self._getMatches(line, index)
        if not matches:
            return LexError(line=line, column=index+1)

        all_matches = matches if self._record_attempts else None

        if isinstance(matches[0], Skip):
            result = matches[0]
        else:
            result = self._getLongestMatch(self._removeSkips(matches))

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
                for m in all_matches
            ]

        return result

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

    def _getPatterns(self):
        if not self._patterns:
            self._compilePatterns()
        return self._patterns

    def _compilePatterns(self):
        self._patterns = [re.compile(rule.pattern) for rule in self._rules]

    def _makeSkipOrToken(self, match, rule, line, index):
        if rule.isSkip:
            return self._makeSkip(match, rule, line, index)
        return self._makeToken(match, rule, line, index)

    def _makeSkip(self, match, rule, line, index):
        return Skip(
            lexeme=match.group(), name=rule.name,
            line=line, column=1+index, pattern=rule.pattern,
        )

    def _makeToken(self, match, rule, line, index):
        return Token(
            lexeme=match.group(), name=rule.name,
            line=line, column=1+index, pattern=rule.pattern,
        )

    def _removeSkips(self, matches):
        return [m for m in matches if isinstance(m, Token)]

    def _getLongestMatch(self, matches):
        return max(matches, key=lambda m: len(m.lexeme))
```

- [ ] **Step 4: Run tests**

```bash
bin/test/units.bash src/plcc/scan/matcher_test.py -v
```
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/scan/matcher.py src/plcc/scan/matcher_test.py
git commit -m "feat(scan): populate pattern always; build attempts list when record_attempts=True"
```

---

## Task 3: jsonl_formatter — handle Skip, emit enriched fields

**Files:**
- Modify: `src/plcc/tokens/jsonl_formatter.py`
- Modify: `src/plcc/tokens/jsonl_formatter_test.py`

The formatter gains a `show_all` keyword argument (default `False`). When `True`, it adds `regex` (from `obj.pattern`), `source_line` (from `obj.line.string`), and — if non-empty — an `attempts` array. Skip objects get `kind: "skip"`.

- [ ] **Step 1: Write failing tests**

Add to `src/plcc/tokens/jsonl_formatter_test.py`:

```python
from ..scan.Skip import Skip


def _skip(lexeme=' ', name='WS', line=None, column=3):
    l = line or _line(s='42 99', n=1, f='test.txt')
    s = Skip(lexeme=lexeme, name=name, line=l, column=column)
    s.pattern = r'\s+'
    return s


def _token_enriched():
    t = Token(lexeme='42', name='NUM', line=_line(s='hello 42', n=2, f='src.txt'), column=7)
    t.pattern = r'\d+'
    return t


def test_lean_record_omits_regex_source_line_attempts():
    t = Token(lexeme='42', name='NUM', line=_line(), column=1)
    record = json.loads(format_record(t))
    assert 'regex' not in record
    assert 'source_line' not in record
    assert 'attempts' not in record


def test_show_all_token_includes_regex_and_source_line():
    t = _token_enriched()
    record = json.loads(format_record(t, show_all=True))
    assert record['kind'] == 'token'
    assert record['regex'] == r'\d+'
    assert record['source_line'] == 'hello 42'


def test_show_all_token_omits_attempts_when_empty():
    t = _token_enriched()
    record = json.loads(format_record(t, show_all=True))
    assert 'attempts' not in record


def test_show_all_token_includes_attempts_when_present():
    t = _token_enriched()
    t.attempts = [
        {'name': 'NUM', 'regex': r'\d+', 'lexeme': '42',
         'char_count': 2, 'is_skip': False, 'winner': True},
    ]
    record = json.loads(format_record(t, show_all=True))
    assert len(record['attempts']) == 1
    assert record['attempts'][0]['winner'] is True


def test_skip_record_has_kind_skip():
    s = _skip()
    record = json.loads(format_record(s, show_all=True))
    assert record['kind'] == 'skip'
    assert record['name'] == 'WS'
    assert record['lexeme'] == ' '


def test_skip_record_lean_not_emitted_without_show_all():
    # format_record on a Skip without show_all should still work structurally
    # (tokens_cli decides whether to print it, not the formatter)
    s = _skip()
    record = json.loads(format_record(s))
    assert record['kind'] == 'skip'
    assert 'regex' not in record


def test_exactly_one_winner_in_attempts():
    t = _token_enriched()
    t.attempts = [
        {'name': 'ONE', 'regex': r'\d', 'lexeme': '4',
         'char_count': 1, 'is_skip': False, 'winner': False},
        {'name': 'NUM', 'regex': r'\d+', 'lexeme': '42',
         'char_count': 2, 'is_skip': False, 'winner': True},
    ]
    record = json.loads(format_record(t, show_all=True))
    winners = [a for a in record['attempts'] if a['winner']]
    assert len(winners) == 1
```

- [ ] **Step 2: Run to confirm failures**

```bash
bin/test/units.bash src/plcc/tokens/jsonl_formatter_test.py -v -k "show_all or skip_record or lean or winner"
```
Expected: FAIL — `format_record` doesn't accept `show_all`, doesn't handle `Skip`.

- [ ] **Step 3: Implement**

Replace `src/plcc/tokens/jsonl_formatter.py`:

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
            record['source_line'] = obj.line.string
            if obj.attempts:
                record['attempts'] = obj.attempts
        return json.dumps(record)
    raise TypeError(f'Unexpected type: {type(obj)}')


def format_error_record(obj):
    if not isinstance(obj, LexError):
        raise TypeError(f'Unexpected type: {type(obj)}')
    return json.dumps({
        'kind': 'error',
        'stage': 'plcc-tokens',
        'severity': 'error',
        'pos': {
            'file': obj.line.file,
            'line': obj.line.number,
            'column': obj.column,
        },
        'lexeme': obj.line.string[obj.column - 1],
        'message': 'unrecognized character',
    })
```

- [ ] **Step 4: Run tests**

```bash
bin/test/units.bash src/plcc/tokens/jsonl_formatter_test.py -v
```
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/tokens/jsonl_formatter.py src/plcc/tokens/jsonl_formatter_test.py
git commit -m "feat(tokens): formatter handles Skip and emits enriched fields when show_all=True"
```

---

## Task 4: tokens_cli — `--show-all`, per-file verbose events, emit skips

**Files:**
- Modify: `src/plcc/tokens/tokens_cli.py`
- Modify: `src/plcc/tokens/tokens_cli_test.py`

Changes:
- Add `--show-all` to the docopt usage string.
- Add `SCANNING_FILE` to `Events`.
- Emit `STARTED`, `FINISHED`, and per-file `SCANNING_FILE` verbose events.
- Pass `record_attempts=show_all` to `Matcher`.
- Pass `show_all=show_all` to `format_record`.
- Emit skip records to stdout when `show_all` is True; silently drop them otherwise (existing behaviour).

- [ ] **Step 1: Write failing tests**

Add to `src/plcc/tokens/tokens_cli_test.py`:

```python
_SPEC_WITH_SKIP = {
    "lexical": {"ruleList": [
        {"name": "NUM", "pattern": "\\d+", "isSkip": False,
         "line": {"string": "", "number": 1, "file": None}},
        {"name": "WS", "pattern": "\\s+", "isSkip": True,
         "line": {"string": "", "number": 2, "file": None}},
    ]},
    "syntax": {"rules": []},
    "semantics": []
}


def test_default_omits_regex_and_source_line(capsys, monkeypatch, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC))
    monkeypatch.setattr('sys.stdin', io.StringIO('42\n'))
    run_main(['/spec.json'])
    out, _ = capsys.readouterr()
    record = json.loads(out.strip())
    assert 'regex' not in record
    assert 'source_line' not in record


def test_show_all_includes_regex_and_source_line(capsys, monkeypatch, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC))
    monkeypatch.setattr('sys.stdin', io.StringIO('42\n'))
    run_main(['--show-all', '/spec.json'])
    out, _ = capsys.readouterr()
    record = json.loads(out.strip())
    assert record['regex'] == '\\d+'
    assert record['source_line'] == '42'


def test_default_suppresses_skip_records(capsys, monkeypatch, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC_WITH_SKIP))
    monkeypatch.setattr('sys.stdin', io.StringIO('42 99\n'))
    run_main(['/spec.json'])
    out, _ = capsys.readouterr()
    records = [json.loads(l) for l in out.strip().splitlines() if l]
    kinds = [r['kind'] for r in records]
    assert 'skip' not in kinds


def test_show_all_emits_skip_records(capsys, monkeypatch, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC_WITH_SKIP))
    monkeypatch.setattr('sys.stdin', io.StringIO('42 99\n'))
    run_main(['--show-all', '/spec.json'])
    out, _ = capsys.readouterr()
    records = [json.loads(l) for l in out.strip().splitlines() if l]
    kinds = [r['kind'] for r in records]
    assert 'skip' in kinds


def test_verbose_scanning_file_event(capsys, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC))
    fs.create_file('/src.txt', contents='42\n')
    run_main(['-v', '--verbose-format=text', '/spec.json', '/src.txt'])
    _, err = capsys.readouterr()
    assert 'scanning /src.txt' in err


def test_verbose_started_finished_events(capsys, monkeypatch, fs):
    fs.create_file('/spec.json', contents=json.dumps(_SPEC))
    monkeypatch.setattr('sys.stdin', io.StringIO('42\n'))
    run_main(['-v', '--verbose-format=text', '/spec.json'])
    _, err = capsys.readouterr()
    assert 'started' in err
    assert 'finished' in err
```

- [ ] **Step 2: Run to confirm failures**

```bash
bin/test/units.bash src/plcc/tokens/tokens_cli_test.py -v -k "show_all or skip_records or verbose_scanning or verbose_started"
```
Expected: FAIL.

- [ ] **Step 3: Implement**

Replace `src/plcc/tokens/tokens_cli.py`:

```python
import enum
import sys

from docopt import docopt

from ..lines import Line
from ..scan.matcher import Matcher
from ..scan.scanner import Scanner
from ..scan.Skip import Skip
from ..scan.LexError import LexError
from .spec_loader import load_lexical_rules
from .jsonl_formatter import format_record, format_error_record
from ..verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-tokens
    Tokenize source files given a spec JSON file, output token JSONL.

Usage:
    plcc-tokens [-v ...] [options] SPEC_JSON [SOURCE ...]

Arguments:
    SPEC_JSON   Path to spec JSON file (output of plcc-spec).
    SOURCE      Source files to tokenize. Use '-' for stdin. Defaults to stdin.

Options:
    -h --help               Show this message.
    --show-all              Include regex, source_line, attempts; emit skip records.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"
    SCANNING_FILE = "scanning"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-tokens", Events, args)
    show_all = args['--show-all']
    rules = load_lexical_rules(args['SPEC_JSON'])
    matcher = Matcher(rules, record_attempts=show_all)
    scanner = Scanner(matcher)
    sources = args['SOURCE'] or ['-']
    verbose.emit(Events.STARTED, message="tokenizing")
    lines = _lines_from_sources(sources, verbose)
    for obj in scanner.scan(lines):
        if isinstance(obj, Skip):
            if show_all:
                print(format_record(obj, show_all=True), flush=True)
            continue
        if isinstance(obj, LexError):
            print(format_error_record(obj), flush=True)
            continue
        print(format_record(obj, show_all=show_all), flush=True)
    verbose.emit(Events.FINISHED, message="done")


def _lines_from_sources(sources, verbose):
    for file in sources:
        verbose.emit(Events.SCANNING_FILE, level=1, message=f"scanning {file}")
        if file == '-':
            yield from _lines_from_stream(sys.stdin, '-')
        else:
            with open(file, 'r') as f:
                yield from _lines_from_stream(f, file)


def _lines_from_stream(stream, file):
    for i, raw in enumerate(stream, start=1):
        yield Line(string=raw.rstrip('\n'), number=i, file=file)
```

- [ ] **Step 4: Run tests**

```bash
bin/test/units.bash src/plcc/tokens/tokens_cli_test.py -v
```
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/tokens/tokens_cli.py src/plcc/tokens/tokens_cli_test.py
git commit -m "feat(tokens): add --show-all flag, SCANNING_FILE event, emit skips and enriched records"
```

---

## Task 5: Update token.schema.json

**Files:**
- Modify: `src/plcc/schemas/token.schema.json`

Adds a `SkipRecord` branch to the `oneOf` discriminator (currently a `kind: "skip"` record fails validation — neither existing branch matches). Also adds optional `regex`, `source_line`, and `attempts` to `TokenRecord` and `SkipRecord`, with a full `attempts` item schema.

There are no unit tests for the schema itself; the bats tests in Task 7 will validate records against the schema using `check-jsonschema`.

- [ ] **Step 1: Replace the schema file**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "TokenStreamRecord",
  "description": "One JSONL record from plcc-tokens stdout.",
  "definitions": {
    "SourcePosition": {
      "type": "object",
      "required": ["file", "line", "column"],
      "properties": {
        "file":   { "type": ["string", "null"] },
        "line":   { "type": "integer", "minimum": 1 },
        "column": { "type": "integer", "minimum": 1 }
      }
    },
    "AttemptEntry": {
      "type": "object",
      "required": ["name", "regex", "lexeme", "char_count", "is_skip", "winner"],
      "properties": {
        "name":       { "type": "string" },
        "regex":      { "type": "string" },
        "lexeme":     { "type": "string" },
        "char_count": { "type": "integer", "minimum": 0 },
        "is_skip":    { "type": "boolean" },
        "winner":     { "type": "boolean" }
      }
    },
    "TokenOrSkipProperties": {
      "name":        { "type": "string" },
      "lexeme":      { "type": "string" },
      "source":      { "$ref": "#/definitions/SourcePosition" },
      "regex":       { "type": "string" },
      "source_line": { "type": "string" },
      "attempts": {
        "type": "array",
        "items": { "$ref": "#/definitions/AttemptEntry" }
      }
    }
  },
  "oneOf": [
    {
      "title": "TokenRecord",
      "type": "object",
      "required": ["kind", "name", "lexeme", "source"],
      "properties": {
        "kind": { "type": "string", "const": "token" },
        "name":        { "type": "string" },
        "lexeme":      { "type": "string" },
        "source":      { "$ref": "#/definitions/SourcePosition" },
        "regex":       { "type": "string" },
        "source_line": { "type": "string" },
        "attempts": {
          "type": "array",
          "items": { "$ref": "#/definitions/AttemptEntry" }
        }
      }
    },
    {
      "title": "SkipRecord",
      "type": "object",
      "required": ["kind", "name", "lexeme", "source"],
      "properties": {
        "kind": { "type": "string", "const": "skip" },
        "name":        { "type": "string" },
        "lexeme":      { "type": "string" },
        "source":      { "$ref": "#/definitions/SourcePosition" },
        "regex":       { "type": "string" },
        "source_line": { "type": "string" },
        "attempts": {
          "type": "array",
          "items": { "$ref": "#/definitions/AttemptEntry" }
        }
      }
    },
    {
      "title": "ErrorRecord",
      "type": "object",
      "required": ["kind", "stage", "severity", "pos", "lexeme", "message"],
      "properties": {
        "kind":     { "type": "string", "const": "error" },
        "stage":    { "type": "string" },
        "severity": { "type": "string" },
        "pos":      { "$ref": "#/definitions/SourcePosition" },
        "lexeme":   { "type": "string" },
        "message":  { "type": "string" }
      }
    }
  ]
}
```

- [ ] **Step 2: Verify the existing bats command tests still pass**

```bash
bin/test/commands.bash tests/bats/commands/plcc-tokens.bats
```
Expected: all PASS — the existing schema-validation test still validates lean `TokenRecord` and `ErrorRecord`.

- [ ] **Step 3: Commit**

```bash
git add src/plcc/schemas/token.schema.json
git commit -m "feat(schema): add SkipRecord branch and optional enrichment fields"
```

---

## Task 6: Rewrite scan.py

**Files:**
- Modify: `src/plcc/cmd/scan.py`

This is the biggest change. Removes:
- `import threading`
- `stderr_thread`, `stderr_chunks`, `_drain_stderr`
- both `parse_child_events` / `reformat_child_events` calls
- `child_flags_for_orchestrator` (replaced with `verbose.child_flags()`)
- `stderr=subprocess.PIPE` on both subprocesses

Adds:
- Five `--show-*` flags in the docopt string
- TTY `^D` hint on stdout when stdin is a TTY
- `stderr=None` on both subprocess calls (inherited)
- `--show-all` forwarded to `plcc-tokens` when any enrichment flag is active
- A `_render_record` function with the full rendering logic

No pytest unit tests exist for `scan.py` (it's an orchestrator; the bats tier covers it). Run the existing bats tests at the end to confirm nothing regresses.

- [ ] **Step 1: Replace scan.py**

```python
import enum
import json
import os
import subprocess
import sys
import tempfile

from docopt import docopt, DocoptExit

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS


def _location_str(source):
    file = source.get("file", "-")
    line = source.get("line", "?")
    col = source.get("column", "?")
    return f"{file}:{line}:{col}"


__doc__ = """plcc-scan
    Tokenize source input and print tokens in human-readable format.

Usage:
    plcc-scan [-v ...] [options] GRAMMAR [SOURCE ...]

Arguments:
    GRAMMAR     Path to the PLCC grammar file.
    SOURCE      Source files to tokenize. Reads stdin if none given.

Options:
    -h --help           Show this message.
    --show-skips        Show skip records in output.
    --show-line         Show source line and cursor before each token.
    --show-attempts     Show rule match attempts before each token.
    --show-regex        Show matched regex in each token line.
    --show-all          Enable all --show-* flags.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def _render_record(record, show_skips, show_line, show_regex, show_attempts):
    kind = record.get("kind")

    if kind == "error":
        loc = _location_str(record.get("pos", {}))
        lexeme = record.get("lexeme", "?")
        message = record.get("message", "unrecognized character")
        print(f"{loc}: error: {message} '{lexeme}'", flush=True)
        return

    if kind == "skip" and not show_skips:
        return

    if kind not in ("token", "skip"):
        return

    source = record.get("source", {})
    loc = _location_str(source)
    name = record.get("name", "?")
    lexeme = record.get("lexeme", "?")
    regex = record.get("regex", "")
    source_line = record.get("source_line", "")
    attempts = record.get("attempts", [])
    col = source.get("column", 1)

    if show_line and source_line:
        print(source_line)
        print(" " * (col - 1) + "^")

    if show_attempts:
        for attempt in attempts:
            prefix = "    * " if attempt.get("winner") else "      "
            a_name = attempt.get("name", "?")
            a_regex = attempt.get("regex", "?")
            a_count = attempt.get("char_count", 0)
            a_lexeme = attempt.get("lexeme", "?")
            print(f"{prefix}{a_name} '{a_regex}' {a_count} chars '{a_lexeme}'")

    if show_regex and kind == "skip":
        print(f"{loc} {name} '{regex}' '{lexeme}' SKIPPED", flush=True)
    elif show_regex:
        print(f"{loc} {name} '{regex}' '{lexeme}'", flush=True)
    elif kind == "skip":
        print(f"{loc} {name} '{lexeme}' SKIPPED", flush=True)
    else:
        print(f"{loc} {name} '{lexeme}'", flush=True)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    try:
        args = docopt(__doc__, argv)
    except DocoptExit as e:
        print(str(e), file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-scan --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose = VerboseContext.from_args("plcc-scan", Events, args)
    grammar = args["GRAMMAR"]
    sources = args["SOURCE"]

    show_all = args["--show-all"]
    show_skips = args["--show-skips"] or show_all
    show_line = args["--show-line"] or show_all
    show_regex = args["--show-regex"] or show_all
    show_attempts = args["--show-attempts"] or show_all
    any_enrichment = show_skips or show_line or show_regex or show_attempts

    if sys.stdin.isatty() and (not sources or "-" in sources):
        print("reading from stdin — press ^D to end input", flush=True)

    verbose.emit(Events.STARTED, message=f"scanning with {grammar}")
    child_flags = verbose.child_flags()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        spec_path = f.name
    try:
        with open(spec_path, "w") as spec_out:
            result = subprocess.run(
                ["plcc-spec", grammar] + child_flags,
                stdout=spec_out,
                stderr=None,
            )
        if result.returncode != 0:
            print(f"plcc-scan: plcc-spec failed (exit {result.returncode})", file=sys.stderr)
            sys.exit(result.returncode)

        token_sources = sources if sources else ["-"]
        tokens_flags = child_flags + (["--show-all"] if any_enrichment else [])

        proc = subprocess.Popen(
            ["plcc-tokens", spec_path] + token_sources + tokens_flags,
            stdout=subprocess.PIPE,
            stderr=None,
        )

        for raw in proc.stdout:
            line = raw.decode("utf-8").strip()
            if not line:
                continue
            record = json.loads(line)
            _render_record(record, show_skips, show_line, show_regex, show_attempts)

        proc.wait()

        if proc.returncode != 0:
            print(f"plcc-scan: plcc-tokens failed (exit {proc.returncode})", file=sys.stderr)
            sys.exit(proc.returncode)
    finally:
        os.unlink(spec_path)

    verbose.emit(Events.FINISHED, message="done")
```

- [ ] **Step 2: Run the existing bats suite to confirm no regressions**

```bash
bin/test/commands.bash tests/bats/commands/plcc-scan.bats
```
Expected: all pre-existing tests PASS. In particular `plcc-scan includes file:line:col in token output` still matches `^-:1:1 NUM '42'$` (lean default, no regex).

- [ ] **Step 3: Run units to confirm nothing else broke**

```bash
bin/test/units.bash
```
Expected: all PASS.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/cmd/scan.py
git commit -m "feat(scan): replace stderr capture with pass-through; add --show-* enrichment flags and TTY hint"
```

---

## Task 7: Fixture and bats tests for plcc-tokens

**Files:**
- Create: `tests/fixtures/scan-verbosity.plcc`
- Modify: `tests/bats/commands/plcc-tokens.bats`

The new fixture has two token rules that can both match digits (allowing attempts to show a winner and a loser), plus a skip rule. `ONE '\d'` matches a single digit; `NUM '\d+'` matches one or more. For input `42`, `NUM` wins with the longer match; `ONE` appears as a loser in attempts.

- [ ] **Step 1: Create the fixture**

`tests/fixtures/scan-verbosity.plcc`:
```
token ONE '\d'
token NUM '\d+'
skip  WS  '\s+'
%
<program> ::= NUM
```

- [ ] **Step 2: Add tests to plcc-tokens.bats**

Add to `tests/bats/commands/plcc-tokens.bats` (after the existing tests):

```bash
@test "plcc-tokens default token record omits regex and source_line" {
    result=$(echo '42' | plcc-tokens "${SPEC_JSON}")
    echo "$result" | python3 -c "
import json, sys
r = json.load(sys.stdin)
assert 'regex' not in r, f'regex present in lean record: {r}'
assert 'source_line' not in r, f'source_line present in lean record: {r}'
"
}

@test "plcc-tokens --show-all token record includes regex and source_line" {
    result=$(echo '42' | plcc-tokens --show-all "${SPEC_JSON}")
    echo "$result" | python3 -c "
import json, sys
r = json.load(sys.stdin)
assert 'regex' in r, f'regex missing from enriched record: {r}'
assert 'source_line' in r, f'source_line missing from enriched record: {r}'
assert r['source_line'] == '42', f'wrong source_line: {r}'
"
}

@test "plcc-tokens --show-all emits kind=skip records" {
    VERBOSITY_SPEC_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/scan-verbosity.plcc" > "${VERBOSITY_SPEC_JSON}"
    result=$(echo '42 99' | plcc-tokens --show-all "${VERBOSITY_SPEC_JSON}")
    kinds=$(echo "$result" | python3 -c "
import json, sys
for line in sys.stdin:
    line = line.strip()
    if line:
        r = json.loads(line)
        print(r['kind'])
")
    [[ "$kinds" == *"skip"* ]]
    rm -f "${VERBOSITY_SPEC_JSON}"
}

@test "plcc-tokens --show-all skip records validate against schema" {
    VERBOSITY_SPEC_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/scan-verbosity.plcc" > "${VERBOSITY_SPEC_JSON}"
    echo '42 99' | plcc-tokens --show-all "${VERBOSITY_SPEC_JSON}" | while IFS= read -r line || [ -n "$line" ]; do
        [ -z "$line" ] && continue
        echo "$line" | check-jsonschema --schemafile "${SCHEMA}" -
    done
    rm -f "${VERBOSITY_SPEC_JSON}"
}

@test "plcc-tokens -v emits per-file scanning event on stderr" {
    tmp=$(mktemp)
    echo "42" > "$tmp"
    run --separate-stderr plcc-tokens -v --verbose-format=text "${SPEC_JSON}" "$tmp"
    [[ "$stderr" == *"scanning $tmp"* ]]
    rm -f "$tmp"
}
```

- [ ] **Step 3: Run the bats tests**

```bash
bin/test/commands.bash tests/bats/commands/plcc-tokens.bats
```
Expected: all tests PASS including the new ones.

- [ ] **Step 4: Commit**

```bash
git add tests/fixtures/scan-verbosity.plcc tests/bats/commands/plcc-tokens.bats
git commit -m "test(tokens): add --show-all enrichment and -v per-file event bats tests"
```

---

## Task 8: Bats tests for plcc-scan

**Files:**
- Modify: `tests/bats/commands/plcc-scan.bats`

Adds tests for all five enrichment flags plus verbose regression guards. Uses `scan-verbosity.plcc` for tests that require skip rules or multi-rule attempts.

- [ ] **Step 1: Add tests to plcc-scan.bats**

Add to `tests/bats/commands/plcc-scan.bats` (after the existing tests):

```bash
@test "plcc-scan --show-skips adds SKIPPED lines" {
    VERBOSITY_SPEC_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/scan-verbosity.plcc" > "${VERBOSITY_SPEC_JSON}"
    run bash -c "echo '42 99' | plcc-scan --show-skips '${FIXTURES}/scan-verbosity.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"SKIPPED"* ]]
    rm -f "${VERBOSITY_SPEC_JSON}"
}

@test "plcc-scan --show-skips format is file:line:col NAME 'lexeme' SKIPPED" {
    run bash -c "echo '42 99' | plcc-scan --show-skips '${FIXTURES}/scan-verbosity.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" =~ -:1:[0-9]+\ WS\ \'" "'\'' SKIPPED ]]
}

@test "plcc-scan --show-line shows source line and caret cursor" {
    run bash -c "echo '42' | plcc-scan --show-line '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"42"* ]]
    [[ "$output" == *"^"* ]]
}

@test "plcc-scan --show-line cursor is at correct column" {
    # '42' starts at column 1: cursor should have zero leading spaces
    run bash -c "echo '42' | plcc-scan --show-line '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    # Second line of output should be exactly "^" (no leading spaces)
    second_line=$(echo "$output" | sed -n '2p')
    [ "$second_line" = "^" ]
}

@test "plcc-scan --show-attempts produces indented attempt lines" {
    run bash -c "echo '42' | plcc-scan --show-attempts '${FIXTURES}/scan-verbosity.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"chars"* ]]
}

@test "plcc-scan --show-attempts has exactly one starred winner" {
    run bash -c "echo '42' | plcc-scan --show-attempts '${FIXTURES}/scan-verbosity.plcc'"
    [ "$status" -eq 0 ]
    star_count=$(echo "$output" | grep -c '^\s*\*')
    [ "$star_count" -eq 1 ]
}

@test "plcc-scan --show-regex includes regex in token output" {
    run bash -c "echo '42' | plcc-scan --show-regex '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" =~ ^-:1:1\ NUM\ \'\\\d\+\'\ \'42\'$ ]]
}

@test "plcc-scan --show-all produces source line, cursor, attempts, and token line" {
    run bash -c "echo '42' | plcc-scan --show-all '${FIXTURES}/scan-verbosity.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"42"* ]]
    [[ "$output" == *"^"* ]]
    [[ "$output" == *"chars"* ]]
    [[ "$output" =~ \'\\\d\+ ]]
}

@test "plcc-scan -v emits started and finished events on stderr" {
    run --separate-stderr bash -c "echo '42' | plcc-scan -v '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$stderr" == *"started"* ]]
    [[ "$stderr" == *"finished"* ]]
}

@test "plcc-scan -v hint is absent from stderr" {
    run --separate-stderr bash -c "echo '42' | plcc-scan -v '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$stderr" != *"press ^D"* ]]
}

@test "plcc-scan -vv produces no more stderr output than -v" {
    run --separate-stderr bash -c "echo '42' | plcc-scan -v '${FIXTURES}/trivial.plcc'"
    v1_stderr="$stderr"
    run --separate-stderr bash -c "echo '42' | plcc-scan -vv '${FIXTURES}/trivial.plcc'"
    v2_stderr="$stderr"
    # -vv should not add scan-specific lines beyond -v
    v1_lines=$(echo "$v1_stderr" | wc -l)
    v2_lines=$(echo "$v2_stderr" | wc -l)
    [ "$v2_lines" -le "$v1_lines" ]
}

@test "plcc-scan -vvv produces no more stderr output than -v" {
    run --separate-stderr bash -c "echo '42' | plcc-scan -v '${FIXTURES}/trivial.plcc'"
    v1_stderr="$stderr"
    run --separate-stderr bash -c "echo '42' | plcc-scan -vvv '${FIXTURES}/trivial.plcc'"
    v3_stderr="$stderr"
    v1_lines=$(echo "$v1_stderr" | wc -l)
    v3_lines=$(echo "$v3_stderr" | wc -l)
    [ "$v3_lines" -le "$v1_lines" ]
}

@test "plcc-scan TTY hint absent when stdin is not a TTY" {
    run bash -c "echo '42' | plcc-scan '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" != *"press ^D"* ]]
}
```

- [ ] **Step 2: Run the full bats suite**

```bash
bin/test/commands.bash tests/bats/commands/plcc-scan.bats
```
Expected: all tests PASS.

- [ ] **Step 3: Run the full test suite**

```bash
bin/test/functional.bash
```
Expected: all tiers PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/bats/commands/plcc-scan.bats
git commit -m "test(scan): add --show-* flags, verbose levels, and TTY hint bats tests"
```

---

## Self-review

**Spec coverage check:**

| Spec requirement | Task |
|---|---|
| `Token`/`Skip` gain `pattern` and `attempts` | Task 1 |
| Matcher always sets `pattern`; builds `attempts` from full `_getMatches` | Task 2 |
| Formatter handles Skip; emits `regex`, `source_line`, `attempts` when `show_all` | Task 3 |
| `plcc-tokens --show-all` single enrichment flag; `SCANNING_FILE` event; emits skips | Task 4 |
| Schema: `SkipRecord` branch; optional enrichment fields; attempts item schema | Task 5 |
| `scan.py` pass-through stderr; enrichment flags; TTY hint; new renderer | Task 6 |
| Bats: `plcc-tokens --show-all`, schema validation, `-v` per-file event | Task 7 |
| Bats: all `--show-*`, verbose levels `-v`/`-vv`/`-vvv`, TTY hint absence | Task 8 |
| `compare=False` regression guard | Task 1 + verified in Task 2 |
| Regex field → `obj.pattern` in formatter, emitted as JSON key `"regex"` | Task 3 |
| `source_line` from `obj.line.string` | Task 3 |
| `is_skip` carried in attempts for downstream consumers | Task 2 (set in matcher) + Task 3 (passed through) |
| `char_count == len(lexeme)` in each attempt entry | Task 2 |
| No removals from `verbose.py` | Not touched — verified implicitly by `bin/test/functional.bash` |
