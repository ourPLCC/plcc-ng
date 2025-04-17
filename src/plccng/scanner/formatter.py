from .structs import Token
from .LexError import LexError
from ..lines import Line
from .Skip import Skip
import json

class Formatter:
    def __init__(self, yieldSkips=False):
        self.yieldSkips = yieldSkips

    def format(self, tokensSkipsOrLexErrors):
        for obj in tokensSkipsOrLexErrors:
            string = self._formatAccordingToType(obj)
            if string:
                yield string

    def _formatAccordingToType(self, obj):
        if isinstance(obj, Token):
            return self._formatToken(obj)
        elif isinstance(obj, LexError):
            return self._formatLexError(obj)
        elif isinstance(obj, Skip) and self.yieldSkips:
            return self._formatSkip(obj)

    def _formatToken(self, token):
        return json.dumps({
"Type": "Token",
"Name": token.name,
"Lexeme": token.lexeme,
"File": token.line.file,
"Line": token.line.number,
"Column": token.column
}, sort_keys=True, indent=2)

    def _formatLexError(self, lexError):
        return json.dumps({
"Type": "LexError",
"File": lexError.line.file,
"Line": lexError.line.number,
"Column": lexError.column
}, sort_keys=True, indent=2)


    def _formatSkip(self, skip):
        return json.dumps(
{
"Type": "Skip",
"Name": skip.name,
"Lexeme": skip.lexeme,
"Column": skip.column
}, sort_keys=True, indent=2)

