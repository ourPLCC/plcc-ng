from ..SpecError import SpecError

class InvalidLhsAltNameError(SpecError):
    def __init__(self, rule):
        super().__init__(line=rule.line, column=1,
            message=f"invalid LHS alternate name '{rule.lhs.altName}' — must start with an uppercase letter followed by letters, digits, or underscores")

    def __eq__(self, other):
        if not isinstance(other, InvalidLhsAltNameError):
            return False
        return (self.line == other.line and
                self.message == other.message and
                self.column == other.column)
