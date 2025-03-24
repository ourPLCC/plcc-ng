from .parse_from_strings import parse_from_strings


def parse_from_string(string, file=None, startLineNumber=1):
    return parse_from_strings(string.splitlines(), file=file, startLineNumber=startLineNumber)
