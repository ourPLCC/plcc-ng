from .LexicalSpecError import LexicalSpecError


class PatternDelimiterExpected(LexicalSpecError):
    def __init__(self, line=None, column=None, index=None, delimiter=None):
        super().__init__(line=line, column=column, index=index, message=f"Expected delimiter: {delimiter}")
