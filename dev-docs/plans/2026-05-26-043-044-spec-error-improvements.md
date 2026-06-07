# Spec Error Improvements (Issues 043 and 044) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix two spec error bugs: (043) `parseSpec` drops rough-phase errors by shadowing the `errors` variable; (044) spec errors appear corrupted when piped through the verbose event layer because `plcc-spec` writes multi-line human text instead of structured events.

**Architecture:** Issue 043 is a one-line variable rename. Issue 044 extends `VerboseContext.emit_error` and `reformat_child_events` to render `source_line`/`hint` fields in text mode, adds `kind`/`hint` properties to the spec error base classes, and updates `plcc_spec_cli.py` to call `emit_error` instead of printing directly.

**Tech Stack:** Python, pytest, bats

---

## File Map

| File | Change |
| --- | --- |
| `src/plcc/spec/parseSpec.py` | Rename shadowed `errors` variable (043) |
| `src/plcc/spec/parseSpec_test.py` | New test: rough errors not dropped |
| `src/plcc/spec/SpecError.py` | Add `kind` and `hint` properties |
| `src/plcc/spec/SpecError_test.py` | New file: tests for `kind` and `hint` |
| `src/plcc/spec/syntax/MalformedBNFError.py` | Add `kind` and `hint` properties |
| `src/plcc/spec/syntax/MalformedBNFError_test.py` | New tests for `kind` and `hint` |
| `src/plcc/verbose.py` | Render `source_line`/`hint` in `emit_error` and `reformat_child_events` text mode |
| `src/plcc/verbose_test.py` | New tests for rich error rendering |
| `src/plcc/spec/plcc_spec_cli.py` | Use `verbose.emit_error` instead of `print` |
| `src/plcc/spec/plcc_spec_cli_test.py` | New tests for structured error output |
| `tests/bats/commands/plcc-spec.bats` | New test: caret and source line appear in stderr |

---

## Task 1: Fix 043 — variable shadowing in parseSpec

**Files:**

- Modify: `src/plcc/spec/parseSpec.py`
- Modify: `src/plcc/spec/parseSpec_test.py`

- [ ] **Step 1: Write the failing test**

The file currently starts with:

```python
from .parseSpec import parseSpec
```

Add the new import and test so the file becomes:

```python
from .parseSpec import parseSpec
from .rough.UnclosedBlockError import UnclosedBlockError


def test_rough_errors_are_returned():
    # An unclosed %%% block triggers UnclosedBlockError at rough-parse time.
    # Before the fix, the errors variable was overwritten and rough errors dropped.
    _, errors = parseSpec("token NUM '\\d+'\n%%%\nunclosed block\n")
    assert any(isinstance(e, UnclosedBlockError) for e in errors)
```

Keep all existing tests in the file unchanged.

- [ ] **Step 2: Run test to verify it fails**

```bash
bin/test/units.bash src/plcc/spec/parseSpec_test.py::test_rough_errors_are_returned -v
```

Expected: FAIL — the error list is empty because rough errors are dropped.

- [ ] **Step 3: Fix the variable shadowing**

Replace `src/plcc/spec/parseSpec.py` with:

```python
from .Spec import Spec
from .split_rough import split_rough
from . import lexical, rough, semantics, syntax


def parseSpec(string, file=None, startLineNumber=1):
    rough_, rough_errors = rough.parseRough(string, file, startLineNumber)
    rough_ = iter(rough_)
    rough_lex, rough_syn, rough_sems = split_rough(rough_)
    lex_, lex_errors = lexical.parseLexicalSpec(rough_lex)
    syn_, syn_errors = syntax.parse_syntactic_spec(rough_syn)
    sems_ = [semantics.parse_semantic_spec(rs) for rs in rough_sems]
    return Spec(lexical=lex_, syntax=syn_, semantics=sems_), rough_errors + lex_errors + syn_errors
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
bin/test/units.bash src/plcc/spec/parseSpec_test.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/spec/parseSpec.py src/plcc/spec/parseSpec_test.py
git commit -m "fix: stop dropping rough-parse errors in parseSpec (closes 043)"
```

---

## Task 2: Add `kind` and `hint` to `SpecError`

**Files:**

- Modify: `src/plcc/spec/SpecError.py`
- Create: `src/plcc/spec/SpecError_test.py`

- [ ] **Step 1: Write the failing tests**

Create `src/plcc/spec/SpecError_test.py`:

```python
from ..lines import Line
from .SpecError import SpecError


def _line(string='test line', number=1, file='test.plcc'):
    return Line(string=string, number=number, file=file)


def test_kind_returns_message_when_set():
    err = SpecError(line=_line(), message="pattern is invalid", column=1)
    assert err.kind == "pattern is invalid"


def test_kind_returns_class_name_when_message_is_none():
    err = SpecError(line=_line(), column=1)
    assert err.kind == "SpecError"


def test_hint_returns_none():
    err = SpecError(line=_line(), message="anything", column=1)
    assert err.hint is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
bin/test/units.bash src/plcc/spec/SpecError_test.py -v
```

