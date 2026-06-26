from ..SpecError import SpecError

class InvalidSeparator(SpecError):
    def __init__(self, rule):
        super().__init__(line=rule.line, column=1,
            message="repeating rule separator must be a terminal (all-uppercase)")

    def __eq__(self, other):
        if not isinstance(other, InvalidSeparator):
            return False
        return (self.line == other.line and
                self.message == other.message and
                self.column == other.column)
