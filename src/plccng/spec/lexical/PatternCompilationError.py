from .LexicalSpecError import LexicalSpecError


class PatternCompilationError(LexicalSpecError):
    def __init__(self, line, column=None, index=None, error=None):
        super().__init__(line=line, column=column, index=index, message=f"{error}")
