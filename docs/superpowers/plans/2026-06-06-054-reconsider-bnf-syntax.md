# Reconsider BNF Syntax Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Change the BNF section syntax so that `:name` annotations move inside angle brackets and nonterminal names are required to be PascalCase.

**Architecture:** Parser regexes change first (gate on which all other tests depend), then validation is updated to use a new shared `class_name` utility, then build_model drops its now-redundant capitalize transforms, then fixtures and tests are updated throughout.

**Tech Stack:** Python, pytest, bats. All test runners are in `bin/test/`. TDD inner loop: `bin/test/units.bash`. Run `bin/test/e2e.bash` after fixtures are updated.

---

## File Map

| Action | File |
|--------|------|
| Create | `src/plcc/spec/syntax/validations/class_name.py` |
| Create | `src/plcc/spec/syntax/validations/class_name_test.py` |
| Modify | `src/plcc/spec/syntax/parse_syntactic_spec.py` |
| Modify | `src/plcc/spec/syntax/parse_syntactic_spec_test.py` |
| Modify | `src/plcc/spec/syntax/MalformedBNFError.py` |
| Modify | `src/plcc/spec/syntax/MalformedBNFError_test.py` |
| Modify | `src/plcc/spec/syntax/validations/validate_lhs.py` |
| Modify | `src/plcc/spec/syntax/validations/validate_lhs_test.py` |
| Modify | `src/plcc/spec/syntax/validations/validate_rhs.py` |
| Modify | `src/plcc/spec/syntax/validations/validate_rhs_test.py` |
| Modify | `src/plcc/model/build_model.py` |
| Modify | `src/plcc/model/build_model_test.py` |
| Modify | `src/plcc/spec/syntax/validations/replace_repeating_with_standard_rules.py` |
| Modify | `src/plcc/spec/syntax/validations/replace_repeating_with_standard_rules_test.py` |
| Modify | `src/plcc/spec/syntax/validations/validate_syntactic_spec_test.py` |
| Modify | `tests/fixtures/arith.plcc` |
| Modify | `tests/fixtures/trivial.plcc` |
| Modify | `tests/fixtures/trivial-full.plcc` |
| Modify | `tests/fixtures/trivial-java.plcc` |
| Modify | `tests/fixtures/trivial-python.plcc` |
| Modify | `tests/fixtures/trivial-arbno.plcc` |

---

## Task 1: Shared class-name utility

**Files:**
- Create: `src/plcc/spec/syntax/validations/class_name.py`
- Create: `src/plcc/spec/syntax/validations/class_name_test.py`

- [ ] **Step 1: Write the failing tests**

Create `src/plcc/spec/syntax/validations/class_name_test.py`:

```python
from .class_name import is_valid_class_name


def test_single_uppercase_letter_is_valid():
    assert is_valid_class_name("E")

def test_pascal_case_is_valid():
    assert is_valid_class_name("Expr")

def test_pascal_case_with_digits_is_valid():
    assert is_valid_class_name("ExprRest123")

def test_pascal_case_with_underscore_is_valid():
    assert is_valid_class_name("Expr_Rest")

def test_lowercase_is_invalid():
    assert not is_valid_class_name("expr")

def test_starts_with_underscore_is_invalid():
    assert not is_valid_class_name("_Expr")

def test_starts_with_digit_is_invalid():
    assert not is_valid_class_name("1Expr")

def test_contains_colon_is_invalid():
    assert not is_valid_class_name("E:name")

def test_empty_string_is_invalid():
    assert not is_valid_class_name("")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
bin/test/units.bash src/plcc/spec/syntax/validations/class_name_test.py -v
```

Expected: ImportError — `class_name` module does not exist yet.

- [ ] **Step 3: Implement `class_name.py`**

Create `src/plcc/spec/syntax/validations/class_name.py`:

```python
import re

CLASS_NAME_RE = re.compile(r"^[A-Z][a-zA-Z0-9_]*$")


def is_valid_class_name(name: str) -> bool:
    return bool(CLASS_NAME_RE.match(name))
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
bin/test/units.bash src/plcc/spec/syntax/validations/class_name_test.py -v
```

Expected: All 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
git -C .worktrees/054-reconsider-bnf-syntax add \
  src/plcc/spec/syntax/validations/class_name.py \
  src/plcc/spec/syntax/validations/class_name_test.py
git -C .worktrees/054-reconsider-bnf-syntax commit -m "feat(syntax): add shared is_valid_class_name utility"
```

---

## Task 2: Update parser to move `:name` inside angle brackets

**Files:**
- Modify: `src/plcc/spec/syntax/parse_syntactic_spec.py`
- Modify: `src/plcc/spec/syntax/parse_syntactic_spec_test.py`

- [ ] **Step 1: Add failing tests for new syntax**

Add these tests to `src/plcc/spec/syntax/parse_syntactic_spec_test.py` (after the existing tests, before the helper functions):

```python
def test_lhs_altname_inside_brackets():
    line = makeLine("<noun:Name> ::= WORD")
    lines = [makeDivider(), line]
    expected = [makeStandardSyntacticRule(line, makeLhsNonTerminal("noun", "Name"), [makeTerminal("WORD")])]
    spec, _ = parse_syntactic_spec(lines)
    assert list(spec) == expected


def test_rhs_field_inside_brackets():
    line = makeLine("<noun> ::= <word:hello>")
    lines = [makeDivider(), line]
    expected = [makeStandardSyntacticRule(line, makeLhsNonTerminal("noun"), [makeRhsNonTerminal("word", "hello")])]
    spec, _ = parse_syntactic_spec(lines)
    assert list(spec) == expected


