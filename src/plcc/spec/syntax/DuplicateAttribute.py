from ..SpecError import SpecError

class DuplicateAttribute(SpecError):
    def __init__(self, rule, symbolName):
        super().__init__(line=rule.line, column=1,
            message=f"duplicate RHS symbol name '{symbolName}' — all capturing RHS symbols must have unique names")

    def __eq__(self, other):
        if not isinstance(other, DuplicateAttribute):
            return False
        return (self.line == other.line and
                self.message == other.message and
                self.column == other.column)
