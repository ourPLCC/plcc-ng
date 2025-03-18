import sys

from ..lines import Line


class Source:
    def __init__(self, files):
        self.files = files
        self.file_index = 0
        self.lines = []
        self.line_index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if not self._isFileValid():
            raise StopIteration

        if self.lines == []:
            self.lines = self._getLinesFromFile()
            self.line_index = 0

        if self.line_index >= len(self.lines):
            self.file_index += 1
            self.lines = []
            return next(self)

        line = self._makeLine()
        self.line_index += 1

        return line

    def _isFileValid(self):
        return self.files is not None and self.file_index < len(self.files)

    def _makeLine(self):
        return Line(
            self.lines[self.line_index].strip(),
            self.line_index + 1,
            self.files[self.file_index],
        )

    def _getLinesFromFile(self):
        return self._removeEmptyLines(self._getInput(self.files[self.file_index]))

    def _removeEmptyLines(self, lst):
        return [s for s in lst if s.strip()]

    def _getInput(self, name):
        return sys.stdin.readlines() if name == "-" else open(name, "r").readlines()
