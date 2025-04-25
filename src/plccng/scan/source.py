import sys

from ..lines import Line


def Source(files):
    if files is None:
        return iter([])
    for file in files:
        yield from _yieldLinesFromFile(file)


def _yieldLinesFromFile(file):
    if file == '-':
        yield from _yieldLines(sys.stdin, file)
    else:
        with open(file, 'r') as f:
            yield from _yieldLines(f, file)


def _yieldLines(inf, file):
    lineNumber = 1
    for line in inf:
        yield Line(string=line.strip(), number=lineNumber, file=file)
        lineNumber += 1
