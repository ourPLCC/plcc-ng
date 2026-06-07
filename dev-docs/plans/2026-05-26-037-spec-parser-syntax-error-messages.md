# Issue 037: Spec Parser Syntax Error Messages — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Python stack trace from `MalformedBNFError` with a human-readable error message that identifies the file, line, column, and includes example valid syntactic rules.

**Architecture:** Give `MalformedBNFError` a `__str__` and column field; change `SyntacticParser` to catch and collect errors (returning `(spec, errors)` like the lexical parser); merge syntactic errors in `parseSpec.py`.

**Tech Stack:** Python 3, pytest, pyfakefs (already used in `plcc_spec_cli_test.py`)

---

## File Map

| File | Change |
| ---- | ------ |
| `src/plcc/spec/syntax/MalformedBNFError.py` | Add `_compute_column`, `__str__` |
| `src/plcc/spec/syntax/MalformedBNFError_test.py` | Create — unit tests for error format |
| `src/plcc/spec/syntax/parse_syntactic_spec.py` | Return `(SyntacticSpec, list)`; catch errors |
| `src/plcc/spec/syntax/parse_syntactic_spec_test.py` | Update all call sites + add new tests |
| `src/plcc/spec/parseSpec.py` | Unpack and merge syntactic errors |
| `src/plcc/spec/plcc_spec_cli_test.py` | Add end-to-end test |

---

## Task 1: Give `MalformedBNFError` a readable `__str__` and column

**Files:**

- Create: `src/plcc/spec/syntax/MalformedBNFError_test.py`
- Modify: `src/plcc/spec/syntax/MalformedBNFError.py`

- [ ] **Step 1: Write the failing tests**

Create `src/plcc/spec/syntax/MalformedBNFError_test.py`:

```python
from ...lines import Line
from .MalformedBNFError import MalformedBNFError


def make_line(string, number=0, file=""):
    return Line(string, number, file)


def test_str_first_line_is_clickable_location():
    err = MalformedBNFError(make_line("<stmt>IfStmt ::= IF", number=25, file="grammar.plcc"))
    assert str(err).startswith("grammar.plcc:25:7: syntax error")


def test_str_includes_offending_line():
    err = MalformedBNFError(make_line("<stmt>IfStmt ::= IF", number=25, file="grammar.plcc"))
    assert "<stmt>IfStmt ::= IF" in str(err)


def test_str_caret_points_to_column():
    err = MalformedBNFError(make_line("<stmt>IfStmt ::= IF", number=25, file="grammar.plcc"))
    lines = str(err).splitlines()
    caret_line = lines[2]
    assert caret_line == "      ^"


def test_str_includes_examples_header():
    err = MalformedBNFError(make_line("<stmt>IfStmt ::= IF"))
    assert "Examples:" in str(err)


def test_str_includes_all_five_example_forms():
    err = MalformedBNFError(make_line("<stmt>IfStmt ::= IF"))
    s = str(err)
    assert "<nonTerminal> ::=" in s
    assert "<nonTerminal> ::= TOKEN <TOKEN> <rhs>" in s
    assert "<nonTerminal>:ClassName ::= TOKEN <TOKEN>:field1 <rhs>:field2" in s
    assert "<nonTerminal> **= <rhs>" in s
    assert "<nonTerminal> **= <rhs> +SEPARATOR" in s


def test_column_after_matched_lhs():
    # <stmt> ends at index 5 (0-based), so first bad char is at column 7 (1-based)
    err = MalformedBNFError(make_line("<stmt>IfStmt ::= IF"))
    assert err.column == 7


def test_column_no_lhs_defaults_to_first_nonwhitespace():
    err = MalformedBNFError(make_line("stmt ::= IF"))
    assert err.column == 1


def test_column_leading_whitespace_counted():
    # two leading spaces + <stmt> (6 chars) → column 9
    err = MalformedBNFError(make_line("  <stmt>IfStmt ::= IF"))
    assert err.column == 9


def test_column_no_lhs_with_leading_whitespace():
    # two leading spaces, no LHS → column 3
    err = MalformedBNFError(make_line("  stmt ::= IF"))
    assert err.column == 3
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
bin/test/units.bash src/plcc/spec/syntax/MalformedBNFError_test.py -v
```

Expected: all 9 tests FAIL — `__str__` and `column` not yet defined.

