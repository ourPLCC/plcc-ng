
from .formatter import Formatter

class Sink:
    def __init__(self, tokensSkipsOrLexErrors):
        formatter = Formatter()
        self.strings = formatter.format(tokensSkipsOrLexErrors)

    def write(self):
        print(next(self.strings))


