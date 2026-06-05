from .Line import Line


def parse_from_strings(strings, file=None, startLineNumber=1):
    for i, string in enumerate(strings, start=startLineNumber):
        if string.endswith('\r\n'):
            string = string[:-2] + '\n'
        elif string.endswith('\r'):
            string = string[:-1] + '\n'
        yield Line(string=string, file=file, number=i)
