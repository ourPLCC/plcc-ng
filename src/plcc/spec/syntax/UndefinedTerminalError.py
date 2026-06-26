from ..SpecError import SpecError

class UndefinedTerminalError(SpecError):
    def __init__(self, rule):
        super().__init__(line=rule.line, column=1,
            message="RHS terminal is not defined in the lexical section")

    def __eq__(self, other):
        if not isinstance(other, UndefinedTerminalError):
            return False
        return (self.line == other.line and
                self.message == other.message and
                self.column == other.column)
