from ...errors import InvalidRhsAltNameError, InvalidRhsNameError, InvalidRhsTerminalError, MissingNonTerminalError
from ...structs import RepeatingSyntacticRule, RhsNonTerminal, Terminal
from ...structs import (
    SyntacticSpec
)
from ...errors import (
    InvalidRhsSeparatorTypeError
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
            if isinstance(rule, RepeatingSyntacticRule):
                self._validateSeparatorIsTerminal(rule)
            for s in rule.rhsSymbolList:
                if isinstance(s, RhsNonTerminal):
                    self._validateNonTerminal(s, rule)
                if isinstance(s, Terminal):
                    self._validateTerminal(s, rule)
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
        return non_terminal.name in self.syntacticSpec.nonTerminals

    def _validateNonTerminalAltName(self, alt_name: str, rule):
        if not re.match(r"^[a-z][a-zA-Z0-9_]+$", alt_name):
            self._appendInvalidRhsAltNameError(rule)

    def _validateSeparatorIsTerminal(self, rule):
        if not isinstance(rule.separator, Terminal):
            self._appendInvalidRhsSeparatorTypeError(rule)

    def _appendInvalidRhsSeparatorTypeError(self, rule):
        self.errorList.append(InvalidRhsSeparatorTypeError(rule))

    def _appendInvalidRhsError(self, rule):
        self.errorList.append(InvalidRhsNameError(rule))

    def _appendInvalidRhsAltNameError(self, rule):
        self.errorList.append(InvalidRhsAltNameError(rule))

    def _appendInvalidRhsTerminalError(self, rule):
        self.errorList.append(InvalidRhsTerminalError(rule))

    def _appendMissingNonTerminalError(self, rule):
        self.errorList.append(MissingNonTerminalError(rule))
