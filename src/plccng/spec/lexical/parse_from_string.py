from .. import rough
from .parse_from_lines import parse_from_lines


def parse_from_string(string, file=None, startLineNumber=1):
    rough_, errors = rough.parseRough(string, file=file, startLineNumber=startLineNumber)
    return parse_from_lines(rough_)
