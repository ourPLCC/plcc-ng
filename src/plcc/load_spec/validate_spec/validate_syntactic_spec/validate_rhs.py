from ...parse_spec.parse_lexical_spec import LexicalSpec
from ...parse_spec.parse_syntactic_spec import (
    SyntacticSpec,
    RhsNonTerminal
)

from .errors  import ValidationError, InvalidRhsNameError
import re

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
        for rule in self.syntacticSpec:
            for s in rule.rhsSymbolList:
                if isinstance(s, RhsNonTerminal):
                    self._validateNonTerminal(s, rule)

        return self.errorList

    def _validateNonTerminal(self, s, rule):
        print("world!")
        if not re.match(r"^[a-z][a-zA-Z0-9_]+$", s.name):
            self._appendInvalidRhsAltNameError(rule)
            print("hello!")

    def _appendInvalidRhsAltNameError(self, rule):
        self.errorList.append(InvalidRhsNameError(rule))

