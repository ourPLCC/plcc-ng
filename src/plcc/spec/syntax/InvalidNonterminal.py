from ..SpecError import SpecError

class InvalidNonterminal(SpecError):
    def __init__(self, rule):
        super().__init__(line=rule.line, column=1,
            message="invalid RHS non-terminal name — must start with a lowercase letter followed by letters, digits, or underscores")

    def __eq__(self, other):
        if not isinstance(other, InvalidNonterminal):
            return False
        return (self.line == other.line and
                self.message == other.message and
                self.column == other.column)
