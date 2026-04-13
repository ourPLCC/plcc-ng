from .LexError import LexError
from .Skip import Skip
from .Token import Token


def format(obj):
    return Formatter().format(obj)


class Formatter:
    def __init__(self):
        pass

    def format(self, obj):
        if isinstance(obj, Token):
            return self._formatToken(obj)
        elif isinstance(obj, LexError):
            return self._formatLexError(obj)
        elif isinstance(obj, Skip):
            return self._formatSkip(obj)
        else:
            raise TypeError(f"Unrecognized type: {type(obj)}")

    def _formatToken(self, token):
        return f"""{token.line.file}:{token.line.number}:{token.column}:Token {token.name} '{token.lexeme}'"""

    def _formatSkip(self, skip):
        return f"""{skip.line.file}:{skip.line.number}:{skip.column}:Skip {skip.name} '{skip.lexeme}'"""

    def _formatLexError(self, lexError):
        return str(lexError)
