from ..SpecError import SpecError

class DuplicateLhsError(SpecError):
    def __init__(self, rule):
        super().__init__(line=rule.line, column=1,
            message=f"duplicate LHS name '{rule.lhs.name}'")

    def __eq__(self, other):
        if not isinstance(other, DuplicateLhsError):
            return False
        return (self.line == other.line and
                self.message == other.message and
                self.column == other.column)
