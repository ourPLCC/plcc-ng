from typing import List

from ...errors import InvalidRhsAltNameError, InvalidRhsNameError, InvalidRhsTerminalError
from ...structs import CapturingTerminal, LhsNonTerminal, Line, RepeatingSyntacticRule, RhsNonTerminal, Symbol, SyntacticRule, Terminal
from ...structs import (
    SyntacticSpec
)
from ...errors import (
    InvalidRhsSeparatorTypeError
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

def test_invalid_undefined_separator():
    rule = makeRepeatingSyntacticRule(
        "sentence",
        [makeTerminal("VERB")],
    )
    spec = [rule]
    errors = validate(spec)
    assert len(errors) == 1
    assert errors[0] == makeInvalidRhsSeparatorTypeError(spec[0])

def test_invalid_separator_not_terminal():
    rule = makeRepeatingSyntacticRule(
        "sentence",
        [makeTerminal("VERB")],
        separator=makeRhsNonTerminal("sep")
    )
    spec = [rule]
    errors = validate(spec)
    assert len(errors) == 1
    assert errors[0] == makeInvalidRhsSeparatorTypeError(spec[0])

def test_valid_separator_terminal():
    rule = makeRepeatingSyntacticRule(
        "sentence",
        [makeTerminal("VERB")],
        separator=makeTerminal("SEP")
    )
    spec = [rule]
    errors = validate(spec)
    assert len(errors) == 0

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


def makeInvalidRhsNameFormatError(rule):
    return InvalidRhsNameError(rule)


def makeInvalidRhsAltNameFormatError(rule):
    return InvalidRhsAltNameError(rule)


def makeInvalidRhsTerminalFormatError(rule):
    return InvalidRhsTerminalError(rule)

def makeInvalidRhsSeparatorTypeError(rule):
    return InvalidRhsSeparatorTypeError(rule)
