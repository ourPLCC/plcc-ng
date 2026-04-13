# Phase 1: Walking Skeleton Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a connected walking skeleton — every Level 0 command processes the trivial grammar, all JSON contracts are defined and tested, and development infrastructure (BATS tests, `bin/` scripts, CI) is fully established.

**Architecture:** Rename `plccng` → `plcc` in-place preserving git history, then refactor existing `spec` and `scan` modules into standalone `plcc-spec` and `plcc-tokens` commands. Add `plcc-tree`, `plcc-model`, `plcc-plantuml-emit`, `plcc-lang-{emit,build,list}`, and `plcc-make`. Three-layer tests: pytest unit tests alongside modules, BATS command/integration/e2e tests, and CI via GitHub Actions.

**Tech Stack:** Python 3.10+, pdm, pytest, pyfakefs, docopt-ng, BATS, check-jsonschema, GitHub Actions

---

## Part 1 — Baseline

### Task 1: Verify existing tests pass

**Files:**
- Run only: `bin/test/units.bash`

**Step 1: Run the existing test suite**

```bash
bin/test/units.bash
```

Expected: all tests pass (green). If any fail, fix them before continuing. Do not proceed until the bar is green.

**Step 2: Note the test count**

Record the number of passing tests for reference (it should not decrease after the rename).

---

### Task 2: Create `multi-lang` branch and rename the package

**Files:**
- Move: `src/plccng/` → `src/plcc/`

**Step 1: Create the branch**

```bash
git checkout -b multi-lang
```

**Step 2: Rename the package directory**

```bash
git mv src/plccng src/plcc
```

**Step 3: Verify the move**

```bash
ls src/plcc/
```

Expected: same files that were in `src/plccng/`.

---

### Task 3: Update imports and `pyproject.toml`

**Files:**
- Modify: `src/plcc/**/*.py` (all files with `plccng` imports)
- Modify: `pyproject.toml`

**Step 1: Replace all `plccng` import references**

```bash
grep -rl 'plccng' src/plcc/ | xargs sed -i '' 's/plccng/plcc/g'
```

On Linux, omit the `''` after `-i`.

**Step 2: Update `pyproject.toml`**

Change `name = "plccng"` to `name = "plcc"` and update the entry point:

```toml
[project]
name = "plcc"

[project.scripts]
plcc = "plcc.plcc_cli:main"
```

Also rename `src/plcc/plccng_cli.py` → `src/plcc/plcc_cli.py` and `src/plcc/plccng_cli_test.py` → `src/plcc/plcc_cli_test.py`:

```bash
git mv src/plcc/plccng_cli.py src/plcc/plcc_cli.py
git mv src/plcc/plccng_cli_test.py src/plcc/plcc_cli_test.py
```

**Step 3: Update `plcc_cli.py` docstring and internal references**

In `src/plcc/plcc_cli.py`, update the module docstring:

```python
"""plcc
    The Programming Languages Compiler Compiler - Next Generation

Usage:
    plcc COMMAND [OPTION ...] [ARGUMENT ...]
    plcc (-h|--help)

Commands:
    spec    Print JSON representation of PLCC spec.
    scan    Print JSON tokens given PLCC spec and code.

Options:
    -h|--help   Display this message
"""
```

Update all `plccng` references inside the file to `plcc`.

**Step 4: Update `plcc_cli_test.py`**

Replace all `plccng` references with `plcc` and update `from .plccng_cli import ...` to `from .plcc_cli import ...`.

**Step 5: Update `pytest.ini` if it references `plccng`**

```bash
grep 'plccng' pytest.ini && sed -i '' 's/plccng/plcc/g' pytest.ini
```

---

### Task 4: Migrate all tests and verify green bar

**Files:**
- Modify: `src/plcc/**/*_test.py` (any remaining `plccng` references)

**Step 1: Find any remaining `plccng` references in tests**

```bash
grep -r 'plccng' src/plcc/
```

Expected: zero results. Fix any that appear.

**Step 2: Reinstall the renamed package**

```bash
pdm install
```

**Step 3: Run the full test suite**

```bash
bin/test/units.bash
```

Expected: same number of tests pass as in Task 1. Do not proceed until the bar is green.

**Step 4: Commit**

```bash
git add -A
git commit -m "refactor: rename plccng package to plcc"
```

---

## Part 2 — Fixtures and Schemas

### Task 5: Create the trivial grammar and test fixtures

**Files:**
- Create: `tests/fixtures/trivial.plcc`
- Create: `tests/fixtures/trivial_input.txt`

**Step 1: Create the fixtures directory**

```bash
mkdir -p tests/fixtures
```

**Step 2: Create `tests/fixtures/trivial.plcc`**

```
%% lexical rules
NUM '\d+'

%% syntactic rules
<program> ::= <NUM>

%% semantic rules
% diagram PlantUML
```

**Step 3: Create `tests/fixtures/trivial_input.txt`**

```
42
```

**Step 4: Commit**

```bash
git add tests/fixtures/
git commit -m "test(fixtures): add trivial grammar and input"
```

---

### Task 6: Define JSON schemas for all Level 0 contracts

**Files:**
- Create: `src/plcc/schemas/spec.schema.json`
- Create: `src/plcc/schemas/token.schema.json`
- Create: `src/plcc/schemas/tree.schema.json`
- Create: `src/plcc/schemas/model.schema.json`

**Step 1: Create the schemas directory**

```bash
mkdir -p src/plcc/schemas
```

**Step 2: Create `spec.schema.json`**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Spec",
  "description": "Output of plcc-spec: a parsed PLCC grammar.",
  "type": "object",
  "required": ["lexical", "syntax", "semantics"],
  "properties": {
    "lexical": {
      "type": "object",
      "required": ["ruleList"],
      "properties": {
        "ruleList": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["name", "pattern", "isSkip"],
            "properties": {
              "name":    { "type": "string" },
              "pattern": { "type": "string" },
              "isSkip":  { "type": "boolean" }
            }
          }
        }
      }
    },
    "syntax": {
      "type": "object",
      "required": ["rules"],
      "properties": {
        "rules": { "type": "array" }
      }
    },
    "semantics": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["language", "tool"],
        "properties": {
          "language": { "type": "string" },
          "tool":     { "type": "string" }
        }
      }
    }
  }
}
```

**Step 3: Create `token.schema.json`**

This schema validates one line of `plcc-tokens` JSONL output. Each line is either a token record or an error record.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "TokenRecord",
  "description": "One JSONL record from plcc-tokens.",
  "type": "object",
  "required": ["kind"],
  "oneOf": [
    {
      "description": "A successfully scanned token.",
      "required": ["kind", "name", "lexeme", "source"],
      "properties": {
        "kind":   { "type": "string", "const": "token" },
        "name":   { "type": "string" },
        "lexeme": { "type": "string" },
        "source": {
          "type": "object",
          "required": ["file", "line", "column"],
          "properties": {
            "file":   { "type": ["string", "null"] },
            "line":   { "type": "integer", "minimum": 1 },
            "column": { "type": "integer", "minimum": 1 }
          }
        }
      }
    },
    {
      "description": "A lex error (in-band).",
      "required": ["kind", "stage", "source"],
      "properties": {
        "kind":  { "type": "string", "const": "error" },
        "stage": { "type": "string" },
        "source": {
          "type": "object",
          "required": ["file", "line", "column"],
          "properties": {
            "file":   { "type": ["string", "null"] },
            "line":   { "type": "integer", "minimum": 1 },
            "column": { "type": "integer", "minimum": 1 }
          }
        }
      }
    }
  ]
}
```

**Step 4: Create `tree.schema.json`**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "TreeRecord",
  "description": "One JSONL record from plcc-tree: one complete parse tree.",
  "type": "object",
  "required": ["kind", "rule"],
  "properties": {
    "kind":     { "type": "string", "const": "tree" },
    "rule":     { "type": "string" },
    "children": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["kind"],
        "properties": {
          "kind": { "type": "string", "enum": ["token", "tree", "error"] }
        }
      }
    }
  }
}
```

**Step 5: Create `model.schema.json`**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Model",
  "description": "Output of plcc-model: language-neutral OO code model.",
  "type": "object",
  "required": ["start", "classes", "semantic_sections"],
  "properties": {
    "start": { "type": "string" },
    "classes": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "fields"],
        "properties": {
          "name":    { "type": "string" },
          "extends": { "type": ["string", "null"] },
          "fields": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["name", "type"],
              "properties": {
                "name": { "type": "string" },
                "type": { "type": "string" }
              }
            }
          },
          "methods": { "type": "array" }
        }
      }
    },
    "semantic_sections": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["tool", "language"],
        "properties": {
          "tool":     { "type": "string" },
          "language": { "type": "string" }
        }
      }
    }
  }
}
```

**Step 6: Add `check-jsonschema` to dev dependencies**

In `pyproject.toml`, add to `[dependency-groups].dev`:

```toml
[dependency-groups]
dev = [
    "pytest>=8.2.0",
    "pyfakefs>=5.4.1",
    "pytest-cov>=5.0.0",
    "pytest-watch>=4.2.0",
    "check-jsonschema>=0.29.0",
]
```

Run `pdm install` to pick up the new dependency.

**Step 7: Commit**

