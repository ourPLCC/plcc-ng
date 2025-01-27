from ...parse_spec.parse_syntactic_spec import (
    SyntacticSpec,
    RhsNonTerminal,
    Terminal,
)
from .errors import (
    InvalidRhsNameError,
    InvalidRhsAltNameError,
    InvalidRhsTerminalError,
    RepeatRhsSymbolNameError,
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
            self._validateNoRepeatRhsSymbols(rule)
        return self.errorList

    def _validateTerminal(self, s, rule):
        if not re.match(r"^[A-Z][A-Z0-9_]+$", s.name):
            self._appendInvalidRhsTerminalError(rule)

    def _validateNonTerminal(self, s, rule):
        if s.altName:
            self._validateNonTerminalAltName(s.altName, rule)
        if not re.match(r"^[a-z][a-zA-Z0-9_]+$", s.name):
            self._appendInvalidRhsError(rule)

    def _validateNonTerminalAltName(self, alt_name: str, rule):
        if not re.match(r"^[a-z][a-zA-Z0-9_]+$", alt_name):
            self._appendInvalidRhsAltNameError(rule)

    def _validateNoRepeatRhsSymbols(self, rule):
        seen = []
        print(rule.rhsSymbolList)
        for symbol in rule.rhsSymbolList:
            for seenSymbol in seen:
                if self._compareSymbolsNames(seenSymbol, symbol):
                    self._appendRepeatRhsSymbolNameError(rule)
            else:
                seen.append(symbol)
                print(seen)

    def _compareSymbolsNames(self, seenSymbol, symbol):
        if seenSymbol.name == symbol.name:
            return True
        else:
            return False


    def _appendInvalidRhsError(self, rule):
        self.errorList.append(InvalidRhsNameError(rule))

    def _appendInvalidRhsAltNameError(self, rule):
        self.errorList.append(InvalidRhsAltNameError(rule))

    def _appendInvalidRhsTerminalError(self, rule):
        self.errorList.append(InvalidRhsTerminalError(rule))

    def _appendRepeatRhsSymbolNameError(self, rule):
        self.errorList.append(RepeatRhsSymbolNameError(rule))