- [ ] **Step 3: Implement `MalformedBNFError`**

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

    def __str__(self):
        caret = " " * (self.column - 1) + "^"
        return (
            f"{self.line.file}:{self.line.number}:{self.column}: syntax error\n"
            f"{self.line.string}\n"
            f"{caret}\n"
            f"{self._EXAMPLES}"
        )
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
bin/test/units.bash src/plcc/spec/syntax/MalformedBNFError_test.py -v
```

Expected: all 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/spec/syntax/MalformedBNFError.py src/plcc/spec/syntax/MalformedBNFError_test.py
git commit -m "feat: give MalformedBNFError a readable __str__ with column and examples"
```

---

## Task 2: Make `SyntacticParser` collect errors and return `(spec, errors)`

**Files:**

- Modify: `src/plcc/spec/syntax/parse_syntactic_spec.py`
- Modify: `src/plcc/spec/syntax/parse_syntactic_spec_test.py`

- [ ] **Step 1: Add new failing tests to `parse_syntactic_spec_test.py`**

Add these three tests at the bottom of `src/plcc/spec/syntax/parse_syntactic_spec_test.py` (above the helper functions):

```python
def test_malformed_bnf_returned_as_error():
    lines = [makeDivider(), makeLine("<noun> +*= WORD")]
    spec, errors = parse_syntactic_spec(lines)
    assert len(errors) == 1
    assert isinstance(errors[0], MalformedBNFError)


def test_malformed_bnf_parsing_continues_after_error():
    # valid rule after the bad one should still be collected
    lines = [makeDivider(), makeLine("<noun> +*= WORD"), makeLine("<noun> ::= WORD")]
    spec, errors = parse_syntactic_spec(lines)
    assert len(errors) == 1
    assert len(list(spec)) == 1


def test_no_errors_on_valid_spec():
    lines = [makeDivider(), makeLine("<noun> ::= WORD")]
    spec, errors = parse_syntactic_spec(lines)
    assert errors == []
```

Also **remove** the old test `test_malformed_bnf_raises` (it conflicts with the new behavior):

```python
# DELETE this test:
def test_malformed_bnf_raises():
    lines = [makeDivider(), makeLine("<noun> +*= WORD")]
    with raises(MalformedBNFError):
        parse_syntactic_spec(lines)
```

- [ ] **Step 2: Run new tests to confirm they fail**

```bash
bin/test/units.bash src/plcc/spec/syntax/parse_syntactic_spec_test.py::test_malformed_bnf_returned_as_error src/plcc/spec/syntax/parse_syntactic_spec_test.py::test_malformed_bnf_parsing_continues_after_error src/plcc/spec/syntax/parse_syntactic_spec_test.py::test_no_errors_on_valid_spec -v
```

Expected: all 3 FAIL — `parse_syntactic_spec` still raises and returns a single value.

- [ ] **Step 3: Update `parse_syntactic_spec.py`**

Replace `src/plcc/spec/syntax/parse_syntactic_spec.py` with:

