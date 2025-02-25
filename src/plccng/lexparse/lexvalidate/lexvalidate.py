from ..LexicalSpec import LexicalSpec

from .NameValidator import NameValidator
from .UniqueNameValidator import UniqueNameValidator
from .PatternValidator import PatternValidator
from .UnrecognizedLineValidator import UnrecognizedLineValidator

def lexvalidate(lexicalSpec: LexicalSpec):
    return LexicalValidator(lexicalSpec).validate()

class LexicalValidator:
    def __init__(self, lexicalSpec: LexicalSpec):
        self.lexicalSpec = lexicalSpec
        self.errorList = []
        self.validators = [
            UniqueNameValidator(),
            NameValidator(),
            PatternValidator(),
            UnrecognizedLineValidator(),
        ]

    def validate(self) -> list:
        if not self.lexicalSpec.ruleList:
            return []
        for rule in self.lexicalSpec.ruleList:
            self._runValidators(rule)
        return self.errorList

    def _runValidators(self, rule_or_line):
        for v in self.validators:
            e = v.check(rule_or_line)
            if e:
                self.errorList.append(e)