```bash
git add src/plcc/schemas/ pyproject.toml pdm.lock
git commit -m "feat(schemas): add minimum viable JSON schemas for all Level 0 contracts"
```

---

## Part 3 — Level 0 Commands

### Task 7: `plcc-spec` — standalone entry point

`plcc-spec` wraps the existing `spec_cli` logic but exposes it as a standalone command (no `spec` subcommand prefix).

**Files:**
- Create: `src/plcc/spec/plcc_spec_cli.py`
- Create: `src/plcc/spec/plcc_spec_cli_test.py`
- Modify: `pyproject.toml`

**Step 1: Write the failing test**

Create `src/plcc/spec/plcc_spec_cli_test.py`:

```python
import json
import pytest
import docopt

from .plcc_spec_cli import main as run_main


def test_no_args_prints_usage():
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_help(capsys):
    with pytest.raises(SystemExit):
        run_main(['--help'])
    out, err = capsys.readouterr()
    assert 'Usage' in out


def test_outputs_spec_json(capsys, fs):
    fs.create_file('/trivial.plcc', contents="""
%% lexical rules
NUM '\\d+'

%% syntactic rules
<program> ::= <NUM>

%% semantic rules
% diagram PlantUML
""")
    run_main(['/trivial.plcc'])
    out, err = capsys.readouterr()
    data = json.loads(out)
    assert 'lexical' in data
    assert 'syntax' in data
    assert 'semantics' in data


def test_lexical_rules_present(capsys, fs):
    fs.create_file('/trivial.plcc', contents="NUM '\\d+'\n")
    run_main(['/trivial.plcc'])
    out, err = capsys.readouterr()
    data = json.loads(out)
    names = [r['name'] for r in data['lexical']['ruleList']]
    assert 'NUM' in names


def test_exits_nonzero_on_spec_error(capsys, fs):
    fs.create_file('/bad.plcc', contents="num 'bad'\n")  # lowercase = invalid
    with pytest.raises(SystemExit) as exc:
        run_main(['/bad.plcc'])
    assert exc.value.code != 0
```

**Step 2: Run tests to confirm they fail**

```bash
pdm run pytest src/plcc/spec/plcc_spec_cli_test.py -v
```

Expected: FAIL — `plcc_spec_cli` module does not exist.

**Step 3: Create `src/plcc/spec/plcc_spec_cli.py`**

```python
"""plcc-spec
    Parse, validate, and print a PLCC grammar file as JSON.

Usage:
    plcc-spec [options] FILE

Arguments:
    FILE    PLCC grammar file. Use - to read from stdin.

Options:
    --no-json       Do not print JSON to stdout.
    -h --help       Show this message.
"""

import json
import sys
from dataclasses import asdict

from docopt import docopt

from . import parseSpec


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    spec, errors = _load(args['FILE'])
    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        sys.exit(1)
    if not args['--no-json']:
        print(json.dumps(asdict(spec), indent=2))


def _load(path):
    if path == '-':
        return parseSpec(sys.stdin.read(), '-')
    with open(path) as f:
        return parseSpec(f.read(), path)
```

**Step 4: Run tests to confirm they pass**

```bash
pdm run pytest src/plcc/spec/plcc_spec_cli_test.py -v
```

Expected: all 5 pass.

**Step 5: Wire the entry point in `pyproject.toml`**

Add to `[project.scripts]`:

```toml
plcc-spec = "plcc.spec.plcc_spec_cli:main"
```

**Step 6: Reinstall and smoke-test**

```bash
pdm install
plcc-spec tests/fixtures/trivial.plcc | python -m json.tool > /dev/null && echo "OK"
```

Expected: "OK" — valid JSON output.

**Step 7: Run full unit suite to check for regressions**

```bash
bin/test/units.bash
```

Expected: all pass.

**Step 8: Commit**

```bash
git add src/plcc/spec/plcc_spec_cli.py src/plcc/spec/plcc_spec_cli_test.py pyproject.toml
git commit -m "feat(spec): add plcc-spec standalone entry point"
```

---

### Task 8: `plcc-tokens` — standalone entry point with JSONL output

`plcc-tokens` reads a spec JSON file (output of `plcc-spec`) and a text stream on stdin, outputs token JSONL.

**Key design decisions:**
- Input: `--spec=<path>` pointing to spec JSON (not the raw grammar file)
- Output: one JSON object per line — `{"kind": "token", "name": ..., "lexeme": ..., "source": {...}}`
- Lex errors become in-band error records: `{"kind": "error", "stage": "plcc-tokens", "source": {...}}`

**Files:**
- Create: `src/plcc/tokens/tokens_cli.py`
- Create: `src/plcc/tokens/tokens_cli_test.py`
- Create: `src/plcc/tokens/jsonl_formatter.py`
- Create: `src/plcc/tokens/jsonl_formatter_test.py`
- Create: `src/plcc/tokens/spec_loader.py`
- Create: `src/plcc/tokens/spec_loader_test.py`
- Modify: `pyproject.toml`

**Step 1: Write the failing test for `spec_loader`**

Create `src/plcc/tokens/spec_loader_test.py`:

```python
import json
import pytest
from pyfakefs.fake_filesystem_unittest import Patcher

from .spec_loader import load_lexical_rules


def test_loads_lexical_rules(fs):
    spec = {
        "lexical": {
            "ruleList": [
                {"name": "NUM", "pattern": "\\d+", "isSkip": False,
                 "line": {"string": "", "number": 1, "file": None}}
            ]
        },
        "syntax": {"rules": []},
        "semantics": []
    }
    fs.create_file('/spec.json', contents=json.dumps(spec))
    rules = load_lexical_rules('/spec.json')
    assert len(rules) == 1
    assert rules[0].name == 'NUM'
    assert rules[0].pattern == '\\d+'
    assert rules[0].isSkip is False


def test_empty_rule_list(fs):
    spec = {"lexical": {"ruleList": []}, "syntax": {"rules": []}, "semantics": []}
    fs.create_file('/empty.json', contents=json.dumps(spec))
    rules = load_lexical_rules('/empty.json')
    assert rules == []
```

**Step 2: Run to confirm failure**

```bash
pdm run pytest src/plcc/tokens/spec_loader_test.py -v
```

Expected: FAIL — module does not exist.

**Step 3: Create `src/plcc/tokens/spec_loader.py`**

```python
"""Load lexical rules from a spec JSON file for use by plcc-tokens."""

import json
from dataclasses import dataclass


@dataclass
class _LexicalRule:
    name: str
    pattern: str
    isSkip: bool


def load_lexical_rules(spec_json_path):
    """Return a list of lexical rule objects from a spec JSON file."""
    with open(spec_json_path) as f:
        data = json.load(f)
    return [
        _LexicalRule(name=r['name'], pattern=r['pattern'], isSkip=r['isSkip'])
        for r in data['lexical']['ruleList']
    ]
```

**Step 4: Run spec_loader tests to confirm pass**

```bash
pdm run pytest src/plcc/tokens/spec_loader_test.py -v
```

Expected: both pass.

**Step 5: Write the failing test for `jsonl_formatter`**

Create `src/plcc/tokens/jsonl_formatter_test.py`:

```python
import json
from ..lines import Line
from ..scan.Token import Token
from ..scan.LexError import LexError
from .jsonl_formatter import format_record


def _line(s='hello', n=1, f='test.txt'):
    return Line(string=s, number=n, file=f)


def test_formats_token():
    t = Token(lexeme='42', name='NUM', line=_line(), column=3)
    record = json.loads(format_record(t))
    assert record['kind'] == 'token'
    assert record['name'] == 'NUM'
    assert record['lexeme'] == '42'
    assert record['source']['line'] == 1
    assert record['source']['column'] == 3
    assert record['source']['file'] == 'test.txt'


def test_formats_lex_error():
    e = LexError(line=_line(), column=5)
    record = json.loads(format_record(e))
    assert record['kind'] == 'error'
    assert record['stage'] == 'plcc-tokens'
    assert record['source']['column'] == 5


def test_output_is_single_line():
    t = Token(lexeme='x', name='A', line=_line(), column=1)
    output = format_record(t)
    assert '\n' not in output
```

**Step 6: Run to confirm failure**

```bash
pdm run pytest src/plcc/tokens/jsonl_formatter_test.py -v
```

Expected: FAIL — module does not exist.

**Step 7: Create `src/plcc/tokens/jsonl_formatter.py`**

```python
"""JSONL formatter for plcc-tokens output."""

import json

from ..scan.Token import Token
from ..scan.LexError import LexError


def format_record(obj):
    """Return a single-line JSON string for a token or lex error."""
    if isinstance(obj, Token):
        return json.dumps({
            'kind': 'token',
            'name': obj.name,
            'lexeme': obj.lexeme,
            'source': {
                'file': obj.line.file,
                'line': obj.line.number,
                'column': obj.column,
            },
        })
    elif isinstance(obj, LexError):
        return json.dumps({
            'kind': 'error',
            'stage': 'plcc-tokens',
            'source': {
                'file': obj.line.file,
                'line': obj.line.number,
                'column': obj.column,
            },
        })
    else:
        raise TypeError(f'Unexpected type: {type(obj)}')
```

**Step 8: Run jsonl_formatter tests to confirm pass**

```bash
pdm run pytest src/plcc/tokens/jsonl_formatter_test.py -v
```