def test_rhs_terminal_field_inside_brackets():
    line = makeLine("<noun> ::= <A:b>")
    lines = [makeDivider(), line]
    expected = [makeStandardSyntacticRule(line, makeLhsNonTerminal("noun"), [makeCapturingTerminal("A", "b")])]
    spec, _ = parse_syntactic_spec(lines)
    assert list(spec) == expected


def test_old_lhs_altname_outside_brackets_is_error():
    line = makeLine("<noun>:Name ::= WORD")
    spec, errors = parse_syntactic_spec([makeDivider(), line])
    assert len(errors) == 1
    assert isinstance(errors[0], MalformedBNFError)


def test_old_rhs_field_outside_brackets_is_error():
    line = makeLine("<noun> ::= <word>:hello")
    spec, errors = parse_syntactic_spec([makeDivider(), line])
    assert len(errors) == 1
    assert isinstance(errors[0], MalformedBNFError)
```

- [ ] **Step 2: Run new tests to verify they fail**

```bash
bin/test/units.bash src/plcc/spec/syntax/parse_syntactic_spec_test.py::test_lhs_altname_inside_brackets src/plcc/spec/syntax/parse_syntactic_spec_test.py::test_rhs_field_inside_brackets src/plcc/spec/syntax/parse_syntactic_spec_test.py::test_rhs_terminal_field_inside_brackets -v
```

Expected: FAIL — old parser puts the colon outside, so assertions on `altName` fail.

- [ ] **Step 3: Update the three regexes in `parse_syntactic_spec.py`**

In `src/plcc/spec/syntax/parse_syntactic_spec.py`, make these three changes:

**`_buildMatches` (line ~107)** — change the `lhs` capture group in all three patterns from `<\S+>(?::\S+)?` to `<[^>]+>`:

```python
standard = re.match(
    r"^\s*(?P<lhs><[^>]+>)\s*::=(?:\s(?P<rhs>.*))?", lineStr
)
separated = re.match(
    r"^\s*(?P<lhs><[^>]+>)\s*\*\*=\s(?P<rhs>.*)(?P<separator>\+.*)",
    lineStr,
)
repeating = re.match(
    r"^\s*(?P<lhs><[^>]+>)\s*\*\*=\s(?P<rhs>.*)", lineStr
)
```

**`_matchLeft` (line ~140)** — change to parse `name` and optional `:altName` from inside `<>`:

```python
def _matchLeft(self) -> Match[str] | None:
    return re.match(r"<(?P<nonTerminal>[^:>]+)(?::(?P<altName>[^>]+))?>\s*", self.lhs)
```

**`_parseSymbol` (line ~88)** — change the fullmatch to expect `:altName` inside `<>`:

```python
def _parseSymbol(self, symbol: str) -> Symbol:
    capturing = re.fullmatch(r"<(?P<name>[^:>]+)(?::(?P<altName>[^>]+))?>", symbol)
    if capturing:
        return self._parseCapturing(capturing["name"], capturing["altName"])
    if symbol.startswith("<"):
        raise MalformedBNFError(self.line)
    return Terminal(symbol)
```

- [ ] **Step 4: Run all parser tests to see which old ones now fail**

```bash
bin/test/units.bash src/plcc/spec/syntax/parse_syntactic_spec_test.py -v
```

Expected: New tests PASS. Three old tests fail because they use old outside-colon syntax:
- `test_named_lhs_non_terminal` (uses `<noun>:Name ::= WORD`)
- `test_single_char_capturing_terminal_with_altname` (uses `<noun> ::= <A>:b`)
- `test_colon_rhs_non_terminal` (uses `<noun> ::= WORD WORD <word>:hello`)

- [ ] **Step 5: Update the three old tests to use new syntax**

In `src/plcc/spec/syntax/parse_syntactic_spec_test.py`:

Replace `test_named_lhs_non_terminal`:
```python
def test_named_lhs_non_terminal():
    named_lhs_line = makeLine("<noun:Name> ::= WORD")
    lines = [makeDivider(), named_lhs_line]
    expected = [
        makeStandardSyntacticRule(
            named_lhs_line,
            makeLhsNonTerminal("noun", "Name"),
            [makeTerminal("WORD")],
        )
    ]
    spec, _ = parse_syntactic_spec(lines)
    assert list(spec) == expected
```

Replace `test_single_char_capturing_terminal_with_altname`:
```python
def test_single_char_capturing_terminal_with_altname():
    single_char_alt = makeLine("<noun> ::= <A:b>")
    lines = [makeDivider(), single_char_alt]
    expected = [
        makeStandardSyntacticRule(
            single_char_alt,
            makeLhsNonTerminal("noun"),
            [makeCapturingTerminal("A", "b")],
        )
    ]
    spec, _ = parse_syntactic_spec(lines)
    assert list(spec) == expected
```

Replace `test_colon_rhs_non_terminal`:
```python
def test_colon_rhs_non_terminal():
    colon_rhs = makeLine("<noun> ::= WORD WORD <word:hello>")
    lines = [makeDivider(), colon_rhs]
    expected = [
        makeStandardSyntacticRule(
            colon_rhs,
            makeLhsNonTerminal("noun"),
            [
                makeTerminal("WORD"),
                makeTerminal("WORD"),
                makeRhsNonTerminal("word", "hello"),
            ],
        )
    ]
    spec, _ = parse_syntactic_spec(lines)
    assert list(spec) == expected
