from .Line import Line


def parse_from_strings(strings, file=None, startLineNumber=1):
    for i, string in enumerate(strings, start=startLineNumber):
        yield Line(string=string, file=file, number=i)
