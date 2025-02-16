import sys
from ..load_spec.structs import Line

class Source:
    def __init__(self, files):
        self.files = files
        self.line_index = 0
        self.FileReader = iter(FileReader(files))

    def __iter__(self):
        return self.FileReader

    def __next__(self):
        return next(self.FileReader)

class FileReader:
    def __init__(self, files):
        self.files = files
        self.line_index = 0

    def __iter__(self):
        if not self.files:
            return []
        for name in self.files:
            yield from self._readLines(self._getInput(name), name)

    def _getInput(self, name):
        return sys.stdin.readlines() if name == "-" else open(name, 'r')

    def _readLines(self, input, name):
        for line in input:
            if line.strip():
                self.line_index += 1
                yield Line(line.strip(), self.line_index, name)
        self.line_index = 0