Expected: all 3 pass.

**Step 9: Write the failing test for `tokens_cli`**

Create `src/plcc/tokens/tokens_cli_test.py`:

```python
import io
import json
import pytest
import docopt

from .tokens_cli import main as run_main


def test_no_args_prints_usage():
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_help(capsys):
    with pytest.raises(SystemExit):
        run_main(['--help'])
    out, err = capsys.readouterr()
    assert 'Usage' in out


def test_outputs_token_jsonl(capsys, monkeypatch, fs):
    spec = {
        "lexical": {"ruleList": [
            {"name": "NUM", "pattern": "\\d+", "isSkip": False,
             "line": {"string": "", "number": 1, "file": None}}
        ]},
        "syntax": {"rules": []},
        "semantics": []
    }
    import json as _json
    fs.create_file('/spec.json', contents=_json.dumps(spec))
    monkeypatch.setattr('sys.stdin', io.StringIO('42\n'))
    run_main(['/spec.json'])
    out, err = capsys.readouterr()
    lines = [l for l in out.strip().splitlines() if l]
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record['kind'] == 'token'
    assert record['name'] == 'NUM'
    assert record['lexeme'] == '42'


def test_lex_error_is_inband(capsys, monkeypatch, fs):
    spec = {
        "lexical": {"ruleList": [
            {"name": "NUM", "pattern": "\\d+", "isSkip": False,
             "line": {"string": "", "number": 1, "file": None}}
        ]},
        "syntax": {"rules": []},
        "semantics": []
    }
    import json as _json
    fs.create_file('/spec.json', contents=_json.dumps(spec))
    monkeypatch.setattr('sys.stdin', io.StringIO('abc\n'))  # not a NUM
    run_main(['/spec.json'])
    out, err = capsys.readouterr()
    lines = [l for l in out.strip().splitlines() if l]
    assert any(json.loads(l)['kind'] == 'error' for l in lines)
    # stderr must be empty — errors are in-band
    assert err == ''
```

**Step 10: Run to confirm failure**

```bash
pdm run pytest src/plcc/tokens/tokens_cli_test.py -v
```

Expected: FAIL — module does not exist.

**Step 11: Create `src/plcc/tokens/__init__.py`**

Empty file to make it a package:

```python
```

**Step 12: Create `src/plcc/tokens/tokens_cli.py`**

```python
"""plcc-tokens
    Tokenize stdin given a spec JSON file, output token JSONL.

Usage:
    plcc-tokens [options] SPEC_JSON

Arguments:
    SPEC_JSON   Path to spec JSON file (output of plcc-spec).

Options:
    -h --help   Show this message.
"""

import sys

from docopt import docopt

from ..lines import Line
from ..scan.matcher import Matcher
from ..scan.scanner import Scanner
from ..scan.Skip import Skip
from .spec_loader import load_lexical_rules
from .jsonl_formatter import format_record


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    rules = load_lexical_rules(args['SPEC_JSON'])
    matcher = Matcher(rules)
    scanner = Scanner(matcher)
    lines = _read_stdin_as_lines()
    for obj in scanner.scan(lines):
        if isinstance(obj, Skip):
            continue
        print(format_record(obj), flush=True)


def _read_stdin_as_lines():
    for i, raw in enumerate(sys.stdin, start=1):
        yield Line(string=raw.rstrip('\n'), number=i, file='<stdin>')
```

**Step 13: Run tokens_cli tests to confirm pass**

```bash
pdm run pytest src/plcc/tokens/tokens_cli_test.py -v
```

Expected: all 4 pass.

**Step 14: Wire the entry point**

Add to `[project.scripts]` in `pyproject.toml`:

```toml
plcc-tokens = "plcc.tokens.tokens_cli:main"
```

**Step 15: Run full unit suite**

```bash
bin/test/units.bash
```

Expected: all pass.

**Step 16: Commit**

```bash
git add src/plcc/tokens/ pyproject.toml
git commit -m "feat(tokens): add plcc-tokens standalone entry point with JSONL output"
```

---

### Task 9: `plcc-tree` — minimal parse tree for trivial grammar

`plcc-tree` reads token JSONL from stdin and outputs tree JSONL. Phase 1 implementation handles the trivial grammar only: one `<program>` rule consuming one `NUM` token.

**Files:**
- Create: `src/plcc/tree/__init__.py`
- Create: `src/plcc/tree/tree_cli.py`
- Create: `src/plcc/tree/tree_cli_test.py`
- Modify: `pyproject.toml`

**Step 1: Write the failing test**

Create `src/plcc/tree/tree_cli_test.py`:

```python
import io
import json
import pytest
import docopt

from .tree_cli import main as run_main


_ONE_TOKEN = json.dumps({
    'kind': 'token', 'name': 'NUM', 'lexeme': '42',
    'source': {'file': '<stdin>', 'line': 1, 'column': 1}
})

_ONE_ERROR = json.dumps({
    'kind': 'error', 'stage': 'plcc-tokens',
    'source': {'file': '<stdin>', 'line': 1, 'column': 1}
})


def test_no_args_prints_usage():
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_help(capsys):
    with pytest.raises(SystemExit):
        run_main(['--help'])
    out, err = capsys.readouterr()
    assert 'Usage' in out


def test_token_stream_produces_tree(capsys, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(_ONE_TOKEN + '\n'))
    run_main(['--spec=tests/fixtures/trivial.plcc'])
    out, err = capsys.readouterr()
    lines = [l for l in out.strip().splitlines() if l]
    assert len(lines) == 1
    tree = json.loads(lines[0])
    assert tree['kind'] == 'tree'
    assert tree['rule'] == 'program'


def test_error_record_passes_through(capsys, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(_ONE_ERROR + '\n'))
    run_main(['--spec=tests/fixtures/trivial.plcc'])
    out, err = capsys.readouterr()
    lines = [l for l in out.strip().splitlines() if l]
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record['kind'] == 'error'
    assert err == ''  # error stays in-band
```

**Step 2: Run to confirm failure**

```bash
pdm run pytest src/plcc/tree/tree_cli_test.py -v
```

Expected: FAIL.

**Step 3: Create `src/plcc/tree/__init__.py`**

Empty file.

**Step 4: Create `src/plcc/tree/tree_cli.py`**

```python
"""plcc-tree
    Parse token JSONL from stdin into tree JSONL.

Usage:
    plcc-tree [options] --spec=SPEC_JSON

Options:
    --spec=SPEC_JSON   Path to spec JSON file (output of plcc-spec).
    -h --help          Show this message.
"""

import json
import sys

from docopt import docopt


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        if record.get('kind') == 'error':
            # Pass error records through unchanged
            print(json.dumps(record), flush=True)
        elif record.get('kind') == 'token':
            # Wrap each token in a minimal tree record
            tree = {
                'kind': 'tree',
                'rule': 'program',
                'children': [record],
            }
            print(json.dumps(tree), flush=True)
```

**Step 5: Run tests to confirm pass**

```bash
pdm run pytest src/plcc/tree/tree_cli_test.py -v
```

Expected: all 4 pass.

**Step 6: Wire the entry point**

```toml
plcc-tree = "plcc.tree.tree_cli:main"
```

**Step 7: Run full unit suite and commit**

```bash
bin/test/units.bash
git add src/plcc/tree/ pyproject.toml
git commit -m "feat(tree): add plcc-tree minimal pass-through for trivial grammar"
```

---

### Task 10: `plcc-model` — initial code model for trivial grammar

`plcc-model` reads spec JSON (from a file path argument or stdin) and outputs model JSON. Phase 1: produces the model for the trivial grammar only.

**Files:**
- Create: `src/plcc/model/__init__.py`
- Create: `src/plcc/model/build_model.py`
- Create: `src/plcc/model/build_model_test.py`
- Create: `src/plcc/model/model_cli.py`
- Create: `src/plcc/model/model_cli_test.py`
- Modify: `pyproject.toml`

**Step 1: Write the failing test for `build_model`**

Create `src/plcc/model/build_model_test.py`:

```python
import json
import pytest
from .build_model import build_model


_TRIVIAL_SPEC = {
    "lexical": {
        "ruleList": [
            {"name": "NUM", "pattern": "\\d+", "isSkip": False,
             "line": {"string": "", "number": 1, "file": None}}
        ]
    },
    "syntax": {
        "rules": [
            {
                "lhs": {"name": "program"},
                "rhs": [{"kind": "capturing_terminal", "name": "NUM", "field": "num"}]
            }
        ]
    },
    "semantics": [
        {"language": "PlantUML", "tool": "diagram", "codeFragmentList": []}
    ]
}


def test_returns_model_with_start():
    model = build_model(_TRIVIAL_SPEC)
    assert model['start'] == 'program'


def test_returns_one_class():
    model = build_model(_TRIVIAL_SPEC)
    assert len(model['classes']) == 1
    assert model['classes'][0]['name'] == 'Program'


def test_class_has_num_field():
    model = build_model(_TRIVIAL_SPEC)
    fields = model['classes'][0]['fields']
    assert any(f['name'] == 'num' and f['type'] == 'Token' for f in fields)


def test_semantic_sections_present():
    model = build_model(_TRIVIAL_SPEC)
    sections = model['semantic_sections']
    assert any(s['tool'] == 'diagram' and s['language'] == 'PlantUML' for s in sections)
```

