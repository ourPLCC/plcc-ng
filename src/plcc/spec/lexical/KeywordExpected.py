from .LexicalSpecError import LexicalSpecError


class KeywordExpected(LexicalSpecError):
    def __init__(self, line, index=None, column=None):
        super().__init__(line=line, index=index, column=column,
            message="Expected 'token' or 'skip'."
        )