```

- [ ] **Step 6: Run all parser tests to verify all pass**

```bash
bin/test/units.bash src/plcc/spec/syntax/parse_syntactic_spec_test.py -v
```

Expected: All tests PASS.

- [ ] **Step 7: Commit**

```bash
git -C .worktrees/054-reconsider-bnf-syntax add \
  src/plcc/spec/syntax/parse_syntactic_spec.py \
  src/plcc/spec/syntax/parse_syntactic_spec_test.py
git -C .worktrees/054-reconsider-bnf-syntax commit -m "feat(syntax): move :name annotation inside angle brackets"
```

---

## Task 3: Update MalformedBNFError example syntax and column detection

**Files:**
- Modify: `src/plcc/spec/syntax/MalformedBNFError.py`
- Modify: `src/plcc/spec/syntax/MalformedBNFError_test.py`

- [ ] **Step 1: Update the failing test for the example syntax string**

In `src/plcc/spec/syntax/MalformedBNFError_test.py`, replace `test_str_includes_all_five_example_forms`:

```python
def test_str_includes_all_five_example_forms():
    err = MalformedBNFError(make_line("<stmt>IfStmt ::= IF"))
    s = str(err)
    assert "<NonTerminal> ::=" in s
    assert "<NonTerminal> ::= TOKEN <TOKEN> <Rhs>" in s
    assert "<NonTerminal:ClassName> ::= TOKEN <TOKEN:field1> <Rhs:field2>" in s
    assert "<NonTerminal> **= <Rhs>" in s
    assert "<NonTerminal> **= <Rhs> +SEPARATOR" in s
```

- [ ] **Step 2: Run to verify it fails**

```bash
bin/test/units.bash src/plcc/spec/syntax/MalformedBNFError_test.py::test_str_includes_all_five_example_forms -v
```

Expected: FAIL — old examples don't match.

- [ ] **Step 3: Update `MalformedBNFError.py`**

In `src/plcc/spec/syntax/MalformedBNFError.py`, update `_EXAMPLES` and the column-detection regex:

```python
import re


class MalformedBNFError(Exception):
    _EXAMPLES = (
        "Examples:\n"
        "  <NonTerminal> ::=\n"
        "  <NonTerminal> ::= TOKEN <TOKEN> <Rhs>\n"
        "  <NonTerminal:ClassName> ::= TOKEN <TOKEN:field1> <Rhs:field2>\n"
        "  <NonTerminal> **= <Rhs>\n"
        "  <NonTerminal> **= <Rhs> +SEPARATOR"
    )

    def __init__(self, line):
        self.line = line
        self.column = self._compute_column()

    def _compute_column(self):
        original = self.line.string
        leading = len(original) - len(original.lstrip())
        lhs_match = re.match(r"<[^>]+>", original.lstrip())
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

- [ ] **Step 4: Run all MalformedBNFError tests**

```bash
bin/test/units.bash src/plcc/spec/syntax/MalformedBNFError_test.py -v
```

Expected: All tests PASS. Note: the column tests use `<stmt>IfStmt ::= IF` — the new `<[^>]+>` regex matches `<stmt>` (stops at `>`), same as before, so column values are unchanged.

- [ ] **Step 5: Commit**

```bash
git -C .worktrees/054-reconsider-bnf-syntax add \
  src/plcc/spec/syntax/MalformedBNFError.py \
  src/plcc/spec/syntax/MalformedBNFError_test.py
git -C .worktrees/054-reconsider-bnf-syntax commit -m "fix(syntax): update MalformedBNFError examples for new BNF syntax"
```

---

## Task 4: Update `validate_lhs` to require PascalCase nonterminal names

**Files:**
- Modify: `src/plcc/spec/syntax/validations/validate_lhs.py`
- Modify: `src/plcc/spec/syntax/validations/validate_lhs_test.py`

- [ ] **Step 1: Add failing test for PascalCase being valid**

Add to `src/plcc/spec/syntax/validations/validate_lhs_test.py`:

```python
def test_pascal_case_lhs_name_is_valid():
    rule = makeSyntacticRule(
        makeLine("<Sentence> ::= WORD"),
        makeLhsNonTerminal("Sentence"),
        [makeTerminal("WORD")],
    )
    errors, _ = validate([rule])
    assert not any(isinstance(e, InvalidLhsNameError) for e in errors)


def test_lowercase_lhs_name_is_invalid():
    rule = makeSyntacticRule(
        makeLine("<sentence> ::= WORD"),
        makeLhsNonTerminal("sentence"),
        [makeTerminal("WORD")],
    )
    errors, _ = validate([rule])
    assert any(isinstance(e, InvalidLhsNameError) for e in errors)
```

- [ ] **Step 2: Run new tests to see which fail**

```bash
bin/test/units.bash src/plcc/spec/syntax/validations/validate_lhs_test.py::test_pascal_case_lhs_name_is_valid src/plcc/spec/syntax/validations/validate_lhs_test.py::test_lowercase_lhs_name_is_invalid -v
```

Expected: `test_pascal_case_lhs_name_is_valid` FAILS (currently PascalCase is rejected). `test_lowercase_lhs_name_is_invalid` PASSES.

- [ ] **Step 3: Update `validate_lhs.py`**

Replace the contents of `src/plcc/spec/syntax/validations/validate_lhs.py`:

