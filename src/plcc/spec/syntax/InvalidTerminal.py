from ..SpecError import SpecError

class InvalidTerminal(SpecError):
    def __init__(self, rule):
        super().__init__(line=rule.line, column=1,
            message="invalid RHS terminal name — must be all uppercase letters, digits, and underscores, and cannot start with a digit")

    def __eq__(self, other):
        if not isinstance(other, InvalidTerminal):
            return False
        return (self.line == other.line and
                self.message == other.message and
                self.column == other.column)