**Step 2: Run to confirm failure**

```bash
pdm run pytest src/plcc/model/build_model_test.py -v
```

Expected: FAIL.

**Step 3: Create `src/plcc/model/__init__.py`**

Empty.

**Step 4: Create `src/plcc/model/build_model.py`**

```python
"""Transform spec JSON into a language-neutral code model."""


def build_model(spec):
    """
    Given a parsed spec dict (output of plcc-spec deserialized),
    return a model dict ready for JSON serialization.
    """
    classes = _build_classes(spec)
    semantic_sections = _build_semantic_sections(spec)
    start = _find_start(spec)
    return {
        'start': start,
        'classes': classes,
        'semantic_sections': semantic_sections,
    }


def _find_start(spec):
    rules = spec.get('syntax', {}).get('rules', [])
    if not rules:
        return None
    return rules[0]['lhs']['name']


def _build_classes(spec):
    classes = []
    for rule in spec.get('syntax', {}).get('rules', []):
        lhs_name = rule['lhs']['name']
        class_name = lhs_name.capitalize()
        fields = _extract_fields(rule.get('rhs', []))
        classes.append({
            'name': class_name,
            'extends': None,
            'fields': fields,
            'methods': [],
        })
    return classes


def _extract_fields(rhs):
    fields = []
    for symbol in rhs:
        kind = symbol.get('kind', '')
        if 'capturing' in kind:
            field_name = symbol.get('field') or symbol.get('name', '').lower()
            field_type = 'Token' if 'terminal' in kind else symbol.get('name', 'Object').capitalize()
            fields.append({'name': field_name, 'type': field_type})
    return fields


def _build_semantic_sections(spec):
    return [
        {'tool': s['tool'], 'language': s['language']}
        for s in spec.get('semantics', [])
    ]
```

**Step 5: Run build_model tests to confirm pass**

```bash
pdm run pytest src/plcc/model/build_model_test.py -v
```

Expected: all 4 pass.

**Step 6: Write the failing test for `model_cli`**

Create `src/plcc/model/model_cli_test.py`:

```python
import io
import json
import pytest
import docopt

from .model_cli import main as run_main


_TRIVIAL_SPEC_JSON = json.dumps({
    "lexical": {"ruleList": [
        {"name": "NUM", "pattern": "\\d+", "isSkip": False,
         "line": {"string": "", "number": 1, "file": None}}
    ]},
    "syntax": {"rules": [
        {"lhs": {"name": "program"},
         "rhs": [{"kind": "capturing_terminal", "name": "NUM", "field": "num"}]}
    ]},
    "semantics": [{"language": "PlantUML", "tool": "diagram", "codeFragmentList": []}]
})


def test_no_args_prints_usage():
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_help(capsys):
    with pytest.raises(SystemExit):
        run_main(['--help'])
    out, err = capsys.readouterr()
    assert 'Usage' in out


def test_reads_spec_from_file(capsys, fs):
    fs.create_file('/spec.json', contents=_TRIVIAL_SPEC_JSON)
    run_main(['/spec.json'])
    out, err = capsys.readouterr()
    model = json.loads(out)
    assert 'classes' in model
    assert model['start'] == 'program'


def test_reads_spec_from_stdin(capsys, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_SPEC_JSON))
    run_main(['-'])
    out, err = capsys.readouterr()
    model = json.loads(out)
    assert model['start'] == 'program'
```

**Step 7: Run to confirm failure**

```bash
pdm run pytest src/plcc/model/model_cli_test.py -v
```

Expected: FAIL.

**Step 8: Create `src/plcc/model/model_cli.py`**

```python
"""plcc-model
    Transform spec JSON into a language-neutral code model.

Usage:
    plcc-model [options] [SPEC_JSON]

Arguments:
    SPEC_JSON   Path to spec JSON file. Use - or omit to read from stdin.

Options:
    -h --help   Show this message.
"""

import json
import sys

from docopt import docopt

from .build_model import build_model


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    path = args['SPEC_JSON'] or '-'
    spec = _load(path)
    model = build_model(spec)
    print(json.dumps(model, indent=2))


def _load(path):
    if path == '-':
        return json.load(sys.stdin)
    with open(path) as f:
        return json.load(f)
```

**Step 9: Run model_cli tests to confirm pass**

```bash
pdm run pytest src/plcc/model/model_cli_test.py -v
```

Expected: all 4 pass.

**Step 10: Wire the entry point**

```toml
plcc-model = "plcc.model.model_cli:main"
```

**Step 11: Run full unit suite and commit**

```bash
bin/test/units.bash
git add src/plcc/model/ pyproject.toml
git commit -m "feat(model): add plcc-model initial implementation for trivial grammar"
```

---

### Task 11: `plcc-plantuml-emit` — minimal PlantUML plugin

`plcc-plantuml-emit` reads model JSON from stdin, writes a `.puml` file to `--output`.

**Files:**
- Create: `src/plcc/lang/ext/plantuml/__init__.py`
- Create: `src/plcc/lang/ext/plantuml/emit.py`
- Create: `src/plcc/lang/ext/plantuml/emit_test.py`
- Modify: `pyproject.toml`

**Step 1: Create directory structure**

```bash
mkdir -p src/plcc/lang/ext/plantuml
touch src/plcc/lang/__init__.py
touch src/plcc/lang/ext/__init__.py
touch src/plcc/lang/ext/plantuml/__init__.py
```

**Step 2: Write the failing test**

Create `src/plcc/lang/ext/plantuml/emit_test.py`:

```python
import json
import os
import pytest

from .emit import main as run_main


_TRIVIAL_MODEL = json.dumps({
    'start': 'program',
    'classes': [
        {'name': 'Program', 'extends': None,
         'fields': [{'name': 'num', 'type': 'Token'}],
         'methods': []}
    ],
    'semantic_sections': [{'tool': 'diagram', 'language': 'PlantUML'}]
})


def test_no_args_prints_usage():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_creates_puml_file(tmp_path, monkeypatch):
    import io
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))
    run_main([f'--output={tmp_path}'])
    puml_files = list(tmp_path.glob('*.puml'))
    assert len(puml_files) == 1


def test_puml_contains_class_name(tmp_path, monkeypatch):
    import io
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))
    run_main([f'--output={tmp_path}'])
    content = list(tmp_path.glob('*.puml'))[0].read_text()
    assert 'Program' in content


def test_puml_contains_field(tmp_path, monkeypatch):
    import io
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))
    run_main([f'--output={tmp_path}'])
    content = list(tmp_path.glob('*.puml'))[0].read_text()
    assert 'num' in content


def test_exits_zero_on_success(tmp_path, monkeypatch):
    import io
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))
    # Should not raise SystemExit
    run_main([f'--output={tmp_path}'])
```

**Step 3: Run to confirm failure**

```bash
pdm run pytest src/plcc/lang/ext/plantuml/emit_test.py -v
```

Expected: FAIL.

**Step 4: Create `src/plcc/lang/ext/plantuml/emit.py`**

```python
"""plcc-plantuml-emit
    Emit PlantUML class diagram from model JSON.

Usage:
    plcc-plantuml-emit --output=DIR [options]

Options:
    --output=DIR    Directory to write output files into.
    -h --help       Show this message.
"""

import json
import os
import sys

from docopt import docopt


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    output_dir = args['--output']
    os.makedirs(output_dir, exist_ok=True)
    model = json.load(sys.stdin)
    for cls in model.get('classes', []):
        _emit_class(cls, output_dir)


def _emit_class(cls, output_dir):
    name = cls['name']
    fields = cls.get('fields', [])
    lines = ['@startuml', f'class {name} {{']
    for field in fields:
        lines.append(f'  {field["name"]}: {field["type"]}')
    lines += ['}', '@enduml']
    path = os.path.join(output_dir, f'{name.lower()}.puml')
    with open(path, 'w') as f:
        f.write('\n'.join(lines) + '\n')
```

**Step 5: Run tests to confirm pass**

```bash
pdm run pytest src/plcc/lang/ext/plantuml/emit_test.py -v
```

Expected: all 5 pass.

**Step 6: Wire the entry point**

```toml
plcc-plantuml-emit = "plcc.lang.ext.plantuml.emit:main"
```

**Step 7: Run full unit suite and commit**

```bash
bin/test/units.bash
git add src/plcc/lang/ pyproject.toml
git commit -m "feat(plantuml): add plcc-plantuml-emit minimal plugin"
```

---

### Task 12: `plcc-lang-emit` — dispatcher

`plcc-lang-emit` constructs `plcc-<lang>-emit` and execs it, passing model JSON from stdin.

**Files:**
- Create: `src/plcc/lang/emit.py`
- Create: `src/plcc/lang/emit_test.py`
- Modify: `pyproject.toml`

**Step 1: Write the failing test**

Create `src/plcc/lang/emit_test.py`:

```python
import subprocess
import json
import pytest
import docopt

from .emit import main as run_main, resolve_emit_command


def test_no_args_prints_usage():
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_resolve_plantuml():
    cmd = resolve_emit_command('PlantUML')
    assert cmd == 'plcc-plantuml-emit'


def test_resolve_lowercases_lang():
    cmd = resolve_emit_command('Java')
    assert cmd == 'plcc-java-emit'


def test_missing_plugin_exits_nonzero(tmp_path, monkeypatch):
    import io
    monkeypatch.setattr('sys.stdin', io.StringIO('{}'))
    with pytest.raises(SystemExit) as exc:
        run_main([f'--target=NoSuchLang9999', f'--output={tmp_path}'])
    assert exc.value.code != 0
```

