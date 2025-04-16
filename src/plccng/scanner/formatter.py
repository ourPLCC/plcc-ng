from .structs import Token
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
        elif isinstance(obj, LexError):
            return self._formatLexError(obj)

    def _formatToken(self, token):
        return f'''
{{
  "Type": "Token",
  "Name": "{token.name}",
  "Lexeme": "{token.lexeme}",
  "File": "{token.line.file}",
  "Line": {token.line.number},
  "Column": {token.column}
}}
'''

    def _formatLexError(self, lexError):
        return f'''
{{
  "Type": "LexError",
  "File": "{lexError.line.file}",
  "Line": {lexError.line.number},
  "Column": {lexError.column}
}}
'''


