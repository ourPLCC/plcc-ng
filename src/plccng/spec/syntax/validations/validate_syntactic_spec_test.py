from typing import List

from ...lexical import LexicalRule, LexicalSpec
from ....lines import Line
from ..LhsNonTerminal import LhsNonTerminal
from ..Symbol import Symbol
from ..SyntacticRule import SyntacticRule
from ..SyntacticSpec import SyntacticSpec
from ..Terminal import Terminal
from .validate_syntactic_spec import validate_syntactic_spec


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
    if ruleList is None:
        ruleList = []
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