**Step 2: Run to confirm failure**

```bash
pdm run pytest src/plcc/lang/emit_test.py -v
```

Expected: FAIL.

**Step 3: Create `src/plcc/lang/emit.py`**

```python
"""plcc-lang-emit
    Dispatch to the appropriate plcc-<lang>-emit command.

Usage:
    plcc-lang-emit --target=LANG --output=DIR

Options:
    --target=LANG   Target language (e.g. PlantUML, Java, Python).
    --output=DIR    Directory to write output files into.
    -h --help       Show this message.
"""

import shutil
import subprocess
import sys

from docopt import docopt


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    lang = args['--target']
    output = args['--output']
    cmd = resolve_emit_command(lang)
    if not shutil.which(cmd):
        print(
            f"No emitter found for '{lang}'. Is {cmd} installed?\n"
            f"Run plcc-lang-list to see what is available.",
            file=sys.stderr,
        )
        sys.exit(1)
    result = subprocess.run(
        [cmd, f'--output={output}'],
        stdin=sys.stdin,
    )
    sys.exit(result.returncode)


def resolve_emit_command(lang):
    return f'plcc-{lang.lower()}-emit'
```

**Step 4: Run tests to confirm pass**

```bash
pdm run pytest src/plcc/lang/emit_test.py -v
```

Expected: all 4 pass.

**Step 5: Wire the entry point**

```toml
plcc-lang-emit = "plcc.lang.emit:main"
```

**Step 6: Commit**

```bash
git add src/plcc/lang/emit.py src/plcc/lang/emit_test.py pyproject.toml
git commit -m "feat(lang): add plcc-lang-emit dispatcher"
```

---

### Task 13: `plcc-lang-build` — dispatcher

`plcc-lang-build` constructs `plcc-<lang>-build` and execs it, exiting 0 silently if not found.

**Files:**
- Create: `src/plcc/lang/build.py`
- Create: `src/plcc/lang/build_test.py`
- Modify: `pyproject.toml`

**Step 1: Write the failing test**

Create `src/plcc/lang/build_test.py`:

```python
import pytest
import docopt

from .build import main as run_main, resolve_build_command


def test_no_args_prints_usage():
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_resolve_build_command():
    cmd = resolve_build_command('Java')
    assert cmd == 'plcc-java-build'


def test_missing_build_command_exits_zero(tmp_path):
    # plcc-plantuml-build does not exist — should exit 0 silently
    try:
        run_main([f'--target=PlantUML', f'--output={tmp_path}'])
    except SystemExit as e:
        assert e.code == 0
```

**Step 2: Run to confirm failure**

```bash
pdm run pytest src/plcc/lang/build_test.py -v
```

**Step 3: Create `src/plcc/lang/build.py`**

```python
"""plcc-lang-build
    Dispatch to the appropriate plcc-<lang>-build command if it exists.

Usage:
    plcc-lang-build --target=LANG --output=DIR

Options:
    --target=LANG   Target language.
    --output=DIR    Output directory (already populated by plcc-lang-emit).
    -h --help       Show this message.
"""

import shutil
import subprocess
import sys

from docopt import docopt


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    lang = args['--target']
    output = args['--output']
    cmd = resolve_build_command(lang)
    if not shutil.which(cmd):
        sys.exit(0)  # No build step for this language — not an error
    result = subprocess.run([cmd, f'--output={output}'])
    sys.exit(result.returncode)


def resolve_build_command(lang):
    return f'plcc-{lang.lower()}-build'
```

**Step 4: Run tests to confirm pass**

```bash
pdm run pytest src/plcc/lang/build_test.py -v
```

**Step 5: Wire entry point and commit**

```toml
plcc-lang-build = "plcc.lang.build:main"
```

```bash
git add src/plcc/lang/build.py src/plcc/lang/build_test.py pyproject.toml
git commit -m "feat(lang): add plcc-lang-build dispatcher"
```

---

### Task 14: `plcc-lang-list` — discover installed emitters

`plcc-lang-list` scans PATH for `plcc-*-emit` commands and prints one language name per line.

**Files:**
- Create: `src/plcc/lang/list.py`
- Create: `src/plcc/lang/list_test.py`
- Modify: `pyproject.toml`

**Step 1: Write the failing test**

Create `src/plcc/lang/list_test.py`:

```python
import pytest
from .list import find_languages, extract_language_name


def test_extract_language_name():
    assert extract_language_name('plcc-plantuml-emit') == 'plantuml'
    assert extract_language_name('plcc-java-emit') == 'java'


def test_extract_ignores_non_matching():
    assert extract_language_name('plcc-lang-emit') is None
    assert extract_language_name('python') is None


def test_find_languages_returns_list(monkeypatch):
    monkeypatch.setenv('PATH', '/fake/bin')
    import os, pathlib
    # Not testing actual PATH scan here — just that function is callable
    result = find_languages()
    assert isinstance(result, list)
```

**Step 2: Run to confirm failure**

```bash
pdm run pytest src/plcc/lang/list_test.py -v
```

**Step 3: Create `src/plcc/lang/list.py`**

```python
"""plcc-lang-list
    List installed language emitter plugins.

Usage:
    plcc-lang-list

Options:
    -h --help   Show this message.
"""

import os
import re
import shutil
import sys

from docopt import docopt

_EMIT_PATTERN = re.compile(r'^plcc-(.+)-emit$')


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    docopt(__doc__, argv)
    for lang in sorted(find_languages()):
        print(lang)


def find_languages():
    """Scan PATH for plcc-*-emit commands; return list of language names."""
    languages = []
    seen = set()
    for directory in _path_dirs():
        try:
            for entry in os.scandir(directory):
                name = extract_language_name(entry.name)
                if name and name not in seen and _is_executable(entry):
                    languages.append(name)
                    seen.add(name)
        except (PermissionError, FileNotFoundError):
            continue
    return languages


def extract_language_name(command_name):
    """Return the language name from a plcc-<lang>-emit command name, or None."""
    m = _EMIT_PATTERN.match(command_name)
    if m:
        lang = m.group(1)
        # Exclude the dispatcher itself
        if lang != 'lang':
            return lang
    return None


def _path_dirs():
    return os.environ.get('PATH', '').split(os.pathsep)


def _is_executable(entry):
    return entry.is_file() and os.access(entry.path, os.X_OK)
```

**Step 4: Run tests to confirm pass**

```bash
pdm run pytest src/plcc/lang/list_test.py -v
```

**Step 5: Wire entry point and commit**

```toml
plcc-lang-list = "plcc.lang.list:main"
```

```bash
git add src/plcc/lang/list.py src/plcc/lang/list_test.py pyproject.toml
git commit -m "feat(lang): add plcc-lang-list PATH scanner"
```

---

## Part 4 — Level 2 Commands

### Task 15: `plcc-make` — orchestrator

`plcc-make` runs the full build pipeline for a grammar file.

**Files:**
- Create: `src/plcc/cmd/__init__.py`
- Create: `src/plcc/cmd/make.py`
- Create: `src/plcc/cmd/make_test.py`
- Modify: `pyproject.toml`

**Step 1: Write the failing test**

Create `src/plcc/cmd/make_test.py`:

```python
import pytest
import docopt

from .make import main as run_main, validate_tool_name


def test_no_args_prints_usage():
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_help(capsys):
    with pytest.raises(SystemExit):
        run_main(['--help'])
    out, err = capsys.readouterr()
    assert 'Usage' in out


def test_validate_tool_name_accepts_valid():
    validate_tool_name('diagram')
    validate_tool_name('Java')
    validate_tool_name('my-tool')
    validate_tool_name('tool_123')


def test_validate_tool_name_rejects_path_traversal():
    with pytest.raises(ValueError):
        validate_tool_name('../etc')
    with pytest.raises(ValueError):
        validate_tool_name('foo/bar')
    with pytest.raises(ValueError):
        validate_tool_name('/absolute')


def test_validate_tool_name_rejects_empty():
    with pytest.raises(ValueError):
        validate_tool_name('')
```

**Step 2: Run to confirm failure**

```bash
pdm run pytest src/plcc/cmd/make_test.py -v
```

**Step 3: Create `src/plcc/cmd/__init__.py`**

Empty.

**Step 4: Create `src/plcc/cmd/make.py`**

