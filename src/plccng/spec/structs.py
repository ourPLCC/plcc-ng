from __future__ import annotations
from dataclasses import dataclass

from plccng.lineparse import Line
from plccng.roughparse.structs import Block


@dataclass
class LexicalSpec:
    ruleList: list[LexicalRule|Line]


@dataclass
class LexicalRule:
    line: Line
    isSkip: bool
    name: str
    pattern: str


@dataclass
class SemanticSpec:
    language: str
    tool: str
    codeFragmentList: list[CodeFragment]


@dataclass
class TargetLocator:
    line: Line
    className: str
    modifier: str = None


@dataclass
class CodeFragment:
    targetLocator: TargetLocator
    block: Block


@dataclass(frozen=True)
class Symbol:
    name: str | None
    pass


@dataclass(frozen=True)
class Terminal(Symbol):
    pass


@dataclass(frozen=True)
class CapturingSymbol:
    altName: str | None = None
    pass

    def getAttributeName(self):
        if self.altName == None:
            return self.name.lower()
        else:
            return self.altName.lower()


@dataclass(frozen=True)
class CapturingTerminal(CapturingSymbol, Terminal):
    pass


@dataclass(frozen=True)
class NonTerminal(Symbol):
    pass


@dataclass(frozen=True)
class LhsNonTerminal(NonTerminal):
    altName: str | None = None
    pass


@dataclass(frozen=True)
class RhsNonTerminal(CapturingSymbol, NonTerminal):
    pass


@dataclass(frozen=True)
class SyntacticRule:
    line: Line
    lhs: LhsNonTerminal
    rhsSymbolList: list[Symbol]
    pass


@dataclass(frozen=True)
class StandardSyntacticRule(SyntacticRule):
    pass


@dataclass(frozen=True)
class RepeatingSyntacticRule(SyntacticRule):
    separator: Terminal | None = None
    pass


@dataclass
class SyntacticSpec(list):
    nonTerminals: set[str]
    def __init__(self, rules=None ):
        if rules: super().__init__(rules)
        self.nonTerminals = set()

    def getNonTerminals(self):
        if len(self.nonTerminals) > 0:
            return self.nonTerminals
        for rule in self:
            self.nonTerminals.add(rule.lhs.name)
        return self.nonTerminals
    pass

