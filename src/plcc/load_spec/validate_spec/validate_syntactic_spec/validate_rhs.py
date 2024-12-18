from ...parse_spec.parse_lexical_spec import LexicalSpec
from ...parse_spec.parse_syntactic_spec import SyntacticSpec, RhsNonTerminal, Terminal

from .errors import ValidationError, InvalidRhsNameError, InvalidRhsAltNameError, InvalidRhsTerminalError
import re


def validate_rhs(
    syntacticSpec: SyntacticSpec, lexicalSpec: LexicalSpec, nonTerminals: set()
):
    return SyntacticRhsValidator(syntacticSpec, lexicalSpec, nonTerminals).validate()


class SyntacticRhsValidator:
    spec: SyntacticSpec

    def __init__(
        self,
        syntacticSpec: SyntacticSpec,
        lexicalSpec: LexicalSpec,
        nonTerminals: set(),
    ):
        self.syntacticSpec = syntacticSpec
        self.lexicalSpec = lexicalSpec
        self.errorList = []
        self.nonTerminals = set()

    def validate(self):
        for rule in self.syntacticSpec:
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

    def _validateNonTerminalAltName(self, alt_name: str, rule):
        if not re.match(r"^[a-z][a-zA-Z0-9_]+$", alt_name):
            self._appendInvalidRhsAltNameError(rule)

    def _appendInvalidRhsError(self, rule):
        self.errorList.append(InvalidRhsNameError(rule))

    def _appendInvalidRhsAltNameError(self, rule):
        self.errorList.append(InvalidRhsAltNameError(rule))

    def _appendInvalidRhsTerminalError(self, rule):
        self.errorList.append(InvalidRhsTerminalError(rule))