Expected: FAIL — `SpecError` has no `kind` or `hint` attribute.

- [ ] **Step 3: Add properties to `SpecError`**

Replace `src/plcc/spec/SpecError.py` with:

```python
from .ValidationError import ValidationError


class SpecError(ValidationError):
    def __init__(self, line=None, message=None, column=None, index=None):
        self.column = column if column is not None else index + 1
        ValidationError.__init__(self, line=line, message=message)

    @property
    def kind(self):
        return self.message or type(self).__name__

    @property
    def hint(self):
        return None

    def __str__(self):
        m = f'\n{self.message}' if self.message else ''
        return f'''{self.__class__.__name__}: {self.line.file}:{self.line.number}:{self.column}\n{self.line.string}\n{' '*(self.column-1)}^{m}\n'''
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
bin/test/units.bash src/plcc/spec/SpecError_test.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/spec/SpecError.py src/plcc/spec/SpecError_test.py
git commit -m "feat: add kind and hint properties to SpecError"
```

---

## Task 3: Add `kind` and `hint` to `MalformedBNFError`

**Files:**

- Modify: `src/plcc/spec/syntax/MalformedBNFError.py`
- Modify: `src/plcc/spec/syntax/MalformedBNFError_test.py`

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/spec/syntax/MalformedBNFError_test.py`:

```python
def test_kind_returns_syntax_error():
    err = MalformedBNFError(make_line("<stmt>IfStmt ::= IF"))
    assert err.kind == "syntax error"


def test_hint_returns_examples():
    err = MalformedBNFError(make_line("<stmt>IfStmt ::= IF"))
    assert err.hint == MalformedBNFError._EXAMPLES
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
bin/test/units.bash src/plcc/spec/syntax/MalformedBNFError_test.py::test_kind_returns_syntax_error src/plcc/spec/syntax/MalformedBNFError_test.py::test_hint_returns_examples -v
```

Expected: FAIL — `MalformedBNFError` has no `kind` or `hint` attribute.

- [ ] **Step 3: Add properties to `MalformedBNFError`**

Replace `src/plcc/spec/syntax/MalformedBNFError.py` with:

```python
import re


class MalformedBNFError(Exception):
    _EXAMPLES = (
        "Examples:\n"
        "  <nonTerminal> ::=\n"
        "  <nonTerminal> ::= TOKEN <TOKEN> <rhs>\n"
        "  <nonTerminal>:ClassName ::= TOKEN <TOKEN>:field1 <rhs>:field2\n"
        "  <nonTerminal> **= <rhs>\n"
        "  <nonTerminal> **= <rhs> +SEPARATOR"
    )

    def __init__(self, line):
        self.line = line
        self.column = self._compute_column()

    def _compute_column(self):
        original = self.line.string
        leading = len(original) - len(original.lstrip())
        lhs_match = re.match(r"<\S+>(?::\S+)?", original.lstrip())
        if lhs_match:
            return leading + lhs_match.end() + 1
        return leading + 1

    @property
    def kind(self):
        return "syntax error"

    @property
    def hint(self):
        return self._EXAMPLES

    def __str__(self):
        caret = " " * (self.column - 1) + "^"
        return (
            f"{self.line.file}:{self.line.number}:{self.column}: syntax error\n"
            f"{self.line.string}\n"
            f"{caret}\n"
            f"{self._EXAMPLES}"
        )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
bin/test/units.bash src/plcc/spec/syntax/MalformedBNFError_test.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/spec/syntax/MalformedBNFError.py src/plcc/spec/syntax/MalformedBNFError_test.py
git commit -m "feat: add kind and hint properties to MalformedBNFError"
```

---

## Task 4: Extend `verbose.emit_error` and `reformat_child_events` with rich rendering

**Files:**

- Modify: `src/plcc/verbose.py`
- Modify: `src/plcc/verbose_test.py`

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/verbose_test.py`:

