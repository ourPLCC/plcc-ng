from typing import List

from ....lineparse.Line import Line

from ...errors import InvalidLhsAltNameError, InvalidLhsNameError
from ...structs import LhsNonTerminal, Symbol, SyntacticRule, Terminal
from ...structs import (
    SyntacticSpec,
)
from ...errors import (
    DuplicateLhsError
)
from .validate_lhs import validate_lhs


def test_capital_lhs_terminal():
    capital_lhs_name = makeLine("<Sentence> ::= WORD")
    spec = [
        makeSyntacticRule(
            capital_lhs_name, makeLhsNonTerminal("Sentence"), [makeTerminal("WORD")]
        )
    ]
    errors, nonterms = validate(spec)
    assert len(errors) == 1
    assert errors[0] == makeInvalidLhsNameFormatError(spec[0])


def test_undercase_lhs_alt_name():
    invalid_alt_name = makeLine("<sentence>:name ::= WORD")
    spec = [
        makeSyntacticRule(
            invalid_alt_name,
            makeLhsNonTerminal("sentence", "name"),
            [makeTerminal("WORD")],
        )
    ]
    errors, nonterms = validate(spec)
    assert len(errors) == 1
    assert errors[0] == makeInvalidLhsAltNameFormatError(spec[0])


def test_underscore_lhs_alt_name():
    invalid_alt_name = makeLine("<sentence>:_name ::= WORD")
    spec = [
        makeSyntacticRule(
            invalid_alt_name,
            makeLhsNonTerminal("sentence", "_name"),
            [makeTerminal("WORD")],
        )
    ]
    errors, nonterms = validate(spec)
    assert len(errors) == 1
    assert errors[0] == makeInvalidLhsAltNameFormatError(spec[0])


def test_duplicate_lhs_name():
    lhs_sentence = makeLhsNonTerminal("sentence")
    rule_1 = makeSyntacticRule(
        makeLine("<sentence> ::= VERB"),
        lhs_sentence,
        [makeTerminal("VERB")],
    )
    rule_2 = makeSyntacticRule(
        makeLine("<sentence> ::= WORD"),
        lhs_sentence,
        [makeTerminal("WORD")],
    )
    spec = [rule_1, rule_2]
    errors, nonterms = validate(spec)
    assert len(errors) == 1
    assert errors[0] == makeDuplicateLhsError(spec[1])


def test_duplicate_lhs_alt_name():
    rule_1 = makeSyntacticRule(
        makeLine("<sentence>:Name ::= VERB"),
        makeLhsNonTerminal("sentence", "Name"),
        [makeTerminal("VERB")],
    )
    rule_2 = makeSyntacticRule(
        makeLine("<sentence>:Name ::= WORD"),
        makeLhsNonTerminal("sentence", "Name"),
        [makeTerminal("WORD")],
    )
    spec = [rule_1, rule_2]
    errors, nonterms = validate(spec)
    assert len(errors) == 1
    assert errors[0] == makeDuplicateLhsError(spec[1])


def test_duplicate_resolved_name():
    alt_name = makeSyntacticRule(
        makeLine("<sentence>:Name ::= VERB"),
        makeLhsNonTerminal("sentence", "Name"),
        [makeTerminal("VERB")],
    )
    non_terminal_name = makeSyntacticRule(
        makeLine("<name> ::= WORD"),
        makeLhsNonTerminal("name"),
        [makeTerminal("WORD")],
    )
    spec = [alt_name, non_terminal_name]
    errors, nonterms = validate(spec)
    assert len(errors) == 1
    assert errors[0] == makeDuplicateLhsError(spec[1])


def validate(syntacticSpec: SyntacticSpec):
    return validate_lhs(syntacticSpec)


def makeSyntacticRule(line: Line, lhs: LhsNonTerminal, rhsList: List[Symbol]):
    return SyntacticRule(line, lhs, rhsList)


def makeLine(string, lineNumber=1, file=None):
    return Line(string, lineNumber, file)


def makeLhsNonTerminal(name: str | None, altName: str | None = None):
    return LhsNonTerminal(name, altName)


def makeTerminal(name: str | None):
    return Terminal(name)


def makeInvalidLhsNameFormatError(rule):
    return InvalidLhsNameError(rule)


def makeInvalidLhsAltNameFormatError(rule):
    return InvalidLhsAltNameError(rule)


def makeDuplicateLhsError(rule):
    return DuplicateLhsError(rule)
