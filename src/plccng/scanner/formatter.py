
from .structs import Token
from .Skip import Skip
from .LexError import LexError
from ..lines import Line

class Formatter:
    def __init__(self, tokensSkipsOrLexErrors):
        self.tokensSkipsOrLexErrors = tokensSkipsOrLexErrors
        self.json = "["

    def format(self):
        for obj in self.tokensSkipsOrLexErrors:
            self._formatAccordingToType(obj)

        return self.json + "\n]"

    def _formatAccordingToType(self, obj):
        if isinstance(obj, Token):
            self._formatToken(obj)
        elif isinstance(obj, Skip):
            self._formatSkip(obj)
        elif isinstance(obj, LexError):
            self._formatLexError(obj)

    def _formatToken(self, token):
        self.json += f'''
\t{{
\t\t"Type": "Token",
\t\t"Name": "{token.name}",
\t\t"Lexeme": "{token.lexeme}",
\t\t"Line": {token.line.number},
\t\t"Column": {token.column}
\t}},
'''

    def _formatSkip(self, skip):
        self.json += f'''
\t{{
\t\t"Type": "Skip",
\t\t"Name": "{skip.name}",
\t\t"Lexeme": "{skip.lexeme}",
\t\t"Column": {skip.column}
\t}},
'''

    def _formatLexError(self, lexError):
        self.json += f'''
\t{{
\t\t"Type": "LexError",
\t\t"Line": "{lexError.line.string}",
\t\t"Column": {lexError.column}
\t}},'''


