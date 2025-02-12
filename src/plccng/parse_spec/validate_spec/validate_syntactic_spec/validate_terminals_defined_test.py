from typing import List

# Dependencies
from plccng.parse_spec.structs import (
    CapturingTerminal,
    LexicalRule,
    LhsNonTerminal,
    Line,
    Symbol,
    SyntacticRule,
    Terminal,
    LexicalSpec,
    SyntacticSpec,
    RepeatingSyntacticRule
)
from .validate_terminals_defined import validate_terminals_defined
from plccng.parse_spec.errors import UndefinedTerminalError

def test_undefined_terminal_error():
    lexicalSpec = makeLexicalSpec([])
    syntacticSpec = makeSyntacticSpec([
        makeSyntacticRule(
            makeLine("<sentence> ::= THIS"),
            makeLhsNonTerminal("sentence"),
            [makeTerminal("THIS")]
        )
    ])
    errors = validateTerms(syntacticSpec, lexicalSpec)
    assert len(errors) == 1
    assert isinstance(errors[0], UndefinedTerminalError)


def test_no_lexical_spec_undefined_error():
    lexicalSpec = None
    syntacticSpec = makeSyntacticSpec([
        makeSyntacticRule(
            makeLine("<sentence> ::= THIS"),
            makeLhsNonTerminal("sentence"),
            [makeTerminal("THIS")]
        )
    ])
    errors = validateTerms(syntacticSpec, lexicalSpec)
    assert len(errors) == 1
    assert isinstance(errors[0], UndefinedTerminalError)


def test_valid_defined_terminal():
    this = makeLexicalRule(name="THIS", pattern="THIS")
    lexicalSpec = makeLexicalSpec([this])
    syntacticSpec = makeSyntacticSpec([
        makeSyntacticRule(
            makeLine("<sentence> ::= THIS"),
            makeLhsNonTerminal("sentence"),
            [makeTerminal("THIS")]
        )
    ])
    errors = validateTerms(syntacticSpec, lexicalSpec)
    assert len(errors) == 0

def test_multiple_undefined_terminals_error():
    lexicalSpec = makeLexicalSpec([])
    syntacticSpec = makeSyntacticSpec([
        makeSyntacticRule(
            makeLine("<sentence> ::= THIS FIRST SECOND"),
            makeLhsNonTerminal("sentence"),
            [makeTerminal("THIS"), makeTerminal("FIRST"), makeTerminal("SECOND")]
        )
    ])
    errors = validateTerms(syntacticSpec, lexicalSpec)
    assert len(errors) == 3
    for e in errors:
        assert isinstance(e, UndefinedTerminalError)

def test_multiple_valid_defined_terminals():
    this = makeLexicalRule(name="THIS", pattern="THIS")
    first = makeLexicalRule(name="FIRST", pattern="FIRST")
    second = makeLexicalRule(name="SECOND", pattern="SECOND")
    lexicalSpec = makeLexicalSpec([this, first, second])
    syntacticSpec = makeSyntacticSpec([
        makeSyntacticRule(
            makeLine("<sentence> ::= THIS FIRST SECOND"),
            makeLhsNonTerminal("sentence"),
            [makeTerminal("THIS"), makeTerminal("FIRST"), makeTerminal("SECOND")]
        )
    ])
    errors = validateTerms(syntacticSpec, lexicalSpec)
    assert len(errors) == 0

def test_undefined_terminal_with_defined_terminal_error():
    this = makeLexicalRule(name="THIS", pattern="THIS")
    first = makeLexicalRule(name="FIRST", pattern="FIRST")
    lexicalSpec = makeLexicalSpec([this, first])
    syntacticSpec = makeSyntacticSpec([
        makeSyntacticRule(
            makeLine("<sentence> ::= THIS FIRST SECOND"),
            makeLhsNonTerminal("sentence"),
            [makeTerminal("THIS"), makeTerminal("FIRST"), makeTerminal("SECOND")]
        )
    ])
    errors = validateTerms(syntacticSpec, lexicalSpec)
    assert len(errors) == 1

def test_valid_defined_captured_terminal():
    first = makeLexicalRule(name="FIRST", pattern="FIRST")
    lexicalSpec = makeLexicalSpec([first])
    syntacticSpec = makeSyntacticSpec([
        makeSyntacticRule(
            makeLine("<sentence> ::= <FIRST>"),
            makeLhsNonTerminal("sentence"),
            [makeCapturingTerminal("FIRST")]
        )
    ])
    errors = validateTerms(syntacticSpec, lexicalSpec)
    assert len(errors) == 0

def test_undefined_captured_terminal_error():
    lexicalSpec = makeLexicalSpec([])
    syntacticSpec = makeSyntacticSpec([
        makeSyntacticRule(
            makeLine("<sentence> ::= <FIRST>"),
            makeLhsNonTerminal("sentence"),
            [makeCapturingTerminal("FIRST")]
        )
    ])
    errors = validateTerms(syntacticSpec, lexicalSpec)
    assert len(errors) == 1
    assert isinstance(errors[0], UndefinedTerminalError)

