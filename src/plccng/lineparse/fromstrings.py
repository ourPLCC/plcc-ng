from plccng.lineparse.Line import Line


def fromstrings(strings, file=None, startLineNumber=1):
    for i, string in enumerate(strings, start=startLineNumber):
        yield Line(string=string, file=file, number=i)
