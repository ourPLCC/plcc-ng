from .structs import Token
from .LexError import LexError
from ..lines import Line
from .Skip import Skip
import json

class Formatter:
    def __init__(self):
        pass # Couldn't this just be a function like format()?

    def format(self, obj):
        if isinstance(obj, Token):
            return self._formatToken(obj)
        elif isinstance(obj, LexError):
            return self._formatLexError(obj)
        elif isinstance(obj, Skip):
            return self._formatSkip(obj)
        else:
            raise TypeError("Error: Can only format Tokens, Skips, or LexErrors.")

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
}}'''

    def _formatSkip(self, skip):
        return f'''
{{
  "Type": "Skip",
  "Name": "{skip.name}",
  "Lexeme": "{skip.lexeme}",
  "File": "{skip.line.file}",
  "Line": {skip.line.number},
  "Column": {skip.column}
}}
'''