```python
def test_emit_error_text_mode_with_source_line_and_hint(capsys):
    ctx = VerboseContext("plcc-spec", SampleEvents, level=0, fmt="text")
    ctx.emit_error(
        {"file": "g.plcc", "line": 3, "column": 7},
        "syntax error",
        source_line="<stmt>Assign ::= IDENT",
        hint="Examples:\n  <x> ::=",
    )
    _, err = capsys.readouterr()
    lines = err.splitlines()
    assert lines[0] == "plcc-spec: g.plcc:3:7: error: syntax error"
    assert lines[1] == "<stmt>Assign ::= IDENT"
    assert lines[2] == "      ^"
    assert "Examples:" in err


def test_emit_error_text_mode_without_source_line_unchanged(capsys):
    ctx = VerboseContext("plcc-spec", SampleEvents, level=0, fmt="text")
    ctx.emit_error({"file": "g.plcc", "line": 3, "column": 7}, "something failed")
    _, err = capsys.readouterr()
    assert err.strip() == "plcc-spec: g.plcc:3:7: error: something failed"


def test_emit_error_json_mode_includes_source_line_and_hint(capsys):
    ctx = VerboseContext("plcc-spec", SampleEvents, level=0, fmt="json")
    ctx.emit_error(
        {"file": "g.plcc", "line": 3, "column": 7},
        "syntax error",
        source_line="<stmt>Assign ::= IDENT",
        hint="Examples:\n  <x> ::=",
    )
    _, err = capsys.readouterr()
    record = json.loads(err.strip())
    assert record["source_line"] == "<stmt>Assign ::= IDENT"
    assert record["hint"] == "Examples:\n  <x> ::="


def test_reformat_child_events_renders_source_line_and_hint(capsys):
    ctx = VerboseContext("parent", SampleEvents, level=0, fmt="text")
    event = {
        "stage": "plcc-spec",
        "event": "error",
        "pos": {"file": "g.plcc", "line": 3, "column": 7},
        "message": "syntax error",
        "source_line": "<stmt>Assign ::= IDENT",
        "hint": "Examples:\n  <x> ::=",
    }
    ctx.reformat_child_events([event])
    _, err = capsys.readouterr()
    lines = err.splitlines()
    assert lines[0] == "plcc-spec: g.plcc:3:7: error: syntax error"
    assert lines[1] == "<stmt>Assign ::= IDENT"
    assert lines[2] == "      ^"
    assert "Examples:" in err


def test_reformat_child_events_without_source_line_unchanged(capsys):
    ctx = VerboseContext("parent", SampleEvents, level=0, fmt="text")
    event = {
        "stage": "plcc-spec",
        "event": "error",
        "pos": {"file": "g.plcc", "line": 3, "column": 7},
        "message": "something failed",
    }
    ctx.reformat_child_events([event])
    _, err = capsys.readouterr()
    assert err.strip() == "plcc-spec: g.plcc:3:7: error: something failed"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
bin/test/units.bash src/plcc/verbose_test.py::test_emit_error_text_mode_with_source_line_and_hint src/plcc/verbose_test.py::test_reformat_child_events_renders_source_line_and_hint -v
```

Expected: FAIL.

- [ ] **Step 3: Extend `emit_error` text mode in `verbose.py`**

Replace the `else` branch of `emit_error` (lines 62–70 in `src/plcc/verbose.py`) with:

```python
    else:
        filename = pos.get("file") or "<stdin>"
        line = pos.get("line", 0)
        col = pos.get("column", 0)
        parts = [f"{self.stage}: {filename}:{line}:{col}: error: {message}"]
        source_line = fields.get("source_line")
        hint = fields.get("hint")
        if source_line is not None:
            parts.append(source_line)
            if col > 0:
                parts.append(" " * (col - 1) + "^")
        if hint is not None:
            parts.append(hint)
        print("\n".join(parts), file=sys.stderr, flush=True)
```

- [ ] **Step 4: Extend `reformat_child_events` in `verbose.py`**

Replace the `if ev.get("event") == "error":` block inside `reformat_child_events` (lines 96–104) with:

```python
            if ev.get("event") == "error":
                stage = ev.get("stage", "unknown")
                pos = ev.get("pos", {}) or {}
                file = pos.get("file") or "<stdin>"
                line = pos.get("line", 0)
                col = pos.get("column", 0)
                msg = ev.get("message", "")
                parts = [f"{stage}: {file}:{line}:{col}: error: {msg}"]
                source_line = ev.get("source_line")
                hint = ev.get("hint")
                if source_line is not None:
                    parts.append(source_line)
                    if col > 0:
                        parts.append(" " * (col - 1) + "^")
                if hint is not None:
                    parts.append(hint)
                print("\n".join(parts), file=sys.stderr, flush=True)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
bin/test/units.bash src/plcc/verbose_test.py -v
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/verbose.py src/plcc/verbose_test.py
git commit -m "feat: render source_line and hint in emit_error and reformat_child_events text mode"
```

---

## Task 5: Update `plcc_spec_cli.py` to use `emit_error`

**Files:**

- Modify: `src/plcc/spec/plcc_spec_cli.py`
- Modify: `src/plcc/spec/plcc_spec_cli_test.py`

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/spec/plcc_spec_cli_test.py`:

```python
def test_malformed_syntactic_rule_stderr_includes_source_line(capsys, fs):
    fs.create_file('/bad.plcc', contents=(
        "token NUM '\\d+'\n"
        "%\n"
        "<program>IfStmt ::= NUM\n"
    ))
    with pytest.raises(SystemExit):
        run_main(['/bad.plcc'])
    _, err = capsys.readouterr()
    assert "<program>IfStmt ::= NUM" in err


