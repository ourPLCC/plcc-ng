from typing import List
from ...load_rough_spec.parse_lines import Line
from ...parse_spec.parse_syntactic_spec import (
    SyntacticRule,
    SyntacticSpec,
    Symbol,
    LhsNonTerminal,
    Terminal,
    RhsNonTerminal,
    CapturingTerminal,
)
from .errors import (
    InvalidRhsNameError,
    InvalidRhsAltNameError,
    InvalidRhsTerminalError,
    RepeatRhsSymbolNameError,
)
from .validate_rhs import validate_rhs


def test_number_rhs_terminal():
    invalid_terminal = makeLine("<sentence> ::= 1WORD")
    spec = [
        makeSyntacticRule(
            invalid_terminal, makeLhsNonTerminal("sentence"), [makeTerminal("1WORD")]
        )
    ]
    errors = validate(spec)
    assert len(errors) == 1
    assert errors[0] == makeInvalidRhsTerminalFormatError(spec[0])

def test_uppercase_rhs_alt_name():
    invalid_alt_name = makeLine("<sentence> ::= <word>:Name")
    Name1 = [
        makeSyntacticRule(
            invalid_alt_name,
            makeLhsNonTerminal("sentence"),
            [makeRhsNonTerminal("word", "Name")],
        )
    ]
    errors = validate(Name1)
    assert len(errors) == 1
    assert errors[0] == makeInvalidRhsAltNameFormatError(Name1[0])


def test_valid_rhs_alt_name():
    invalid_alt_name = makeLine("<sentence> ::= <word>:name")
    Name1 = [
        makeSyntacticRule(
            invalid_alt_name,
            makeLhsNonTerminal("sentence"),
            [makeRhsNonTerminal("word", "name")],
        )
    ]
    errors = validate(Name1)
    assert len(errors) == 0


def test_invalid_Rhs_error():
    name1 = makeSyntacticRule(
        makeLine("<sentence> ::= VERB"),
        makeLhsNonTerminal("sentence"),
        [makeTerminal("VERB")],
    )
    name2 = makeSyntacticRule(
        makeLine("<name> ::= <VERB>"),
        makeLhsNonTerminal("name"),
        [makeRhsNonTerminal("VERB")],
    )
    spec = [name1, name2]
    errors = validate(spec)
    assert len(errors) == 1
    assert errors[0] == makeInvalidRhsNameFormatError(spec[1])

def test_no_repeat_Rhs_nonterminal():
    rule = makeSyntacticRule(
        makeLine("<sentence> ::= <verb> <verb>"),
        makeLhsNonTerminal("sentence"),
        [makeRhsNonTerminal("verb"), makeRhsNonTerminal("verb")]
    )
    spec = [rule]
    errors = validate(spec)
    assert len(errors) == 1
    assert errors[0] == makeRepeateRhsSymbolError(spec[0])

def test_repeat_Rhs_nonterminal_with_same_alt_name_not_allowed():
    rule = makeSyntacticRule(
        makeLine("<sentence> ::= <verb>:name <verb>:name"),
        makeLhsNonTerminal("sentence"),
        [makeRhsNonTerminal("verb", "name"), makeRhsNonTerminal("verb", "name")]
    )
    spec = [rule]
    errors = validate(spec)
    assert len(errors) == 1
    assert errors[0] == makeRepeateRhsSymbolError(spec[0])

def test_repeat_rhs_nonterminal_with_different_alt_name_allowed():
    rule = makeSyntacticRule(
        makeLine("<sentence> ::= <verb>:name <verb>:different"),
        makeLhsNonTerminal("sentence"),
        [makeRhsNonTerminal("verb", "name"), makeRhsNonTerminal("verb", "different")]
    )
    spec = [rule]
    errors = validate(spec)
    assert len(errors) == 0

def test_repeating_non_captured_terminals_allowed():
    rule = makeSyntacticRule(
        makeLine("<sentence> ::= ONE ONE ONE ONE ONE"),
        makeLhsNonTerminal("sentence"),
        [makeTerminal("ONE"), makeTerminal("ONE"), makeTerminal("ONE"), makeTerminal("ONE"), makeTerminal("ONE")]
    )
    spec = [rule]
    errors = validate(spec)
    assert len(errors) == 0

def test_repeating_captured_terminals_not_allowed():
    rule = makeSyntacticRule(
        makeLine("<sentence> ::== <ONE> <ONE>"),
        makeLhsNonTerminal("sentence"),
        [makeCapturingTerminal("ONE"), makeCapturingTerminal("ONE")]
    )
    spec = [rule]
    errors = validate(spec)
    assert len(errors) == 1
    assert errors[0] == makeRepeateRhsSymbolError(spec[0])

def test_repeating_captured_terminals_allowed_with_alt_name():
    rule = makeSyntacticRule(
        makeLine("<sentence> ::== <ONE>:name <ONE>:different"),
        makeLhsNonTerminal("sentence"),
        [makeCapturingTerminal("ONE", "name"), makeCapturingTerminal("ONE", "different")]
    )
    spec = [rule]
    errors = validate(spec)
    assert len(errors) == 0

def test_repeating_captured_terminals_not_allowed_with_same_alt_name():
    rule = makeSyntacticRule(
        makeLine("<sentence> ::== <ONE>:same <ONE>:same"),
        makeLhsNonTerminal("sentence"),
        [makeCapturingTerminal("ONE", "same"), makeCapturingTerminal("ONE", "same")]
    )
    spec = [rule]
    errors = validate(spec)
    assert len(errors) == 1
    assert errors[0] == makeRepeateRhsSymbolError(spec[0])

def validate(syntacticSpec: SyntacticSpec):
    return validate_rhs(syntacticSpec)


def makeSyntacticRule(line: Line, lhs: LhsNonTerminal, rhsList: List[Symbol]):
    return SyntacticRule(line, lhs, rhsList)


def makeLine(string, lineNumber=1, file=None):
    return Line(string, lineNumber, file)


def makeLhsNonTerminal(name: str | None, altName: str | None = None):
    return LhsNonTerminal(name, altName)


def makeRhsNonTerminal(name: str | None, altName: str | None = None):
    return RhsNonTerminal(name, altName)


def makeTerminal(name: str | None):
    return Terminal(name)

def makeCapturingTerminal(name: str, altName: str | None = None):
    return CapturingTerminal(name, altName)


def makeInvalidRhsNameFormatError(rule):
    return InvalidRhsNameError(rule)


def makeInvalidRhsAltNameFormatError(rule):
    return InvalidRhsAltNameError(rule)


def makeInvalidRhsTerminalFormatError(rule):
    return InvalidRhsTerminalError(rule)

def makeRepeateRhsSymbolError(rule):
    return RepeatRhsSymbolNameError(rule)