```python
"""plcc-make
    Build a PLCC project from a grammar file.

Usage:
    plcc-make GRAMMAR

Arguments:
    GRAMMAR     Path to the PLCC grammar file.

Options:
    -h --help   Show this message.
"""

import json
import os
import re
import shutil
import subprocess
import sys

from docopt import docopt

_TOOL_NAME_RE = re.compile(r'^[a-zA-Z0-9_-]+$')


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    grammar = args['GRAMMAR']
    build_dir = 'build'

    # 1. Clean
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)

    # 2. Spec
    spec_json = os.path.join(build_dir, 'spec.json')
    _run_or_die(['plcc-spec', grammar], stdout_file=spec_json)

    # 3. Model
    model_json = os.path.join(build_dir, 'model.json')
    _run_or_die(['plcc-model', spec_json], stdout_file=model_json)

    # 4 & 5. Emit and build per semantic section
    with open(spec_json) as f:
        spec = json.load(f)
    for section in spec.get('semantics', []):
        tool = section['tool']
        lang = section['language']
        validate_tool_name(tool)
        output_dir = os.path.join(build_dir, tool)
        os.makedirs(output_dir, exist_ok=True)
        with open(model_json) as model_f:
            _run_or_die(
                ['plcc-lang-emit', f'--target={lang}', f'--output={output_dir}'],
                stdin_file=model_json,
            )
        _run_or_die(['plcc-lang-build', f'--target={lang}', f'--output={output_dir}'])


def validate_tool_name(name):
    """Raise ValueError if tool name could escape build/."""
    if not name or not _TOOL_NAME_RE.match(name):
        raise ValueError(
            f"Invalid tool name '{name}'. "
            "Tool names must match [a-zA-Z0-9_-]+ to prevent path traversal."
        )


def _run_or_die(cmd, stdout_file=None, stdin_file=None):
    stdin = open(stdin_file) if stdin_file else None
    stdout = open(stdout_file, 'w') if stdout_file else None
    try:
        result = subprocess.run(cmd, stdin=stdin, stdout=stdout)
        if result.returncode != 0:
            print(f"plcc-make: {cmd[0]} failed (exit {result.returncode})", file=sys.stderr)
            sys.exit(result.returncode)
    finally:
        if stdin:
            stdin.close()
        if stdout:
            stdout.close()
```

**Step 5: Run tests to confirm pass**

```bash
pdm run pytest src/plcc/cmd/make_test.py -v
```

Expected: all 5 pass.

**Step 6: Wire the entry point**

```toml
plcc-make = "plcc.cmd.make:main"
```

**Step 7: Run full unit suite and commit**

```bash
bin/test/units.bash
git add src/plcc/cmd/ pyproject.toml
git commit -m "feat(make): add plcc-make orchestrator"
```

---

### Task 16: Level 2 skeleton commands

`plcc-scan`, `plcc-parse`, and `plcc-rep` print "not yet implemented" and exit 1. They exist to confirm the packaging wiring is complete and make the full command surface visible.

**Files:**
- Create: `src/plcc/cmd/scan.py`
- Create: `src/plcc/cmd/parse.py`
- Create: `src/plcc/cmd/rep.py`
- Create: `src/plcc/cmd/skeleton_test.py`
- Modify: `pyproject.toml`

**Step 1: Write the failing test**

Create `src/plcc/cmd/skeleton_test.py`:

```python
import pytest

from .scan import main as scan_main
from .parse import main as parse_main
from .rep import main as rep_main


def _exits_nonzero(fn):
    with pytest.raises(SystemExit) as exc:
        fn([])
    assert exc.value.code != 0


def test_scan_exits_nonzero():
    _exits_nonzero(scan_main)


def test_parse_exits_nonzero():
    _exits_nonzero(parse_main)


def test_rep_exits_nonzero():
    _exits_nonzero(rep_main)


def test_scan_prints_not_implemented(capsys):
    with pytest.raises(SystemExit):
        scan_main([])
    out, err = capsys.readouterr()
    assert 'not yet implemented' in (out + err).lower()
```

**Step 2: Run to confirm failure**

```bash
pdm run pytest src/plcc/cmd/skeleton_test.py -v
```

**Step 3: Create the three skeleton modules**

`src/plcc/cmd/scan.py`:

```python
import sys

def main(argv=None):
    print("plcc-scan: not yet implemented", file=sys.stderr)
    sys.exit(1)
```

`src/plcc/cmd/parse.py`:

```python
import sys

def main(argv=None):
    print("plcc-parse: not yet implemented", file=sys.stderr)
    sys.exit(1)
```

`src/plcc/cmd/rep.py`:

```python
import sys

def main(argv=None):
    print("plcc-rep: not yet implemented", file=sys.stderr)
    sys.exit(1)
```

**Step 4: Run tests to confirm pass**

```bash
pdm run pytest src/plcc/cmd/skeleton_test.py -v
```

**Step 5: Wire the entry points**

```toml
plcc-scan  = "plcc.cmd.scan:main"
plcc-parse = "plcc.cmd.parse:main"
plcc-rep   = "plcc.cmd.rep:main"
```

**Step 6: Commit**

```bash
pdm install
bin/test/units.bash
git add src/plcc/cmd/scan.py src/plcc/cmd/parse.py src/plcc/cmd/rep.py \
        src/plcc/cmd/skeleton_test.py pyproject.toml
git commit -m "feat(cmd): add plcc-scan, plcc-parse, plcc-rep skeleton entry points"
```

---

## Part 5 — Developer Tooling and BATS Tests

### Task 17: Install BATS and create `bin/` scripts

**Files:**
- Create: `bin/install/bats.bash`
- Create: `bin/build/package.bash`
- Create: `bin/test/commands.bash`
- Create: `bin/test/integration.bash`
- Create: `bin/test/e2e.bash`
- Create: `bin/test/functional.bash`
- Create: `bin/test/packaging.bash`
- Create: `bin/test/all.bash`
- Create: `tests/bats/` directory structure

**Step 1: Create `bin/install/bats.bash`**

```bash
#!/usr/bin/env bash
set -euo pipefail

BATS_VERSION="1.11.0"
INSTALL_DIR="${HOME}/.local/lib/bats"
BIN_DIR="${HOME}/.local/bin"

if command -v bats &>/dev/null && bats --version | grep -q "${BATS_VERSION}"; then
    exit 0
fi

mkdir -p "${INSTALL_DIR}" "${BIN_DIR}"
TMPDIR=$(mktemp -d)
trap "rm -rf ${TMPDIR}" EXIT

git clone --depth 1 --branch "v${BATS_VERSION}" \
    https://github.com/bats-core/bats-core.git "${TMPDIR}/bats"
"${TMPDIR}/bats/install.sh" "${HOME}/.local"
```

Make it executable: `chmod +x bin/install/bats.bash`

**Step 2: Create `bin/build/package.bash`**

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/../.." &> /dev/null && pwd )"
cd "${PROJECT_ROOT}"

pdm install
pdm build
```

Make executable: `chmod +x bin/build/package.bash`

**Step 3: Create `bin/test/commands.bash`**

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/../.." &> /dev/null && pwd )"
cd "${PROJECT_ROOT}"

"${SCRIPT_DIR}/../../bin/install/bats.bash"
pdm install

bats tests/bats/commands/
```

Make executable and repeat pattern for `integration.bash` and `e2e.bash`:

`bin/test/integration.bash` — runs `tests/bats/integration/`
`bin/test/e2e.bash` — runs `tests/bats/e2e/`

**Step 4: Create `bin/test/functional.bash`**

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

"${SCRIPT_DIR}/units.bash"
"${SCRIPT_DIR}/commands.bash"
"${SCRIPT_DIR}/integration.bash"
"${SCRIPT_DIR}/e2e.bash"
```

**Step 5: Create `bin/test/packaging.bash`**

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/../.." &> /dev/null && pwd )"
cd "${PROJECT_ROOT}"

VENV=$(mktemp -d)
trap "rm -rf ${VENV}" EXIT

python -m venv "${VENV}"
"${VENV}/bin/pip" install --quiet dist/*.whl

# Verify all entry points are present
for cmd in plcc-spec plcc-tokens plcc-tree plcc-model \
           plcc-lang-emit plcc-lang-build plcc-lang-list \
           plcc-plantuml-emit plcc-make plcc-scan plcc-parse plcc-rep; do
    if ! "${VENV}/bin/${cmd}" --help &>/dev/null && \
       ! "${VENV}/bin/${cmd}" 2>&1 | grep -qi 'not yet implemented\|usage'; then
        echo "FAIL: ${cmd} not found or broken" >&2
        exit 1
    fi
    echo "OK: ${cmd}"
done

# Run end-to-end in the installed venv
"${VENV}/bin/plcc-make" tests/fixtures/trivial.plcc
test -f build/spec.json    || { echo "FAIL: build/spec.json missing"; exit 1; }
test -f build/model.json   || { echo "FAIL: build/model.json missing"; exit 1; }
ls build/diagram/*.puml    || { echo "FAIL: no .puml in build/diagram/"; exit 1; }
echo "packaging: all checks passed"
```

**Step 6: Create `bin/test/all.bash`**

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

"${SCRIPT_DIR}/functional.bash"
"${SCRIPT_DIR}/packaging.bash"
```

**Step 7: Create BATS directory structure**

```bash
mkdir -p tests/bats/commands tests/bats/integration tests/bats/e2e
```

**Step 8: Commit**

```bash
git add bin/ tests/bats/
chmod +x bin/install/bats.bash bin/build/package.bash \
         bin/test/commands.bash bin/test/integration.bash \
         bin/test/e2e.bash bin/test/functional.bash \
         bin/test/packaging.bash bin/test/all.bash
