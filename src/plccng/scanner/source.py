from dataclasses import dataclass
import sys

@dataclass(frozen=True)
class Line:
    string: str
    number: int
    file: str = None

class Source:
    def __init__(self, files):
        self.files = files
        self.line_index = 0

    def __iter__(self):
        if self.files == None:
            return None
        yield from self._readAll()

    def _readAll(self):
        for name in self.files:
            yield from self._readLines(sys.stdin.readlines(), name) if name == "-" else self._readLines(open(name, 'r'), name)
            self.line_index = 0

    def _readLines(self, input, name):
        for line in input:
            if line.strip():
                self.line_index += 1
                yield Line(line.strip(), self.line_index, name)
        self.line_index = 0

