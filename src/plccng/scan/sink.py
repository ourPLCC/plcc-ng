from .formatter import format
from .Skip import Skip


class Sink:
    def __init__(self, printSkips):
        self.printSkips = printSkips

    def write(self, obj):
        if not isinstance(obj, Skip) or self.printSkips:
            string = format(obj)
            print(string, flush=True)
