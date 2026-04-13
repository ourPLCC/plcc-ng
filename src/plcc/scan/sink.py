from .Skip import Skip
from .json_formatter import format


class Sink:
    def __init__(self, printSkips, format_fn=format):
        self.printSkips = printSkips
        self.format = format_fn

    def write(self, obj):
        if not isinstance(obj, Skip) or self.printSkips:
            string = self.format(obj)
            print(string, flush=True)