git commit -m "build(bin): add developer scripts for build, install, and test"
```

---

### Task 18: BATS command tests

One `.bats` file per command. Each verifies the command is on PATH, `--help` works, valid input produces schema-valid output, and bad input produces the right error behavior.

**Files:**
- Create: `tests/bats/commands/plcc-spec.bats`
- Create: `tests/bats/commands/plcc-tokens.bats`
- Create: `tests/bats/commands/plcc-tree.bats`
- Create: `tests/bats/commands/plcc-model.bats`
- Create: `tests/bats/commands/plcc-plantuml-emit.bats`
- Create: `tests/bats/commands/plcc-lang-emit.bats`
- Create: `tests/bats/commands/plcc-lang-build.bats`
- Create: `tests/bats/commands/plcc-lang-list.bats`
- Create: `tests/bats/commands/plcc-make.bats`
- Create: `tests/bats/commands/plcc-skeletons.bats`

**Step 1: Install BATS**

```bash
bin/install/bats.bash
pdm install
```

**Step 2: Create `tests/bats/commands/plcc-spec.bats`**

```bash
#!/usr/bin/env bats

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/spec.schema.json"
}

@test "plcc-spec is on PATH" {
    command -v plcc-spec
}

@test "plcc-spec --help exits 0 and prints Usage" {
    run plcc-spec --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"Usage"* ]]
}

@test "plcc-spec no args exits nonzero" {
    run plcc-spec
    [ "$status" -ne 0 ]
}

@test "plcc-spec trivial grammar outputs valid JSON" {
    run plcc-spec "${FIXTURES}/trivial.plcc"
    [ "$status" -eq 0 ]
    echo "$output" | python -m json.tool > /dev/null
}

@test "plcc-spec trivial grammar output validates against spec schema" {
    run plcc-spec "${FIXTURES}/trivial.plcc"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${SCHEMA}" -
}

@test "plcc-spec bad grammar exits nonzero and writes to stderr" {
    echo "num 'bad'" > /tmp/bad.plcc
    run plcc-spec /tmp/bad.plcc
    [ "$status" -ne 0 ]
    [ -n "$stderr" ] || [[ "$output" == *""* ]]  # error on stderr
}
```

**Step 3: Create `tests/bats/commands/plcc-tokens.bats`**

```bash
#!/usr/bin/env bats

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/token.schema.json"
    SPEC_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
}

teardown() {
    rm -f "${SPEC_JSON}"
}

@test "plcc-tokens is on PATH" {
    command -v plcc-tokens
}

@test "plcc-tokens --help exits 0" {
    run plcc-tokens --help
    [ "$status" -eq 0 ]
}

@test "plcc-tokens outputs token JSONL for trivial input" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}'"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${SCHEMA}" -
}

@test "plcc-tokens token record has kind=token" {
    result=$(echo '42' | plcc-tokens "${SPEC_JSON}")
    echo "$result" | python -c "import json,sys; r=json.load(sys.stdin); assert r['kind']=='token'"
}

@test "plcc-tokens lex error is in-band not stderr" {
    result=$(echo 'xyz' | plcc-tokens "${SPEC_JSON}" 2>/dev/null)
    # No stderr output for lex errors
    stderr_output=$(echo 'xyz' | plcc-tokens "${SPEC_JSON}" 2>&1 1>/dev/null)
    [ -z "$stderr_output" ]
    # Error is in stdout
    echo "$result" | python -c "import json,sys; r=json.load(sys.stdin); assert r['kind']=='error'"
}
```

**Step 4: Create `tests/bats/commands/plcc-model.bats`**

```bash
#!/usr/bin/env bats

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/model.schema.json"
    SPEC_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
}

teardown() {
    rm -f "${SPEC_JSON}"
}

@test "plcc-model is on PATH" {
    command -v plcc-model
}

@test "plcc-model --help exits 0" {
    run plcc-model --help
    [ "$status" -eq 0 ]
}

@test "plcc-model output validates against model schema" {
    run plcc-model "${SPEC_JSON}"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${SCHEMA}" -
}

@test "plcc-model output has Program class" {
    result=$(plcc-model "${SPEC_JSON}")
    echo "$result" | python -c "
import json, sys
m = json.load(sys.stdin)
names = [c['name'] for c in m['classes']]
assert 'Program' in names, f'Expected Program in {names}'
"
}

@test "plcc-model reads from stdin with -" {
    run bash -c "cat '${SPEC_JSON}' | plcc-model -"
    [ "$status" -eq 0 ]
}
```

**Step 5: Create the remaining command test files**

`tests/bats/commands/plcc-tree.bats`:

```bash
#!/usr/bin/env bats

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/tree.schema.json"
    SPEC_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
}

teardown() { rm -f "${SPEC_JSON}"; }

@test "plcc-tree is on PATH" { command -v plcc-tree; }

@test "plcc-tree outputs tree JSONL" {
    TOKEN=$(echo '42' | plcc-tokens "${SPEC_JSON}")
    run bash -c "echo '${TOKEN}' | plcc-tree --spec='${SPEC_JSON}'"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${SCHEMA}" -
}

@test "plcc-tree passes error records through" {
    ERROR=$(python -c "import json; print(json.dumps({'kind':'error','stage':'plcc-tokens','source':{'file':None,'line':1,'column':1}}))")
    result=$(echo "${ERROR}" | plcc-tree --spec="${SPEC_JSON}" 2>/dev/null)
    echo "$result" | python -c "import json,sys; r=json.load(sys.stdin); assert r['kind']=='error'"
}
```

`tests/bats/commands/plcc-lang-list.bats`:

```bash
#!/usr/bin/env bats

@test "plcc-lang-list is on PATH" { command -v plcc-lang-list; }

@test "plcc-lang-list exits 0" {
    run plcc-lang-list
    [ "$status" -eq 0 ]
}

@test "plcc-lang-list finds plantuml" {
    run plcc-lang-list
    [[ "$output" == *"plantuml"* ]]
}
```

`tests/bats/commands/plcc-lang-emit.bats`:

```bash
#!/usr/bin/env bats

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SPEC_JSON="$(mktemp)"
    MODEL_JSON="$(mktemp)"
    OUTPUT_DIR="$(mktemp -d)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
    plcc-model "${SPEC_JSON}" > "${MODEL_JSON}"
}

teardown() {
    rm -f "${SPEC_JSON}" "${MODEL_JSON}"
    rm -rf "${OUTPUT_DIR}"
}

@test "plcc-lang-emit is on PATH" { command -v plcc-lang-emit; }

@test "plcc-lang-emit missing plugin exits nonzero with message" {
    run bash -c "cat '${MODEL_JSON}' | plcc-lang-emit --target=NoSuchLang9999 --output='${OUTPUT_DIR}'"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "No emitter" ]] || [[ "$stderr" =~ "No emitter" ]]
}

