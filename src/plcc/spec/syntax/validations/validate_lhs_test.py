from typing import List

from ....lines import Line
from ..DuplicateLhsError import DuplicateLhsError
from ..InvalidLhsAltNameError import InvalidLhsAltNameError
from ..InvalidLhsNameError import InvalidLhsNameError
from ..LhsNonTerminal import LhsNonTerminal
from ..Symbol import Symbol
from ..SyntacticRule import SyntacticRule
from ..SyntacticSpec import SyntacticSpec
from ..Terminal import Terminal
from .validate_lhs import validate_lhs


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