def test_malformed_syntactic_rule_stderr_includes_caret_at_correct_column(capsys, fs):
    # <program> is 9 chars, so lhs ends at index 8 (0-based), column 10 (1-based).
    # Caret line must be 9 spaces + ^.
    fs.create_file('/bad.plcc', contents=(
        "token NUM '\\d+'\n"
        "%\n"
        "<program>IfStmt ::= NUM\n"
    ))
    with pytest.raises(SystemExit):
        run_main(['/bad.plcc'])
    _, err = capsys.readouterr()
    assert "         ^" in err


def test_lexical_error_stderr_includes_source_line(capsys, fs):
    # "num 'bad'" is invalid (lowercase token name triggers NameExpected)
    fs.create_file('/bad.plcc', contents="num 'bad'\n")
    with pytest.raises(SystemExit):
        run_main(['/bad.plcc'])
    _, err = capsys.readouterr()
    assert "num 'bad'" in err
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
bin/test/units.bash src/plcc/spec/plcc_spec_cli_test.py::test_malformed_syntactic_rule_stderr_includes_source_line src/plcc/spec/plcc_spec_cli_test.py::test_malformed_syntactic_rule_stderr_includes_caret_at_correct_column src/plcc/spec/plcc_spec_cli_test.py::test_lexical_error_stderr_includes_source_line -v
```

Expected: FAIL — stderr contains the old format without source line in a way that matches or doesn't, but specifically the caret position test will fail.

- [ ] **Step 3: Update `plcc_spec_cli.py`**

Replace `src/plcc/spec/plcc_spec_cli.py` with:

```python
import enum
import json
import sys
from dataclasses import asdict

from docopt import docopt

from . import parseSpec
from ..verbose import VerboseContext, VERBOSE_OPTIONS

# No LL(1) analysis here; see plcc-ll1.
__doc__ = """plcc-spec
    Parse, validate, and print a PLCC grammar file as JSON.

Usage:
    plcc-spec [-v ...] [options] FILE

Arguments:
    FILE    PLCC grammar file. Use - to read from stdin.

Options:
    --no-json       Do not print JSON to stdout.
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-spec", Events, args)
    spec, errors = _load(args['FILE'])
    if errors:
        for e in errors:
            pos = {"file": e.line.file, "line": e.line.number, "column": e.column}
            kwargs = {"source_line": e.line.string}
            if e.hint:
                kwargs["hint"] = e.hint
            verbose.emit_error(pos, e.kind, **kwargs)
        sys.exit(1)
    if not args['--no-json']:
        print(json.dumps(asdict(spec), indent=2))


def _load(path):
    if path == '-':
        return parseSpec(sys.stdin.read(), '-')
    with open(path) as f:
        return parseSpec(f.read(), path)
```

- [ ] **Step 4: Run all spec CLI tests**

```bash
bin/test/units.bash src/plcc/spec/plcc_spec_cli_test.py -v
```

Expected: all PASS.

- [ ] **Step 5: Run full unit suite to catch regressions**

```bash
bin/test/units.bash
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/spec/plcc_spec_cli.py src/plcc/spec/plcc_spec_cli_test.py
git commit -m "fix: route plcc-spec errors through verbose.emit_error with source line and caret (closes 044)"
```

---

## Task 6: Bats integration test for end-to-end caret rendering

**Files:**

- Modify: `tests/bats/commands/plcc-spec.bats`

- [ ] **Step 1: Add the test**

Add to `tests/bats/commands/plcc-spec.bats`:

```bash
@test "plcc-spec malformed syntactic rule: stderr includes source line and caret" {
    printf "token NUM '\\\\d+'\n%%\n<program>IfStmt ::= NUM\n" > "${BAD_SPEC}"
    run --separate-stderr plcc-spec "${BAD_SPEC}"
    [ "$status" -ne 0 ]
    [[ "$stderr" == *"<program>IfStmt ::= NUM"* ]]
    [[ "$stderr" == *"         ^"* ]]
}
```

Note: `<program>` is 9 characters so the caret is preceded by 9 spaces (column 10).

- [ ] **Step 2: Run the commands test suite**

```bash
bin/test/commands.bash
```

Expected: all PASS including the new test.

- [ ] **Step 3: Commit**

```bash
git add tests/bats/commands/plcc-spec.bats
git commit -m "test: add bats test for plcc-spec caret alignment in error output"
```

---

## Task 7: Final check

- [ ] **Run the full functional test suite**

```bash
bin/test/functional.bash
```

Expected: all PASS.