```python
from ...ValidationError import ValidationError
from ..DuplicateLhsError import DuplicateLhsError
from ..InvalidLhsAltNameError import InvalidLhsAltNameError
from ..InvalidLhsNameError import InvalidLhsNameError
from ..SyntacticSpec import SyntacticSpec
from .class_name import is_valid_class_name


def validate_lhs(syntacticSpec: SyntacticSpec):
    return SyntacticLhsValidator(syntacticSpec.copy()).validate()


class SyntacticLhsValidator:
    spec: SyntacticSpec

    def __init__(self, syntacticSpec: SyntacticSpec):
        self.spec = syntacticSpec
        self.errorList = []
        self.nonTerminals = set()

    def validate(self) -> tuple[list[ValidationError], set[str]]:
        while len(self.spec) > 0:
            self.rule = self.spec.pop(0)
            self._checkLine()
        return self.errorList, self.nonTerminals

    def _checkLine(self):
        name, alt_name = self._getNames()
        self._checkName(name)
        if alt_name:
            self._checkAltName(alt_name)
        self._checkDuplicates()

    def _getNames(self) -> tuple[str, str]:
        return (self.rule.lhs.name, self.rule.lhs.altName)

    def _checkName(self, name: str):
        if not is_valid_class_name(name):
            self._appendInvalidLhsNameError()

    def _checkAltName(self, alt_name: str):
        if not is_valid_class_name(alt_name):
            self._appendInvalidLhsAltNameError()

    def _getResolvedName(self) -> str:
        name, alt_name = self._getNames()
        return alt_name if alt_name else name

    def _checkDuplicates(self):
        name = self._getResolvedName()
        if name in self.nonTerminals:
            self._appendDuplicateLhsError()
        self.nonTerminals.add(name)

    def _appendInvalidLhsNameError(self):
        self.errorList.append(InvalidLhsNameError(self.rule))

    def _appendInvalidLhsAltNameError(self):
        self.errorList.append(InvalidLhsAltNameError(self.rule))

    def _appendDuplicateLhsError(self):
        self.errorList.append(DuplicateLhsError(self.rule))
```

- [ ] **Step 4: Run all validate_lhs tests to see which old ones now fail**

```bash
bin/test/units.bash src/plcc/spec/syntax/validations/validate_lhs_test.py -v
```

