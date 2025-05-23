import re

from ..CapturingSymbol import CapturingSymbol
from ..DuplicateAttribute import DuplicateAttribute
from ..InvalidAttribute import InvalidAttribute
from ..InvalidNonterminal import InvalidNonterminal
from ..InvalidSeparator import InvalidSeparator
from ..InvalidTerminal import InvalidTerminal
from ..RepeatingSyntacticRule import RepeatingSyntacticRule
from ..RhsNonTerminal import RhsNonTerminal
from ..SyntacticSpec import SyntacticSpec
from ..Terminal import Terminal
from ..UndefinedNonterminal import UndefinedNonterminal


def validate_rhs(syntacticSpec: SyntacticSpec):
    return SyntacticRhsValidator(syntacticSpec).validate()


class SyntacticRhsValidator:
    spec: SyntacticSpec

    def __init__(
        self,
        syntacticSpec: SyntacticSpec
    ):
        self.syntacticSpec = syntacticSpec
        self._nonTerminalSet = None
        self.errorList = []

    def validate(self):
        for rule in self.syntacticSpec:
            if isinstance(rule, RepeatingSyntacticRule):
                self._validateSeparatorIsTerminal(rule)
            for s in rule.rhsSymbolList:
                if isinstance(s, RhsNonTerminal):
                    self._validateNonTerminal(s, rule)
                if isinstance(s, Terminal):
                    self._validateTerminal(s, rule)
            self._validateNoDuplicateRhsSymbols(rule)
        return self.errorList

    def _validateTerminal(self, s, rule):
        if not re.match(r"^[A-Z][A-Z0-9_]+$", s.name):
            self._appendInvalidRhsTerminalError(rule)

    def _validateNonTerminal(self, s, rule):
        if s.altName:
            self._validateNonTerminalAltName(s.altName, rule)
        if not re.match(r"^[a-z][a-zA-Z0-9_]+$", s.name):
            self._appendInvalidRhsError(rule)
        if not self._nonTerminalExists(s):
            self._appendMissingNonTerminalError(rule)

    def _nonTerminalExists(self, non_terminal):
        return non_terminal.name in self._getNonTerminals()

    def _getNonTerminals(self):
        if self._nonTerminalSet is None:
            self._nonTerminalSet = set()
            for rule in self.syntacticSpec:
                self._nonTerminalSet.add(rule.lhs.name)
        return self._nonTerminalSet

    def _validateNonTerminalAltName(self, altName: str, rule):
        if not re.match(r"^[a-z][a-zA-Z0-9_]+$", altName):
            self._appendInvalidRhsAltNameError(rule)

    def _validateNoDuplicateRhsSymbols(self, rule):
        seen = set()
        for symbol in rule.rhsSymbolList:
            if isinstance(symbol, CapturingSymbol):
                symbolName = symbol.getAttributeName()
                if symbolName in seen:
                    self._appendDuplicateRhsSymbolNameError(rule, symbolName)
                else:
                    seen.add(symbolName)

    def _validateSeparatorIsTerminal(self, rule):
        if not re.match(r"^[A-Z][A-Z0-9_]+$", rule.separator.name):
            self._appendInvalidRhsSeparatorTypeError(rule)

    def _appendInvalidRhsSeparatorTypeError(self, rule):
        self.errorList.append(InvalidSeparator(rule))

    def _appendInvalidRhsError(self, rule):
        self.errorList.append(InvalidNonterminal(rule))

    def _appendInvalidRhsAltNameError(self, rule):
        self.errorList.append(InvalidAttribute(rule))

    def _appendInvalidRhsTerminalError(self, rule):
        self.errorList.append(InvalidTerminal(rule))

    def _appendDuplicateRhsSymbolNameError(self, rule, symbolName):
        self.errorList.append(DuplicateAttribute(rule, symbolName))

    def _appendMissingNonTerminalError(self, rule):
        self.errorList.append(UndefinedNonterminal(rule))
