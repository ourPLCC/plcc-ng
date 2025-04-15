
from .structs import Token
from .Skip import Skip
from .LexError import LexError
from ..lines import Line
from .formatter import Formatter

class Sink:
    def __init__(self):
        self.formatter = Formatter()


    def write(self, tokensSkipsOrLexErrors):
        print(self.formatter.format(tokensSkipsOrLexErrors))

