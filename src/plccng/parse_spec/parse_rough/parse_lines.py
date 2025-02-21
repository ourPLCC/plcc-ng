from plccng.parse_spec.structs import Line


def from_string(string, file=None, startLineNumber=1):
    if string is None:
        return []
    print(string.splitlines())
    return from_strings(string.splitlines(), file=file, startLineNumber=startLineNumber)


def from_file(file, startLineNumber=1):
    with open(file) as f:
        yield from from_strings(f, file=file, startLineNumber=startLineNumber)


def from_strings(strings, file=None, startLineNumber=1):
    for i, string in enumerate(strings, start=startLineNumber):
        yield Line(string=string.rstrip(), file=file, number=i)
