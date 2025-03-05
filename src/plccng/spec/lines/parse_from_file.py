from .parse_from_strings import parse_from_strings


def parse_from_file(file, startLineNumber=1):
    with open(file) as f:
        yield from parse_from_strings(f, file=file, startLineNumber=startLineNumber)
