from dataclasses import dataclass

@dataclass(frozen=True)
class Line:
    string: str
    number: int
    file: str = None

class Source:
    def __init__(self, files):
        self.files = files
        self.index = 0
        self.lines = []
        self.line_index = 0
        if files is not None:
            self._readLines()


    def __iter__(self):
        return self

    def __next__(self):
        if self.index >= len(self.lines):
            raise StopIteration
        value = self.lines[self.index]
        self.index += 1
        return value

    def _readLines(self):
        for fname in self.files:
            with open(fname, 'r') as file:
                for line in file:
                    if line.strip():
                        self.line_index += 1
                        self.lines.append(Line(line.strip(), self.line_index, file.name))
            self.line_index = 0

