from dataclasses import dataclass


def fromFile(file, startLineNumber=1):
    with open(file) as f:
        yield from fromStrings(f, file=file, startLineNumber=startLineNumber)


def fromString(string, file=None, startLineNumber=1):
    if string is None:
        return iter(())
    return fromStrings(string.splitlines(), file=file, startLineNumber=startLineNumber)


def fromStrings(strings, file=None, startLineNumber=1):
    for i, string in enumerate(strings, start=startLineNumber):
        yield Line(string=string, file=file, number=i)


@dataclass(frozen=True)
class Line:
    string: str
    number: int
    file: str = None
