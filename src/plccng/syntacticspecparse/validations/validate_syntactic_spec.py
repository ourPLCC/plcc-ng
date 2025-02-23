from plccng.lexicalspecparse import LexicalSpec

from ..SyntacticSpec import SyntacticSpec
from ..SyntacticRule import SyntacticRule
from .validate_lhs import validate_lhs
from .validate_rhs import validate_rhs
from .validate_terminals_defined import validate_terminals_defined


def validate_syntactic_spec(syntacticSpec: SyntacticSpec, lexicalSpec: LexicalSpec):
    return SyntacticValidator(syntacticSpec, lexicalSpec).validate()


class SyntacticValidator:
    lexicalSpec: LexicalSpec
    syntacticSpec: SyntacticSpec
    rule: SyntacticRule

    def __init__(self, syntacticSpec: SyntacticSpec, lexicalSpec: LexicalSpec):
        self.syntacticSpec = syntacticSpec
        self.lexicalSpec = lexicalSpec
        self.errorList = []

    def validate(self) -> list:
        self._validateLhs()
        self._validateRhs()
        self._validateTerminalsDefined()
        return self.errorList

    def _validateLhs(self):
        lhs_error_list, non_terminal_set = validate_lhs(self.syntacticSpec)
        self.errorList = lhs_error_list

    def _validateRhs(self):
        Rhs_error_list= validate_rhs(self.syntacticSpec)
        self.errorList.extend(Rhs_error_list)

    def _validateTerminalsDefined(self):
        self.errorList.extend(validate_terminals_defined(self.syntacticSpec, self.lexicalSpec))
