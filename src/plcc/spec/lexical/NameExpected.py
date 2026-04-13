from .LexicalSpecError import LexicalSpecError


class NameExpected(LexicalSpecError):
    def __init__(self, line, index=None, column=None):
        super().__init__(line=line, index=index, column=column,
            message='Names begin with capital or underscore and contain only capitals, numbers, and underscore.'
        )
