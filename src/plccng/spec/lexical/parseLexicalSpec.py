from .parse_from_lines import parse_from_lines
from .parse_from_string import parse_from_string


def parseLexicalSpec(thing, file=None, startLineNumber=1):
    if isinstance(thing, str) or thing is None:
        return parse_from_string(thing, file=file, startLineNumber=startLineNumber)
    if isinstance(thing, list):
        return parse_from_lines(thing)
    raise TypeError(f'Unexpected type: {type(thing)}')
