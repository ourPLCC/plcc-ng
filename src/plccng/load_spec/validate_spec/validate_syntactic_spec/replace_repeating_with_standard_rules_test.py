from pytest import raises, mark, fixture
from typing import List

from plccng.load_spec.structs import (
    RepeatingSyntacticRule,
)
from plccng.load_spec.structs import CapturingTerminal, LhsNonTerminal, RhsNonTerminal, StandardSyntacticRule

from ...structs import Line, Symbol, Terminal
from ...structs import (
    SyntacticSpec,
)
from .replace_repeating_with_standard_rules import replace_repeating_with_standard_rules


def test_standard_unaffected():
    rule_1 = makeStandardSyntacticRule(
        "sentence",
        [makeTerminal("VERB")],
    )
    rule_2 = makeStandardSyntacticRule(
        "name",
        [makeTerminal("WORD")],
    )

    oldSpec = [rule_1, rule_2]
    newSpec = replace_repeating_with_standard_rules(SyntacticSpec(oldSpec))
    assert oldSpec == newSpec


def test_no_separator():
    rule_1 = makeStandardSyntacticRule("sentence", [makeTerminal("VERB")])
    rule_2 = makeRepeatingSyntacticRule(
        "name",
        [makeTerminal("WORD")],
    )
    expectedSpec = [
        rule_1,
        makeStandardSyntacticRule(
            "name",
            [makeTerminal("WORD"), makeRhsNonTerminal("name")],
        ),
        makeStandardSyntacticRule("name:void", []),
    ]

    oldSpec = [rule_1, rule_2]
    resolvedSpec = replace_repeating_with_standard_rules(SyntacticSpec(oldSpec))
    assert resolvedSpec == expectedSpec


def test_with_separator():
    rule_1 = makeStandardSyntacticRule(
        "sentence",
        [makeTerminal("VERB")],
    )
    rule_2 = makeRepeatingSyntacticRule(
        "name",
        [makeTerminal("WORD")],
        separator=Terminal("SEP"),
    )

    expectedSpec = [
        rule_1,
        makeStandardSyntacticRule(
            "name",
            [makeTerminal("WORD"), makeRhsNonTerminal("name#")],
        ),
        makeStandardSyntacticRule("name:void", []),
        makeStandardSyntacticRule(
            "name#:void",
            [makeTerminal("SEP"), makeTerminal("WORD"), makeRhsNonTerminal("name#")],
        ),
        makeStandardSyntacticRule("name#:void", []),
    ]

    oldSpec = [rule_1, rule_2]
    resolvedSpec = replace_repeating_with_standard_rules(SyntacticSpec(oldSpec))
    assert resolvedSpec == expectedSpec


def makeStandardSyntacticRule(lhs: str, rhsList: List[Symbol]):
    return StandardSyntacticRule(
        buildLineStandard(lhs, rhsList), makeLhsNonTerminal(lhs), rhsList
    )


def makeRepeatingSyntacticRule(lhs: str, rhsList: List[Symbol], separator=None):
    return RepeatingSyntacticRule(
        buildLineRepeating(lhs, rhsList, separator),
        makeLhsNonTerminal(lhs),
        rhsList,
        separator,
    )


def buildLineStandard(lhs, rhs):
    if lhs.__contains__(":"):
        return makeLine(f"<{lhs.split(":")[0]}>:{lhs.split(":")[1]} ::={buildRhs(rhs)}")
    return makeLine(f"<{lhs}> ::={buildRhs(rhs)}")


def buildLineRepeating(lhs, rhs, sep=None):
    if sep:
        return makeLine(f"{lhs} **={buildRhs(rhs)} +{sep.name}")
    return makeLine(f"{lhs} **={buildRhs(rhs)}")


def makeLine(string, lineNumber=1, file=None):
    return Line(string, lineNumber, file)


def buildRhs(rhs):
    s = ""
    for symbol in rhs:
        if isinstance(symbol, RhsNonTerminal) or isinstance(symbol, CapturingTerminal):
            s += stringifyCapturing(symbol)
            break
        s += " " + symbol.name
    return s


def stringifyCapturing(symbol):
    return f" <{symbol.name}>"


def makeLhsNonTerminal(lhs: str):
    if lhs.__contains__(":"):
        return LhsNonTerminal(lhs.split(":")[0], lhs.split(":")[1])
    return LhsNonTerminal(lhs)


def makeTerminal(name: str | None):
    return Terminal(name)


def makeRhsNonTerminal(name: str):
    return RhsNonTerminal(name)
