from plccng.load_spec.structs import Line


def from_string(string, file=None, startNumber=1):
    if string is None:
        return []
    return from_strings(string.splitlines(), file=file, startNumber=startNumber)


def from_file(file, startNumber=1):
    with open(file) as f:
        yield from from_strings(f, file=file, startNumber=startNumber)


def from_strings(strings, file=None, startNumber=1):
    for i, string in enumerate(strings, start=startNumber):
        yield Line(string=string, file=file, number=i)