Expected: New tests PASS. These old tests now fail because they assume old naming rules or use `capitalize()` behavior:
- `test_capital_lhs_terminal` (expects `Sentence` to be invalid — now it's valid)
- `test_undercase_lhs_alt_name` (uses `makeLhsNonTerminal("sentence", "name")` — `sentence` is now also invalid)
- `test_underscore_lhs_alt_name` (uses `makeLhsNonTerminal("sentence", "_name")`)
- `test_duplicate_lhs_name` (uses `makeLhsNonTerminal("sentence")`)
- `test_duplicate_lhs_alt_name` (uses `makeLhsNonTerminal("sentence", "Name")`)
- `test_duplicate_resolved_name` (relied on `name.capitalize()` for collision detection)

- [ ] **Step 5: Update old tests**

Replace each failing test in `src/plcc/spec/syntax/validations/validate_lhs_test.py`:

```python
# DELETE test_capital_lhs_terminal — behavior reversed; PascalCase is now required, not forbidden.
# The new test_pascal_case_lhs_name_is_valid and test_lowercase_lhs_name_is_invalid cover this.

def test_lowercase_lhs_alt_name():
    invalid_alt_name = makeLine("<Sentence:name> ::= WORD")
    spec = [
        makeSyntacticRule(
            invalid_alt_name,
            makeLhsNonTerminal("Sentence", "name"),
            [makeTerminal("WORD")],
        )
    ]
    errors, nonterms = validate(spec)
    assert len(errors) == 1
    assert errors[0] == makeInvalidLhsAltNameFormatError(spec[0])


def test_underscore_lhs_alt_name():
    invalid_alt_name = makeLine("<Sentence:_Name> ::= WORD")
    spec = [
        makeSyntacticRule(
            invalid_alt_name,
            makeLhsNonTerminal("Sentence", "_Name"),
            [makeTerminal("WORD")],
        )
    ]
    errors, nonterms = validate(spec)
    assert len(errors) == 1
    assert errors[0] == makeInvalidLhsAltNameFormatError(spec[0])


def test_duplicate_lhs_name():
    lhs_sentence = makeLhsNonTerminal("Sentence")
    rule_1 = makeSyntacticRule(
        makeLine("<Sentence> ::= VERB"),
        lhs_sentence,
        [makeTerminal("VERB")],
    )
    rule_2 = makeSyntacticRule(
        makeLine("<Sentence> ::= WORD"),
        lhs_sentence,
        [makeTerminal("WORD")],
    )
    spec = [rule_1, rule_2]
    errors, nonterms = validate(spec)
    assert len(errors) == 1
    assert errors[0] == makeDuplicateLhsError(spec[1])


def test_duplicate_lhs_alt_name():
    rule_1 = makeSyntacticRule(
        makeLine("<Sentence:Name> ::= VERB"),
        makeLhsNonTerminal("Sentence", "Name"),
        [makeTerminal("VERB")],
    )
    rule_2 = makeSyntacticRule(
        makeLine("<Sentence:Name> ::= WORD"),
        makeLhsNonTerminal("Sentence", "Name"),
        [makeTerminal("WORD")],
    )
    spec = [rule_1, rule_2]
    errors, nonterms = validate(spec)
    assert len(errors) == 1
    assert errors[0] == makeDuplicateLhsError(spec[1])


def test_duplicate_resolved_name():
    # <Sentence:Name> resolves to "Name"; <Name> also resolves to "Name" → collision
    alt_name = makeSyntacticRule(
        makeLine("<Sentence:Name> ::= VERB"),
        makeLhsNonTerminal("Sentence", "Name"),
        [makeTerminal("VERB")],
    )
    direct_name = makeSyntacticRule(
        makeLine("<Name> ::= WORD"),
        makeLhsNonTerminal("Name"),
        [makeTerminal("WORD")],
    )
    spec = [alt_name, direct_name]
    errors, nonterms = validate(spec)
    assert len(errors) == 1
    assert errors[0] == makeDuplicateLhsError(spec[1])
```

Note: `test_undercase_lhs_alt_name` is replaced by `test_lowercase_lhs_alt_name` (rename + updated names). Delete the old `test_capital_lhs_terminal` and `test_undercase_lhs_alt_name`.

- [ ] **Step 6: Run all validate_lhs tests**

```bash
bin/test/units.bash src/plcc/spec/syntax/validations/validate_lhs_test.py -v
```

Expected: All tests PASS.

- [ ] **Step 7: Commit**

```bash
git -C .worktrees/054-reconsider-bnf-syntax add \
  src/plcc/spec/syntax/validations/validate_lhs.py \
  src/plcc/spec/syntax/validations/validate_lhs_test.py
git -C .worktrees/054-reconsider-bnf-syntax commit -m "feat(syntax): require PascalCase for LHS nonterminal names and altNames"
```

---

## Task 5: Update `validate_rhs` to require PascalCase nonterminal names

**Files:**
- Modify: `src/plcc/spec/syntax/validations/validate_rhs.py`
- Modify: `src/plcc/spec/syntax/validations/validate_rhs_test.py`

Context: `validate_rhs_test.py` parses its spec strings through `parse_syntactic_spec`, so every test string using the old `:name` outside syntax OR using lowercase nonterminal names needs updating. The `validate` helper calls `parse` then `validate_rhs`.

- [ ] **Step 1: Add failing tests for the new nonterminal name rule**

Add to `src/plcc/spec/syntax/validations/validate_rhs_test.py`:

```python
def test_rhs_non_terminal_must_be_pascal_case():
    # lowercase RHS nonterminal name should generate InvalidNonterminal
    assertError(InvalidNonterminal, '''<Sentence> ::= <word>
<word> ::=''')


def test_rhs_pascal_case_non_terminal_is_valid():
    assertValid(InvalidNonterminal, '''<Word> ::=
<Sentence> ::= <Word>''')


def test_rhs_single_char_field_name_is_valid():
    # field names must allow single character (e.g. "e")
    assertValid(InvalidAttribute, '''<Word> ::=
<Sentence> ::= <Word:e>''')
```

- [ ] **Step 2: Run new tests to verify they fail**

```bash
bin/test/units.bash src/plcc/spec/syntax/validations/validate_rhs_test.py::test_rhs_non_terminal_must_be_pascal_case src/plcc/spec/syntax/validations/validate_rhs_test.py::test_rhs_pascal_case_non_terminal_is_valid src/plcc/spec/syntax/validations/validate_rhs_test.py::test_rhs_single_char_field_name_is_valid -v
```

Expected: `test_rhs_non_terminal_must_be_pascal_case` FAILS (lowercase name currently passes nonterminal check). `test_rhs_pascal_case_non_terminal_is_valid` FAILS (PascalCase currently rejected). `test_rhs_single_char_field_name_is_valid` FAILS (single-char field name rejected by `+` quantifier).

- [ ] **Step 3: Update `validate_rhs.py`**

Replace the `_validateNonTerminal` and `_validateNonTerminalAltName` methods in `src/plcc/spec/syntax/validations/validate_rhs.py`. Add the import at the top:

```python
from .class_name import is_valid_class_name
```

Update the two validation methods:

```python
def _validateNonTerminal(self, s, rule):
    if s.altName:
        self._validateNonTerminalAltName(s.altName, rule)
    if not is_valid_class_name(s.name):
        self._appendInvalidRhsError(rule)
    if not self._nonTerminalExists(s):
        self._appendMissingNonTerminalError(rule)


def _validateNonTerminalAltName(self, altName: str, rule):
    if not re.match(r"^[a-z][a-zA-Z0-9_]*$", altName):
        self._appendInvalidRhsAltNameError(rule)
```

- [ ] **Step 4: Run all validate_rhs tests to see which old ones now fail**

```bash
bin/test/units.bash src/plcc/spec/syntax/validations/validate_rhs_test.py -v
```

Expected: New tests PASS. Most existing tests fail because their spec strings use old outside-colon syntax (e.g., `<verb>:name`) and/or lowercase nonterminal names (e.g., `<sentence>`, `<verb>`, `<word>`).

- [ ] **Step 5: Update all test spec strings**

Replace the full body of existing tests in `src/plcc/spec/syntax/validations/validate_rhs_test.py`. Every spec string must use the new `<Name:field>` syntax and PascalCase nonterminal names. Here is the complete updated test file body (replace all tests except helpers):

```python
def test_rhs_non_terminal_must_not_start_with_underscore():
    assertError(InvalidNonterminal, '''<Sentence> ::= <_Hello>''')


def test_rhs_non_terminal_must_be_pascal_case():
    assertError(InvalidNonterminal, '''<Sentence> ::= <word>
<word> ::=''')


def test_rhs_pascal_case_non_terminal_is_valid():
    assertValid(InvalidNonterminal, '''<Word> ::=
<Sentence> ::= <Word>''')


def test_rhs_single_char_field_name_is_valid():
    assertValid(InvalidAttribute, '''<Word> ::=
<Sentence> ::= <Word:e>''')


def test_no_duplicate_Rhs_nonterminal():
    assertError(DuplicateAttribute, '''<Sentence> ::= <Verb> <Verb>''')


def test_duplicate_Rhs_nonterminal_with_same_alt_name_not_allowed():
    assertError(DuplicateAttribute, '''<Sentence> ::= <Verb:name> <Verb:name>''')


def test_duplicate_rhs_nonterminal_with_different_alt_name_allowed():
    assertValid(DuplicateAttribute, '''<Sentence> ::= <Verb:name> <Verb:different>''')


def test_duplicate_non_captured_terminals_allowed():
    assertValid(DuplicateAttribute, '''<Sentence> ::= ONE ONE ONE ONE''')


def test_duplicate_captured_terminals_not_allowed():
    assertError(DuplicateAttribute, '''<Sentence> ::= <ONE> <ONE>''')


def test_duplicate_captured_terminals_allowed_with_alt_name():
    assertValid('''<Sentence> ::= <ONE:name> <ONE:different>''')


def test_duplicate_captured_terminals_not_allowed_with_same_alt_name():
    assertError(DuplicateAttribute, '''<Sentence> ::= <ONE:same> <ONE:same>''')


def test_different_names_allowed():
    assertValid(DuplicateAttribute, '''<Sentence> ::= <No> <IS> <All> <Legal>''')


def test_duplicate_captured_terminal_and_non_terminal_not_allowed():
    # <NO> is a capturing terminal with attr "no"; <No> is a nonterminal with attr "no"
    assertError(DuplicateAttribute, '''<Sentence> ::= <NO> <No>''')


def test_duplicate_altName_and_nonterminal_name_not_allowed():
    # <No:yes> has attr "yes"; <Yes> has attr "yes" (name.lower())
    assertError(DuplicateAttribute, '''<Sentence> ::= <No:yes> <Yes>''')


def test_duplicate_altName_and_terminal_name_not_allowed():
    # <No:yes> has attr "yes"; <YES> capturing terminal has attr "yes"
    assertError(DuplicateAttribute, '''<Sentence> ::= <No:yes> <YES>''')


def test_one_nonterminal_with_different_altName_allowed():
    # <No:yes> attr "yes"; <No> attr "no" — different, so no duplicate
    assertValid(DuplicateAttribute, '''<Sentence> ::= <No:yes> <No>''')


def test_rhs_terminal_cannot_start_with_number():
    assertError(InvalidTerminal, "<Sentence> ::= 1WORD")


def test_rhs_non_terminal_alt_name_cannot_start_with_uppercase():
    assertError(InvalidAttribute, '''<Word> ::=
<Sentence> ::= <Word:Name>''')


def test_valid_spec():
    assertValid('''
        <Word> ::=
        <Sentence> ::= <Word>
    ''')


def test_valid_rhs_alt_name():
    assertValid(InvalidAttribute, '''<Word> ::=
<Sentence> ::= <Word:name>''')


def test_valid_separator_terminal():
    assertValid('''<Sentence> **= WORD +PERIOD''')


def test_missing_non_terminal():
    assertError(UndefinedNonterminal, '''<Sentence> ::= <Word>''')


def test_invalid_separator_terminal():
    assertError(InvalidSeparator, '''<Sentence> **= WORD +period''')
```

- [ ] **Step 6: Run all validate_rhs tests**

```bash
bin/test/units.bash src/plcc/spec/syntax/validations/validate_rhs_test.py -v
```

Expected: All tests PASS.

- [ ] **Step 7: Commit**

```bash
git -C .worktrees/054-reconsider-bnf-syntax add \
  src/plcc/spec/syntax/validations/validate_rhs.py \
  src/plcc/spec/syntax/validations/validate_rhs_test.py
git -C .worktrees/054-reconsider-bnf-syntax commit -m "feat(syntax): require PascalCase for RHS nonterminal names"
```

---

## Task 6: Update `build_model` to remove redundant capitalize transforms

**Files:**
- Modify: `src/plcc/model/build_model.py`
- Modify: `src/plcc/model/build_model_test.py`

Context: `build_model.py` applies `.upper() + [1:]` capitalize transforms to nonterminal names in three places. Since names are now always PascalCase from the validated spec, these transforms are no-ops on correct input. Remove them and update the test spec dicts to use PascalCase names (reflecting what a validated spec actually produces).

- [ ] **Step 1: Update spec dicts in the test file to use PascalCase names**

In `src/plcc/model/build_model_test.py`, update every `"name"` value in `lhs` and `rhsSymbolList` entries that currently use lowercase nonterminal names. The key changes are:

In `_TRIVIAL_SPEC`:
```python
"lhs": {"name": "Program", "isTerminal": False, "altName": None, "isCapturing": False},
```
And update `test_returns_model_with_start`:
```python
def test_returns_model_with_start():
    model = build_model(_TRIVIAL_SPEC)
    assert model['start'] == 'Program'
```

In `_ARITH_SPEC`, change `"program"` → `"Program"` in the `lhs` dict for the first rule.

In `_ARBNO_SPEC`, change all lowercase nonterminal names:
- `"program"` → `"Program"` in the first rule's lhs
- `"rands"` → `"Rands"` everywhere it appears (lhs name and rhsSymbolList name)
- `"expr"` → `"Expr"` everywhere

Also update assertions in tests that reference the old start name:
- `test_arbno_field_type_is_base_element_type` expects `'Expr'` — this may already be correct if the field type came from a capitalize call on `"expr"`. After updating the spec dict to `"Expr"`, the type should still be `"Expr"`.

- [ ] **Step 2: Run build_model tests to confirm they still pass (capitalize is no-op on PascalCase)**

```bash
bin/test/units.bash src/plcc/model/build_model_test.py -v
```

Expected: All tests PASS (capitalize of PascalCase is identity).

- [ ] **Step 3: Remove the three capitalize transforms from `build_model.py`**

In `src/plcc/model/build_model.py`:

Line ~38 in `_build_classes`:
```python
# Before
class_name = nt_name[:1].upper() + nt_name[1:]
# After
class_name = nt_name
```

Line ~92 in `_extract_arbno_fields`:
```python
# Before
field_type = n[:1].upper() + n[1:]
# After
field_type = n
```

Line ~107 in `_extract_fields`:
```python
# Before
field_type = name[:1].upper() + name[1:]
# After
field_type = name
```

- [ ] **Step 4: Run all build_model tests**

```bash
bin/test/units.bash src/plcc/model/build_model_test.py -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git -C .worktrees/054-reconsider-bnf-syntax add \
  src/plcc/model/build_model.py \
  src/plcc/model/build_model_test.py
git -C .worktrees/054-reconsider-bnf-syntax commit -m "refactor(model): drop redundant capitalize transforms now that names are PascalCase"
```

---

## Task 7: Update `replace_repeating_with_standard_rules` to use new syntax and `#nil`

**Files:**
- Modify: `src/plcc/spec/syntax/validations/replace_repeating_with_standard_rules.py`
- Modify: `src/plcc/spec/syntax/validations/replace_repeating_with_standard_rules_test.py`

Context: The expander generates synthetic `StandardSyntacticRule` objects with `altName="void"`. This changes to `altName="#nil"` — a name that can never be typed by users (fails the class-name regex). The `line` strings (used only in error messages) also update to show new syntax. The `LhsNonTerminal` objects are constructed directly, not through the parser, so no parser change is needed here.

- [ ] **Step 1: Update the test expectations**

In `src/plcc/spec/syntax/validations/replace_repeating_with_standard_rules_test.py`:

The test helper `buildLineStandard` currently generates old-syntax line strings (`<lhs>:altName`). Update it to generate new-syntax strings (`<lhs:altName>`):

```python
def buildLineStandard(lhs, rhs):
    if lhs.__contains__(":"):
        name, alt = lhs.split(":", 1)
        return makeLine(f"<{name}:{alt}> ::={buildRhs(rhs)}")
    return makeLine(f"<{lhs}> ::={buildRhs(rhs)}")
```

Update the expected specs in `test_no_separator` and `test_with_separator`. The synthetic void rules change from `"name:void"` to `"name:#nil"`:

In `test_no_separator`, change:
```python
makeStandardSyntacticRule("name:#nil", []),
```

In `test_with_separator`, change both occurrences of `"name:void"` and `"name#:void"`:
```python
makeStandardSyntacticRule("name:#nil", []),
makeStandardSyntacticRule(
    "name#:#nil",
    [makeTerminal("SEP"), makeTerminal("WORD"), makeRhsNonTerminal("name#")],
),
makeStandardSyntacticRule("name#:#nil", []),
```

The `makeLhsNonTerminal` helper splits on `:` to extract altName — no change needed there since `"name:#nil".split(":")` → `["name", "#nil"]` works correctly.

- [ ] **Step 2: Run tests to verify they fail**

```bash
bin/test/units.bash src/plcc/spec/syntax/validations/replace_repeating_with_standard_rules_test.py -v
```

Expected: `test_no_separator` and `test_with_separator` FAIL — the actual output still uses `"void"`.

- [ ] **Step 3: Update `replace_repeating_with_standard_rules.py`**

Change every `"void"` altName to `"#nil"` and update the `line` strings to use new syntax. The four affected methods:

```python
def _appendVoidRule(self):
    self._appendRule(
        line=f"<{self.rule.lhs.name}:#nil> ::=",
        lhs=self._makeLHS(self.rule.lhs.name, "#nil"),
        rhs=[],
    )

def _appendNTSepRule(self):
    self._appendRule(
        line=f"<{self.ntsep}:#nil> ::= {self.rule.separator.name} {
            self.rhs_string} <{self.ntsep}>",
        lhs=self._makeLHS(self.ntsep, "#nil"),
        rhs=[self.rule.separator]
        + self.rule.rhsSymbolList
        + [self._makeRhsNonTerminal(self.ntsep)],
    )

def _appendVoidNTSepRule(self):
    self._appendRule(
        line=f"<{self.ntsep}:#nil> ::=",
        lhs=self._makeLHS(self.ntsep, "#nil"),
        rhs=[],
    )
```

Also update `_appendBaseRule` and `_appendSepBaseRule` line strings (these don't use `void` but still use the old line format — update for consistency):

```python
def _appendBaseRule(self):
    self._appendRule(
        line=f"<{self.rule.lhs.name}> ::= {
            self.rhs_string} <{self.rule.lhs.name}>",
        lhs=self.rule.lhs,
        rhs=self.rule.rhsSymbolList
        + [self._makeRhsNonTerminal(self.rule.lhs.name)],
    )

def _appendSepBaseRule(self):
    self._appendRule(
        line=f"<{self.rule.lhs.name}> ::= {
            self.rhs_string} <{self.ntsep}>",
        lhs=self.rule.lhs,
        rhs=self.rule.rhsSymbolList + [self._makeRhsNonTerminal(self.ntsep)],
    )
```

- [ ] **Step 4: Run all replace_repeating tests**

```bash
bin/test/units.bash src/plcc/spec/syntax/validations/replace_repeating_with_standard_rules_test.py -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git -C .worktrees/054-reconsider-bnf-syntax add \
  src/plcc/spec/syntax/validations/replace_repeating_with_standard_rules.py \
  src/plcc/spec/syntax/validations/replace_repeating_with_standard_rules_test.py
git -C .worktrees/054-reconsider-bnf-syntax commit -m "refactor(syntax): use #nil for synthetic altName and new line syntax in repeating rule expansion"
```

---

## Task 8: Update `validate_syntactic_spec_test` and run full unit suite

**Files:**
- Modify: `src/plcc/spec/syntax/validations/validate_syntactic_spec_test.py`

- [ ] **Step 1: Update the spec string in the test**

In `src/plcc/spec/syntax/validations/validate_syntactic_spec_test.py`, `test_simple_valid_spec` has:

```python
makeLine('<one> ::= ONE'),
makeLhsNonTerminal('one'),
```

Change to:

```python
makeLine('<One> ::= ONE'),
makeLhsNonTerminal('One'),
```

- [ ] **Step 2: Run the full unit suite**

```bash
bin/test/units.bash
```

Expected: All unit tests PASS.

- [ ] **Step 3: Commit**

```bash
git -C .worktrees/054-reconsider-bnf-syntax add \
  src/plcc/spec/syntax/validations/validate_syntactic_spec_test.py
git -C .worktrees/054-reconsider-bnf-syntax commit -m "test(syntax): update validate_syntactic_spec test for PascalCase names"
```

---

## Task 9: Update fixture `.plcc` files and run integration/e2e tests

**Files:**
- Modify: `tests/fixtures/arith.plcc`
- Modify: `tests/fixtures/trivial.plcc`
- Modify: `tests/fixtures/trivial-full.plcc`
- Modify: `tests/fixtures/trivial-java.plcc`
- Modify: `tests/fixtures/trivial-python.plcc`
- Modify: `tests/fixtures/trivial-arbno.plcc`

- [ ] **Step 1: Update `tests/fixtures/trivial.plcc`**

```
token NUM '\d+'
skip WS '\s+'
%
<Program> ::= NUM
```

- [ ] **Step 2: Update `tests/fixtures/trivial-full.plcc`**

```
token NUM '\d+'
skip WS '\s+'
%
<Program> ::= NUM
% Java Java
% py Python
```

- [ ] **Step 3: Update `tests/fixtures/trivial-java.plcc`**

```
token NUM '\d+'
skip SPACE '\s+'
%
<Program> ::= <NUM:num>
% Java Java
Program
%%%
    public void _run() {
        System.out.println(num.toString());
    }
%%%
```

- [ ] **Step 4: Update `tests/fixtures/trivial-python.plcc`**

```
token NUM '\d+'
skip WS '\s+'
%
<Program> ::= <NUM:num>
% py Python
Program
%%%
def _run(self):
    return int(self.num.lexeme)
%%%
```

- [ ] **Step 5: Update `tests/fixtures/arith.plcc`**

```
token NUM   '\d+'
token PLUS  '\+'
skip  SPACE '\s+'
%
<Program>              ::= <Expr:expr>
<Expr>                 ::= <Term:term> <ExprRest:rest>
<ExprRest:AddRest>     ::= PLUS <Term:term> <ExprRest:rest>
<ExprRest:NilRest>     ::=
<Term>                 ::= <NUM:num>
%
% calculate Python
Program
%%%
def _run(self):
    return self.expr.eval()
%%%
Expr
%%%
def eval(self):
    return self.rest.eval(self.term.eval())
%%%
AddRest
%%%
def eval(self, acc):
    return self.rest.eval(acc + self.term.eval())
%%%
NilRest
%%%
def eval(self, acc):
    return acc
%%%
Term
%%%
def eval(self):
    return int(self.num.lexeme)
%%%
```

- [ ] **Step 6: Update `tests/fixtures/trivial-arbno.plcc`**

```
token NUM   '\d+'
token PLUS  '\+'
token COMMA ','
skip  SPACE '\s+'
%
<Program>          ::= <Rands:rands>
<Rands>            **= <Expr:expr> +COMMA
<Expr:LitExpr>     ::= <NUM:num>
<Expr:AddExpr>     ::= PLUS <Rands:rands>
%
% eval Python
Program
%%%
def _run(self):
    return [e.eval() for e in self.rands.exprList]
%%%
LitExpr
%%%
def eval(self):
    return int(self.num.lexeme)
%%%
AddExpr
%%%
def eval(self):
    return sum(e.eval() for e in self.rands.exprList)
%%%
```

- [ ] **Step 7: Run commands and e2e tests**

```bash
bin/test/commands.bash
bin/test/e2e.bash
```

Expected: All tests PASS. If any bats tests reference old syntax in inline grammar strings, update those as well (check `tests/bats/` for any hardcoded grammar strings using the old format).

- [ ] **Step 8: Commit**

```bash
git -C .worktrees/054-reconsider-bnf-syntax add tests/fixtures/
git -C .worktrees/054-reconsider-bnf-syntax commit -m "feat(fixtures): update all .plcc fixtures to new BNF syntax"
```

---

## Task 10: Final verification

- [ ] **Step 1: Run the full functional test suite**

```bash
bin/test/functional.bash
```

Expected: All tiers PASS (units + commands + integration + e2e).

- [ ] **Step 2: Check for any remaining old-syntax strings in bats tests**

```bash
grep -rn ">:[a-zA-Z]" tests/bats/ src/
```

Expected: No matches (all old outside-colon syntax has been removed).

- [ ] **Step 3: Check for any remaining lowercase nonterminal names in grammar strings**

```bash
grep -rn "<[a-z][a-zA-Z]*>" tests/fixtures/ tests/bats/
```

Expected: No matches in fixture files or bats test grammars.
