from ..SpecError import SpecError

class InvalidLhsNameError(SpecError):
    def __init__(self, rule):
        super().__init__(line=rule.line, column=1,
            message=f"invalid LHS name '{rule.lhs.name}' — must start with an uppercase letter followed by letters, digits, or underscores")

    def __eq__(self, other):
        if not isinstance(other, InvalidLhsNameError):
            return False
        return (self.line == other.line and
                self.message == other.message and
                self.column == other.column)