def test_multiple_undefined_captured_terminals_with_different_rules_error():
    lexicalSpec = makeLexicalSpec([])
    syntacticSpec = makeSyntacticSpec([
        makeSyntacticRule(
            makeLine("<sentence> ::= <FIRST>"),
            makeLhsNonTerminal("sentence"),
            [makeCapturingTerminal("FIRST")]
        ),
        makeSyntacticRule(
            makeLine("<two> ::= <SECOND>"),
            makeLhsNonTerminal("two"),
            [makeCapturingTerminal("SECOND")]
        )
    ])
    errors = validateTerms(syntacticSpec, lexicalSpec)
    assert len(errors) == 2
    for e in errors:
        assert isinstance(e, UndefinedTerminalError)

def test_valid_defined_and_captured_terminals():
    first = makeLexicalRule(name="FIRST", pattern="FIRST")
    second = makeLexicalRule(name="SECOND", pattern="SECOND")
    third = makeLexicalRule(name="THIRD", pattern="THIRD")
    lexicalSpec = makeLexicalSpec([first, second, third])
    syntacticSpec = makeSyntacticSpec([
        makeSyntacticRule(
            makeLine("<sentence> ::= <FIRST> SECOND THIRD"),
            makeLhsNonTerminal("sentence"),
            [makeCapturingTerminal("FIRST"), makeTerminal("SECOND"), makeTerminal("THIRD")]
        )
    ])
    errors = validateTerms(syntacticSpec, lexicalSpec)
    assert len(errors) == 0

def test_valid_separator_terminal():
    verb = makeLexicalRule(name="VERB", pattern="VERB")
    sep = makeLexicalRule(name="SEP", pattern="SEP")
    lexicalSpec = makeLexicalSpec([verb, sep])
    rule = makeRepeatingSyntacticRule(
        "sentence",
        [makeTerminal("VERB")],
        separator=makeTerminal("SEP")
    )
    syntacticSpec = makeSyntacticSpec([rule])
    errors = validateTerms(syntacticSpec, lexicalSpec)
    assert len(errors) == 0

def test_undefined_separator_terminal_error():
    verb = makeLexicalRule(name="VERB", pattern="VERB")
    lexicalSpec = makeLexicalSpec([verb])
    rule = makeRepeatingSyntacticRule(
        "sentence",
        [makeTerminal("VERB")],
        separator=makeTerminal("COMMA")
    )
    syntacticSpec = makeSyntacticSpec([rule])
    errors = validateTerms(syntacticSpec, lexicalSpec)
    assert len(errors) == 1

def test_repeating_rule_no_separator_defined_terminals():
    verb = makeLexicalRule(name="VERB", pattern="VERB")
    lexicalSpec = makeLexicalSpec([verb])
    rule = makeRepeatingSyntacticRule(
        "sentence",
        [makeTerminal("VERB"), makeCapturingTerminal("VERB")]
    )
    syntacticSpec = makeSyntacticSpec([rule])
    errors = validateTerms(syntacticSpec, lexicalSpec)
    assert len(errors) == 0

def test_repeating_rule_no_separator_undefined_terminals():
    lexicalSpec = makeLexicalSpec([])
    rule = makeRepeatingSyntacticRule(
        "sentence",
        [makeTerminal("VERB"), makeCapturingTerminal("VERB")]
    )
    syntacticSpec = makeSyntacticSpec([rule])
    errors = validateTerms(syntacticSpec, lexicalSpec)
    assert len(errors) == 2

def makeLexicalSpec(ruleList=None):
    return LexicalSpec(ruleList)

def makeLexicalRule(name='TEST', pattern='TEST'):
    return LexicalRule(makeLine('TEST'), False, name, pattern)

def makeRepeatingSyntacticRule(lhs: str, rhsList: List[Symbol], separator=None):
    return RepeatingSyntacticRule(
        buildLineRepeating(lhs, rhsList, separator),
        makeLhsNonTerminal(lhs),
        rhsList,
        separator,
    )

def buildLineRepeating(lhs, rhs, sep=None):
    if sep:
        return makeLine(f"{lhs} **={buildRhs(rhs)} +{sep.name}")
    return makeLine(f"{lhs} **={buildRhs(rhs)}")

def buildRhs(rhs):
    s = ""
    for symbol in rhs:
        s += " " + symbol.name
    return s

def validateTerms(syntacticSpec: SyntacticSpec, lexicalSpec: LexicalSpec = []):
    return validate_terminals_defined(syntacticSpec, lexicalSpec)

def makeSyntacticSpec(ruleList=None):
    return SyntacticSpec(ruleList)

def makeSyntacticRule(line: Line, lhs: LhsNonTerminal, rhsList: List[Symbol]):
    return SyntacticRule(line, lhs, rhsList)

def makeLine(string, lineNumber=1, file=None):
    return Line(string, lineNumber, file)

def makeLhsNonTerminal(name: str | None, altName: str | None = None):
    return LhsNonTerminal(name, altName)

def makeTerminal(name: str | None):
    return Terminal(name)

def makeCapturingTerminal(name: str | None, altName: str | None = None):
    return CapturingTerminal(name, altName)