@test "plcc-lang-emit PlantUML creates puml file" {
    run bash -c "cat '${MODEL_JSON}' | plcc-lang-emit --target=PlantUML --output='${OUTPUT_DIR}'"
    [ "$status" -eq 0 ]
    ls "${OUTPUT_DIR}"/*.puml
}
```

`tests/bats/commands/plcc-lang-build.bats`:

```bash
#!/usr/bin/env bats

@test "plcc-lang-build is on PATH" { command -v plcc-lang-build; }

@test "plcc-lang-build exits 0 for language with no build command" {
    run plcc-lang-build --target=PlantUML --output=/tmp
    [ "$status" -eq 0 ]
}
```

`tests/bats/commands/plcc-plantuml-emit.bats`:

```bash
#!/usr/bin/env bats

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SPEC_JSON="$(mktemp)"
    MODEL_JSON="$(mktemp)"
    OUTPUT_DIR="$(mktemp -d)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
    plcc-model "${SPEC_JSON}" > "${MODEL_JSON}"
}

teardown() {
    rm -f "${SPEC_JSON}" "${MODEL_JSON}"
    rm -rf "${OUTPUT_DIR}"
}

@test "plcc-plantuml-emit is on PATH" { command -v plcc-plantuml-emit; }

@test "plcc-plantuml-emit creates a .puml file" {
    run bash -c "cat '${MODEL_JSON}' | plcc-plantuml-emit --output='${OUTPUT_DIR}'"
    [ "$status" -eq 0 ]
    ls "${OUTPUT_DIR}"/*.puml
}

@test "plcc-plantuml-emit puml contains class name" {
    bash -c "cat '${MODEL_JSON}' | plcc-plantuml-emit --output='${OUTPUT_DIR}'"
    grep -r 'Program' "${OUTPUT_DIR}"/*.puml
}
```

`tests/bats/commands/plcc-make.bats`:

```bash
#!/usr/bin/env bats

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    cd "${WORK_DIR}"
}

teardown() {
    rm -rf "${WORK_DIR}"
}

@test "plcc-make is on PATH" { command -v plcc-make; }

@test "plcc-make --help exits 0" {
    run plcc-make --help
    [ "$status" -eq 0 ]
}

@test "plcc-make no args exits nonzero" {
    run plcc-make
    [ "$status" -ne 0 ]
}

@test "plcc-make trivial grammar produces build artifacts" {
    run plcc-make "${FIXTURES}/trivial.plcc"
    [ "$status" -eq 0 ]
    [ -f build/spec.json ]
    [ -f build/model.json ]
    ls build/diagram/*.puml
}
```

`tests/bats/commands/plcc-skeletons.bats`:

```bash
#!/usr/bin/env bats

@test "plcc-scan is on PATH" { command -v plcc-scan; }
@test "plcc-parse is on PATH" { command -v plcc-parse; }
@test "plcc-rep is on PATH" { command -v plcc-rep; }

@test "plcc-scan exits nonzero with not-implemented message" {
    run plcc-scan
    [ "$status" -ne 0 ]
    [[ "${output}${stderr}" =~ [Nn]ot.*[Ii]mplemented ]]
}

@test "plcc-parse exits nonzero" {
    run plcc-parse
    [ "$status" -ne 0 ]
}

@test "plcc-rep exits nonzero" {
    run plcc-rep
    [ "$status" -ne 0 ]
}
```

**Step 6: Run all command tests**

```bash
pdm install
bin/test/commands.bash
```

Expected: all pass. Fix any failures before continuing.

**Step 7: Commit**

```bash
git add tests/bats/commands/
git commit -m "test(bats/commands): add black-box CLI tests for all Level 0 commands"
```

---

### Task 19: BATS integration tests (adjacent pipeline pairs)

**Files:**
- Create: `tests/bats/integration/spec-model.bats`
- Create: `tests/bats/integration/spec-tokens.bats`
- Create: `tests/bats/integration/tokens-tree.bats`
- Create: `tests/bats/integration/model-lang-emit.bats`

**Step 1: Create `tests/bats/integration/spec-model.bats`**

```bash
#!/usr/bin/env bats

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    MODEL_SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/model.schema.json"
}

@test "plcc-spec | plcc-model produces valid model JSON" {
    run bash -c "plcc-spec '${FIXTURES}/trivial.plcc' | plcc-model -"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${MODEL_SCHEMA}" -
}

@test "plcc-spec | plcc-model model has correct start symbol" {
    result=$(plcc-spec "${FIXTURES}/trivial.plcc" | plcc-model -)
    echo "$result" | python -c "
import json, sys
m = json.load(sys.stdin)
assert m['start'] == 'program', f'Expected program, got {m[\"start\"]}'
"
}
```

**Step 2: Create `tests/bats/integration/spec-tokens.bats`**

```bash
#!/usr/bin/env bats

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    TOKEN_SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/token.schema.json"
    SPEC_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
}

teardown() { rm -f "${SPEC_JSON}"; }

@test "plcc-spec output feeds plcc-tokens successfully" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}'"
    [ "$status" -eq 0 ]
}

@test "spec->tokens pipeline output validates against token schema" {
    result=$(echo '42' | plcc-tokens "${SPEC_JSON}")
    echo "$result" | check-jsonschema --schemafile "${TOKEN_SCHEMA}" -
}
```

**Step 3: Create `tests/bats/integration/tokens-tree.bats`**

```bash
#!/usr/bin/env bats

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    TREE_SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/tree.schema.json"
    SPEC_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
}

teardown() { rm -f "${SPEC_JSON}"; }

@test "tokens->tree pipeline produces valid tree JSONL" {
    result=$(echo '42' | plcc-tokens "${SPEC_JSON}" | plcc-tree --spec="${SPEC_JSON}")
    echo "$result" | check-jsonschema --schemafile "${TREE_SCHEMA}" -
}

@test "lex error from tokens passes through tree unchanged" {
    result=$(echo 'xyz' | plcc-tokens "${SPEC_JSON}" | plcc-tree --spec="${SPEC_JSON}" 2>/dev/null)
    echo "$result" | python -c "import json,sys; r=json.load(sys.stdin); assert r['kind']=='error'"
}
```

**Step 4: Create `tests/bats/integration/model-lang-emit.bats`**

```bash
#!/usr/bin/env bats

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SPEC_JSON="$(mktemp)"
    OUTPUT_DIR="$(mktemp -d)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
}

teardown() {
    rm -f "${SPEC_JSON}"
    rm -rf "${OUTPUT_DIR}"
}

@test "plcc-model | plcc-lang-emit produces puml file" {
    run bash -c "plcc-model '${SPEC_JSON}' | plcc-lang-emit --target=PlantUML --output='${OUTPUT_DIR}'"
    [ "$status" -eq 0 ]
    ls "${OUTPUT_DIR}"/*.puml
}
```

**Step 5: Run all integration tests**

```bash
bin/test/integration.bash
```

Expected: all pass.

**Step 6: Commit**

```bash
git add tests/bats/integration/
git commit -m "test(bats/integration): add adjacent pipeline pair integration tests"
```

---

### Task 20: BATS e2e tests

**Files:**
- Create: `tests/bats/e2e/happy-path.bats`
- Create: `tests/bats/e2e/error-propagation.bats`

**Step 1: Create `tests/bats/e2e/happy-path.bats`**

```bash
#!/usr/bin/env bats

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SPEC_SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/spec.schema.json"
    MODEL_SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/model.schema.json"
    WORK_DIR="$(mktemp -d)"
    cd "${WORK_DIR}"
    plcc-make "${FIXTURES}/trivial.plcc"
}

teardown() {
    rm -rf "${WORK_DIR}"
}

@test "plcc-make produces build/spec.json" {
    [ -f build/spec.json ]
}

@test "build/spec.json validates against spec schema" {
    check-jsonschema --schemafile "${SPEC_SCHEMA}" build/spec.json
}

@test "plcc-make produces build/model.json" {
    [ -f build/model.json ]
}

@test "build/model.json validates against model schema" {
    check-jsonschema --schemafile "${MODEL_SCHEMA}" build/model.json
}

@test "plcc-make produces at least one .puml file in build/diagram/" {
    ls build/diagram/*.puml
}

@test "plcc-lang-list finds plantuml after install" {
    run plcc-lang-list
    [[ "$output" == *"plantuml"* ]]
}

@test "plcc-make cleans build/ on rebuild" {
    touch build/diagram/stale-marker.txt
    plcc-make "${FIXTURES}/trivial.plcc"
    [ ! -f build/diagram/stale-marker.txt ]
}
```

**Step 2: Create `tests/bats/e2e/error-propagation.bats`**

```bash
#!/usr/bin/env bats

# Tests that in-band errors pass through the pipeline without breaking it.

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SPEC_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
}

teardown() { rm -f "${SPEC_JSON}"; }

@test "lex error flows in-band through tokens->tree without crashing" {
    # 'abc' is not a valid NUM token — should produce an in-band error
    result=$(echo 'abc' | plcc-tokens "${SPEC_JSON}" | plcc-tree --spec="${SPEC_JSON}" 2>/dev/null)
    # Pipeline exit status should be 0 (error is in-band, not a tool failure)
    echo "${result}" | python -c "
import json, sys
line = sys.stdin.readline().strip()
r = json.loads(line)
assert r['kind'] == 'error', f'Expected error record, got: {r}'
print('OK: error record present in-band')
"
}

@test "lex error does not produce stderr output from pipeline" {
    stderr_out=$(echo 'abc' | plcc-tokens "${SPEC_JSON}" 2>&1 1>/dev/null)
    [ -z "${stderr_out}" ]
}
```

**Step 3: Run all e2e tests**

```bash
bin/test/e2e.bash
```

Expected: all pass.

**Step 4: Run full functional test suite**

```bash
bin/test/functional.bash
```

Expected: all pass.

**Step 5: Commit**

```bash
git add tests/bats/e2e/
git commit -m "test(bats/e2e): add end-to-end happy path and error propagation tests"
```

---

## Part 6 — CI Pipeline

### Task 21: GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`

**Step 1: Create `ci.yml`**

```yaml
name: CI

on:
  push:
    branches: [multi-lang]
  pull_request:
    branches: [multi-lang]

jobs:
  test:
    name: Functional tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - name: Run functional tests
        run: bin/test/functional.bash

  package:
    name: Packaging tests
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - name: Build package
        run: bin/build/package.bash
      - name: Run packaging tests
        run: bin/test/packaging.bash
```

**Step 2: Commit**

```bash
git add .github/
git commit -m "ci: add GitHub Actions workflow for multi-lang branch"
```

**Step 3: Push and verify CI passes**

```bash
git push -u origin multi-lang
```

Watch the Actions tab. Both `test` and `package` jobs should go green. Fix any failures before declaring Phase 1 complete.

---

## Final Verification Checklist

Run these in order before closing Phase 1:

```bash
# 1. Full functional test suite (units + commands + integration + e2e)
bin/test/functional.bash

# 2. Build and packaging test
bin/build/package.bash
bin/test/packaging.bash

# 3. Manual smoke: end-to-end with trivial grammar
plcc-make tests/fixtures/trivial.plcc
cat build/spec.json | python -m json.tool > /dev/null && echo "spec.json: valid JSON"
cat build/model.json | python -m json.tool > /dev/null && echo "model.json: valid JSON"
cat build/diagram/*.puml && echo "diagram: present"

# 4. Verify all commands on PATH
for cmd in plcc-spec plcc-tokens plcc-tree plcc-model \
           plcc-lang-emit plcc-lang-build plcc-lang-list \
           plcc-plantuml-emit plcc-make plcc-scan plcc-parse plcc-rep; do
    command -v "$cmd" && echo "OK: $cmd" || echo "MISSING: $cmd"
done

# 5. Confirm plcc-lang-list finds plantuml
plcc-lang-list | grep plantuml

# 6. CI green on multi-lang branch
```
