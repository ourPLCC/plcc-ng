
from .structs import Token
from .Skip import Skip
from .LexError import LexError
from ..lines import Line

class Formatter:
    def __init__(self):
        self.json = ''

    def format(self, tokensSkipsOrLexErrors):

        for obj in tokensSkipsOrLexErrors:
            self._formatAccordingToType(obj)

        return self.json

    def _formatAccordingToType(self, obj):
        if isinstance(obj, Token):
            self._formatToken(obj)
        elif isinstance(obj, Skip):
            self._formatSkip(obj)
        elif isinstance(obj, LexError):
            self._formatLexError(obj)

    def _formatToken(self, token):
        self.json += f'''
{{
  "Type": "Token",
  "Name": "{token.name}",
  "Lexeme": "{token.lexeme}",
  "Line": {token.line.number},
  "Column": {token.column}
}}
'''

    def _formatSkip(self, skip):
        self.json += f'''
{{
  "Type": "Skip",
  "Name": "{skip.name}",
  "Lexeme": "{skip.lexeme}",
  "Column": {skip.column}
}}
'''

    def _formatLexError(self, lexError):
        self.json += f'''
{{
  "Type": "LexError",
  "Line": "{lexError.line.string}",
  "Column": {lexError.column}
}}
'''


