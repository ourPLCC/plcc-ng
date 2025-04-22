from .Skip import Skip
from .formatter import Formatter

class Sink:
    def __init__(self, printSkips):
        self.printSkips = printSkips
        self.formatter = Formatter()

    def write(self, obj):
        if not isinstance(obj, Skip) or self.printSkips:
            string = self.formatter.format(obj)
            print(string)
