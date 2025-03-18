from .Line import Line
from .parse_from_file import parse_from_file
from .parse_from_string import parse_from_string
from .parse_from_strings import parse_from_strings


def parseLines(string=None, file=None, startLineNumber=1):
    if string is None and file is not None:
        return parse_from_file(file, startLineNumber=startLineNumber)
    if string is None or string == []:
        return []
    if isinstance(string, str):
        return parse_from_string(string, file=file, startLineNumber=startLineNumber)
    if isinstance(string, list):
        return parse_from_strings(string, file=file, startLineNumber=startLineNumber)
    raise TypeError
