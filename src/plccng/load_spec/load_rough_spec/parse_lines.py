from plccng.load_spec.structs import Line


def parse_lines(string, startNumber=1, file=None):
    '''
    Yield Lines in string. Newlines are not preserved.

        string: The string from which Lines are parsed.
        start: Starting number for Line numbering (default=1).
        file: File stored in each Line.
        Line: Line constructor. Called like: Line(string=s, number=i, file=file)
    '''
    if string is None:
        return
    for i, s in enumerate(string.splitlines(), start=startNumber):
        yield Line(string=s, number=i, file=file)
