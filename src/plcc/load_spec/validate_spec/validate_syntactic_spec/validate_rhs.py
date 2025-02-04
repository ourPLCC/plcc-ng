from ...parse_spec.parse_syntactic_spec import (
    SyntacticSpec,
    RhsNonTerminal,
    Terminal,
)
from .errors import (
    InvalidRhsNameError,
    InvalidRhsAltNameError,
    InvalidRhsTerminalError,
    DuplicateRhsSymbolNameError,
)
import re


def validate_rhs(syntacticSpec: SyntacticSpec):
    return SyntacticRhsValidator(syntacticSpec).validate()


class SyntacticRhsValidator:
    spec: SyntacticSpec

    def __init__(
        self,
        syntacticSpec: SyntacticSpec
    ):
        self.syntacticSpec = syntacticSpec
        self.errorList = []

    def validate(self):
        for rule in self.syntacticSpec:
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

    def _validateNonTerminalAltName(self, altName: str, rule):
        if not re.match(r"^[a-z][a-zA-Z0-9_]+$", altName):
            self._appendInvalidRhsAltNameError(rule)

    def _validateNoDuplicateRhsSymbols(self, rule):
        seen = set()
        for symbol in rule.rhsSymbolList:
            if isinstance(symbol, Terminal):
                continue
            symbolName = symbol.getAttributeName()
            if symbolName in seen:
                self._appendDuplicateRhsSymbolNameError(rule, symbolName)
            else:
                seen.add(symbolName)

    def _appendInvalidRhsError(self, rule):
        self.errorList.append(InvalidRhsNameError(rule))

    def _appendInvalidRhsAltNameError(self, rule):
        self.errorList.append(InvalidRhsAltNameError(rule))

    def _appendInvalidRhsTerminalError(self, rule):
        self.errorList.append(InvalidRhsTerminalError(rule))

    def _appendDuplicateRhsSymbolNameError(self, rule, symbolName):
        self.errorList.append(DuplicateRhsSymbolNameError(rule, symbolName))
