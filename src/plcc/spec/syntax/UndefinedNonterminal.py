from ..SpecError import SpecError

class UndefinedNonterminal(SpecError):
    def __init__(self, rule):
        super().__init__(line=rule.line, column=1,
            message="rule contains an RHS non-terminal not defined in any LHS rule")

    def __eq__(self, other):
        if not isinstance(other, UndefinedNonterminal):
            return False
        return (self.line == other.line and
                self.message == other.message and
                self.column == other.column)