```python
import re
from re import Match
from typing import List

from ...lines import Line
from .CapturingSymbol import CapturingSymbol
from .CapturingTerminal import CapturingTerminal
from .LhsNonTerminal import LhsNonTerminal
from .MalformedBNFError import MalformedBNFError
from .RepeatingSyntacticRule import RepeatingSyntacticRule
from .RhsNonTerminal import RhsNonTerminal
from .StandardSyntacticRule import StandardSyntacticRule
from .Symbol import Symbol
from .SyntacticRule import SyntacticRule
from .SyntacticSpec import SyntacticSpec
from .Terminal import Terminal


def parse_syntactic_spec(dividerAndLines):
    return SyntacticParser(dividerAndLines).parseSpec()


class SyntacticParser:
    def __init__(self, dividerAndLines):
        self._spec = SyntacticSpec()
        self._dividerAndLines = dividerAndLines
        self._errors = []

    def parseSpec(self) -> tuple[SyntacticSpec, list]:
        if not self._dividerAndLines:
            return self._spec, []
        lines = self._removeStartingDivider(self._dividerAndLines)
        for line in lines:
            self._parseLine(line)
        return self._spec, self._errors

    def _removeStartingDivider(self, lines):
        lines = self._dividerAndLines
        if not isinstance(lines[0], Line):
            lines = lines[1:]
        return lines

    def _parseLine(self, line):
        parser = SyntacticLineParser(line)
        if parser.isSyntacticRule():
            try:
                rule = parser.parseSyntacticRule()
                self._spec.append(rule)
            except MalformedBNFError as e:
                self._errors.append(e)


class SyntacticLineParser:
    def __init__(self, line: Line):
        self.line = line
        self.lhs = None
        self.rhs = None
        self.separator = None

    def parseSyntacticRule(self) -> SyntacticRule:
        standard, separated, repeating = self._buildMatches()
        if standard:
            return self._parseStandardRule(standard)
        elif separated:
            return self._parseSeparatedRule(separated)
        elif repeating:
            return self._parseRepeatingRule(repeating)
        raise MalformedBNFError(self.line)

    def _parseStandardRule(self, standard: Match[str]) -> StandardSyntacticRule:
        self.lhs, self.rhs = standard["lhs"], standard["rhs"]
        return StandardSyntacticRule(self.line, self._parseLeft(), self._parseRight())

    def _parseLeft(self) -> LhsNonTerminal:
        match = self._matchLeft()
        return LhsNonTerminal(match["nonTerminal"], match["altName"])

    def _parseRight(self) -> List[Symbol]:
        if self.rhs is None:
            return []
        return [
            self._parseSymbol(symbol)
                for symbol in self.rhs.split()
                    if symbol and not symbol.startswith("#")
        ]

    def _parseSymbol(self, symbol: str) -> Symbol:
        capturing = re.match(r"<(?P<name>\S*)>(?P<altName>\S+)?", symbol)
        return (
            self._parseCapturing(capturing["name"], capturing["altName"])
            if capturing
            else Terminal(symbol)
        )

    def _parseCapturing(self, name: str, altName: str) -> CapturingSymbol:
        terminal = re.fullmatch(r"[A-Z_][A-Z0-9_]*", name)
        altName = altName.strip(":") if altName is not None else altName
        return (
            CapturingTerminal(name=name, altName=altName)
            if terminal
            else RhsNonTerminal(name, altName)
        )

    def _buildMatches(
        self,
    ) -> tuple[Match[str] | None, Match[str] | None, Match[str] | None]:
        lineStr = self.line.string.split("#")[0].strip()
        standard = re.match(
            r"^\s*(?P<lhs><\S+>(?::\S+)?)\s*::=(?:\s(?P<rhs>.*))?", lineStr
        )
        separated = re.match(
            r"^\s*(?P<lhs><\S+>(?::\S+)?)\s*\*\*=\s(?P<rhs>.*)(?P<separator>\+.*)",
            lineStr,
        )
        repeating = re.match(
            r"^\s*(?P<lhs><\S+>(?::\S+)?)\s*\*\*=\s(?P<rhs>.*)", lineStr
        )
        return standard, separated, repeating

    def _parseSeparatedRule(self, separated: Match[str]) -> RepeatingSyntacticRule:
        self.lhs, self.rhs, self.separator = (
            separated["lhs"],
            separated["rhs"],
            separated["separator"].strip("+").strip(" "),
        )
        return self._parseRepeating()

    def _parseRepeatingRule(self, repeating: Match[str]) -> RepeatingSyntacticRule:
        self.lhs, self.rhs = repeating["lhs"], repeating["rhs"]
        return self._parseRepeating()

    def _parseRepeating(self) -> RepeatingSyntacticRule:
        return RepeatingSyntacticRule(
            self.line,
            self._parseLeft(),
            self._parseRight(),
            Terminal(self.separator) if self.separator else None,
        )

    def _matchLeft(self) -> Match[str] | None:
        return re.match(r"<(?P<nonTerminal>\S*)>(?::(?P<altName>\S+))?\s*", self.lhs)

    def isSyntacticRule(self) -> bool:
        return re.match(
            r"^\s*$", self.line.string
        ) is None and not self.line.string.startswith("#")
```

- [ ] **Step 4: Run the new tests to confirm they pass**

```bash
bin/test/units.bash src/plcc/spec/syntax/parse_syntactic_spec_test.py::test_malformed_bnf_returned_as_error src/plcc/spec/syntax/parse_syntactic_spec_test.py::test_malformed_bnf_parsing_continues_after_error src/plcc/spec/syntax/parse_syntactic_spec_test.py::test_no_errors_on_valid_spec -v
```

Expected: all 3 PASS.

- [ ] **Step 5: Run the full test file — expect failures on the old tests**

```bash
bin/test/units.bash src/plcc/spec/syntax/parse_syntactic_spec_test.py -v
```

Expected: the 3 new tests PASS; the ~30 existing tests FAIL because they do `list(parse_syntactic_spec(lines))` which now returns `[SyntacticSpec, []]` instead of the rules.

- [ ] **Step 6: Update all existing call sites in `parse_syntactic_spec_test.py`**

Every existing test that calls `parse_syntactic_spec` uses this pattern:

