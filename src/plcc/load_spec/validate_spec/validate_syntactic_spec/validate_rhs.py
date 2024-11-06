from ...parse_spec.parse_lexical_spec import LexicalSpec
from ...parse_spec.parse_syntactic_spec import (
    SyntacticSpec,
    RhsNonTerminal
)

from .errors import ValidationError


def validate_rhs(syntacticSpec: SyntacticSpec, lexicalSpec: LexicalSpec, nonTerminals: set()):
    return SyntacticRhsValidator(syntacticSpec, lexicalSpec, nonTerminals).validate()


class SyntacticRhsValidator:
    spec: SyntacticSpec

    def __init__(self, syntacticSpec: SyntacticSpec, lexicalSpec: LexicalSpec, nonTerminals: set()):
        self.syntacticSpec = syntacticSpec
        self.lexicalSpec = lexicalSpec
        self.errorList = []
        self.nonTerminals = set()

    def validate(self):
        self._validateNonTerminals()
        for rule in self.syntacticSpec:
            for s in rule.rhsSymbolList:
                if isinstance(s, RhsNonTerminal):
                    self._validateNonTerminal(s)

        pass

    def _validateNonTerminal(self, s):
        pass
