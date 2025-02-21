from typing import List
from plccng.lines import Line
from plccng.spec.structs import LhsNonTerminal, RepeatingSyntacticRule, RhsNonTerminal, StandardSyntacticRule, Symbol
from plccng.spec.structs import (
    SyntacticSpec,
)


def replace_repeating_with_standard_rules(spec: SyntacticSpec):
    return SyntacticSpecResolver(SyntacticSpec(spec.copy())).resolve()


class SyntacticSpecResolver:
    oldSpec: SyntacticSpec
    newSpec: List

    def __init__(self, oldSpec: SyntacticSpec):
        self.oldSpec = oldSpec
        self.newSpec = list()

    def resolve(self):
        while len(self.oldSpec) > 0:
            self.rule = self.oldSpec.pop(0)
            self._resolveCurrent()
        return self.newSpec

    def _resolveCurrent(self):
        if isinstance(self.rule, RepeatingSyntacticRule):
            self._resolveRepeating()
        else:
            self.newSpec.append(self.rule)

    def _resolveRepeating(self):
        self._buildRhsString()
        self._resolveWithSep() if self.rule.separator else self._resolveWithoutSep()

    def _resolveWithoutSep(self):
        self._appendBaseRule()
        self._appendVoidRule()

    def _resolveWithSep(self):
        self.ntsep = self.rule.lhs.name + "#"

        self._appendSepBaseRule()
        self._appendVoidRule()
        self._appendNTSepRule()
        self._appendVoidNTSepRule()

    def _buildRhsString(self):
        names = [symbol.name for symbol in self.rule.rhsSymbolList]
        self.rhs_string = ", ".join(names)

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

    def _appendVoidRule(self):
        self._appendRule(
            line=f"<{self.rule.lhs.name}>:void ::=",
            lhs=self._makeLHS(self.rule.lhs.name, "void"),
            rhs=[],
        )

    def _appendNTSepRule(self):
        self._appendRule(
            line=f"<{self.ntsep}>:void ::= {self.rule.separator.name} {
                self.rhs_string} <{self.ntsep}>",
            lhs=self._makeLHS(self.ntsep, "void"),
            rhs=[self.rule.separator]
            + self.rule.rhsSymbolList
            + [self._makeRhsNonTerminal(self.ntsep)],
        )

    def _appendVoidNTSepRule(self):
        self._appendRule(
            line=f"<{self.ntsep}>:void ::=",
            lhs=self._makeLHS(self.ntsep, "void"),
            rhs=[],
        )

    def _appendRule(self, line: str, lhs: LhsNonTerminal, rhs: List[Symbol]):
        self.newSpec.append(StandardSyntacticRule(self._makeLine(line), lhs, rhs))

    def _makeLine(self, string, lineNumber=1, file=None):
        return Line(string, lineNumber, file)

    def _makeLHS(self, name: str, altName: str | None = None):
        return LhsNonTerminal(name, altName)

    def _makeRhsNonTerminal(self, name: str, altName: str | None = None):
        return RhsNonTerminal(name, altName)