```python
# Before
assert list(parse_syntactic_spec(lines)) == expected

# After
spec, errors = parse_syntactic_spec(lines)
assert list(spec) == expected
```

And for the two tests that check for empty results:

```python
# Before
assert list(parse_syntactic_spec(None)) == []
assert list(parse_syntactic_spec([])) == []

# After
spec, errors = parse_syntactic_spec(None)
assert list(spec) == []
spec, errors = parse_syntactic_spec([])
assert list(spec) == []
```

Apply this substitution to every test in the file (all tests except the three new ones added in Step 1). The helper functions at the bottom of the file (`makeDivider`, `makeLine`, etc.) do not change.

Also fix two additional call sites in other test files:

`src/plcc/spec/syntax/validations/validate_rhs_test.py` line 121:

```python
# Before
spec = parse_syntactic_spec(rough_)

# After
spec, _ = parse_syntactic_spec(rough_)
```

`src/plcc/spec/syntax/validations/ll1/build_spec_grammar_test.py` line 93:

```python
# Before
syntacticSpec = parse_syntactic_spec([makeDivider()] + [makeLine(line) for line in lines])

# After
syntacticSpec, _ = parse_syntactic_spec([makeDivider()] + [makeLine(line) for line in lines])
```

Note: line 90 of `build_spec_grammar_test.py` already uses `[0]` indexing (`parse_syntactic_spec(...)[0]`) — this still works on a tuple (returns the spec), so no change needed there.

- [ ] **Step 7: Run the full test file — all should pass**

```bash
bin/test/units.bash src/plcc/spec/syntax/parse_syntactic_spec_test.py -v
```

Expected: all tests PASS.

- [ ] **Step 8: Commit**

```bash
git add src/plcc/spec/syntax/parse_syntactic_spec.py src/plcc/spec/syntax/parse_syntactic_spec_test.py
git commit -m "feat: SyntacticParser collects MalformedBNFError instead of raising"
```

---

## Task 3: Merge syntactic errors in `parseSpec.py` and add CLI test

**Files:**

- Modify: `src/plcc/spec/parseSpec.py`
- Modify: `src/plcc/spec/plcc_spec_cli_test.py`

- [ ] **Step 1: Write the failing CLI test**

Add to `src/plcc/spec/plcc_spec_cli_test.py`:

```python
def test_malformed_syntactic_rule_prints_error_and_exits_nonzero(capsys, fs):
    fs.create_file('/bad.plcc', contents=(
        "token NUM '\\d+'\n"
        "%\n"
        "<program>IfStmt ::= NUM\n"
    ))
    with pytest.raises(SystemExit) as exc:
        run_main(['/bad.plcc'])
    out, err = capsys.readouterr()
    assert exc.value.code != 0
    assert "bad.plcc" in err
    assert "syntax error" in err
    assert "Examples:" in err
```

- [ ] **Step 2: Run the test to confirm it fails**

```bash
bin/test/units.bash src/plcc/spec/plcc_spec_cli_test.py::test_malformed_syntactic_rule_prints_error_and_exits_nonzero -v
```

Expected: FAIL — the error currently produces a stack trace instead of the structured message (or the error is not caught and propagates as an uncaught exception).

- [ ] **Step 3: Update `parseSpec.py` to merge syntactic errors**

Replace `src/plcc/spec/parseSpec.py` with:

```python
from .Spec import Spec
from .split_rough import split_rough
from . import lexical, rough, semantics, syntax


def parseSpec(string, file=None, startLineNumber=1):
    rough_, errors = rough.parseRough(string, file, startLineNumber)
    rough_ = iter(rough_)
    rough_lex, rough_syn, rough_sems = split_rough(rough_)
    lex_, errors = lexical.parseLexicalSpec(rough_lex)
    syn_, syn_errors = syntax.parse_syntactic_spec(rough_syn)
    errors = errors + syn_errors
    sems_ = [semantics.parse_semantic_spec(rs) for rs in rough_sems]
    return Spec(lexical=lex_, syntax=syn_, semantics=sems_), errors
```

- [ ] **Step 4: Run the CLI test to confirm it passes**

```bash
bin/test/units.bash src/plcc/spec/plcc_spec_cli_test.py::test_malformed_syntactic_rule_prints_error_and_exits_nonzero -v
```

Expected: PASS.

- [ ] **Step 5: Run all tests**

```bash
bin/test/units.bash -v
```

Expected: all 781+ tests PASS. Zero failures.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/spec/parseSpec.py src/plcc/spec/plcc_spec_cli_test.py
git commit -m "fix: surface MalformedBNFError as human-readable message in plcc-spec output"
```
