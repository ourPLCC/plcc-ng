from typing import List

from ...LhsNonTerminal import LhsNonTerminal

from ...Terminal import Terminal

from ...Symbol import Symbol

from plccng.lexicalspecparse.LexicalRule import LexicalRule
from plccng.lexicalspecparse.LexicalSpec import LexicalSpec

from ....lineparse.Line import Line
from ...SyntacticRule import SyntacticRule
from .validate_syntactic_spec import validate_syntactic_spec
from ...SyntacticSpec import (
    SyntacticSpec,
)


def test_empty_no_errors():
    syntacticSpec = makeSyntacticSpec([])
    errors = validate(syntacticSpec)
    assert len(errors) == 0


def test_None_no_errors():
    syntacticSpec = makeSyntacticSpec(None)
    errors = validate(syntacticSpec)
    assert len(errors) == 0


def test_simple_valid_spec():
    lexSpec = makeLexicalSpec([makeLexicalRule('ONE', 'ONE')])
    synSpec = makeSyntacticSpec([
        makeSyntacticRule(
            makeLine('<one> ::= ONE'),
            makeLhsNonTerminal('one'),
            [Terminal('ONE')]
        )
    ])
    errors = validate(synSpec, lexSpec)
    assert len(errors) == 0


def validate(syntacticSpec: SyntacticSpec, lexicalSpec: LexicalSpec = []):
    return validate_syntactic_spec(syntacticSpec, lexicalSpec)


def makeSyntacticSpec(ruleList=None):
    return SyntacticSpec(ruleList)


def makeSyntacticRule(line: Line, lhs: LhsNonTerminal, rhsList: List[Symbol]):
    return SyntacticRule(line, lhs, rhsList)

def makeLexicalSpec(ruleList=None):
    return LexicalSpec(ruleList)

def makeLexicalRule(name='TEST', pattern='TEST'):
    return LexicalRule(makeLine('TEST'), False, name, pattern)

def makeLine(string, lineNumber=1, file=None):
    return Line(string, lineNumber, file)


def makeLhsNonTerminal(name: str | None, altName: str | None = None):
    return LhsNonTerminal(name, altName)
