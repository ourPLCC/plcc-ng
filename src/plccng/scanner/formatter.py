
from .structs import Token
from .Skip import Skip
from .LexError import LexError
from ..lines import Line

class Formatter:
    def __init__(self):
        self.json = ''

    def format(self, tokensSkipsOrLexErrors):

        for obj in tokensSkipsOrLexErrors:
            yield self._formatAccordingToType(obj)

    def _formatAccordingToType(self, obj):
        if isinstance(obj, Token):
            return self._formatToken(obj)
        elif isinstance(obj, Skip):
            return self._formatSkip(obj)
        elif isinstance(obj, LexError):
            return self._formatLexError(obj)

    def _formatToken(self, token):
        return f'''
{{
  "Type": "Token",
  "Name": "{token.name}",
  "Lexeme": "{token.lexeme}",
  "Line": {token.line.number},
  "Column": {token.column}
}}
'''

    def _formatSkip(self, skip):
        return f'''
{{
  "Type": "Skip",
  "Name": "{skip.name}",
  "Lexeme": "{skip.lexeme}",
  "Column": {skip.column}
}}
'''

    def _formatLexError(self, lexError):
        return f'''
{{
  "Type": "LexError",
  "Line": {lexError.line.number},
  "Column": {lexError.column}
}}
'''


