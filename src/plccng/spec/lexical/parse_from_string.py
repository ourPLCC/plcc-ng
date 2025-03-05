from plccng.spec import rough
from plccng.spec.lexical.parse_from_lines import parse_from_lines


def parse_from_string(string, file=None, startLineNumber=1):
    rough_ = rough.parse_from_string(string, file=file, startLineNumber=startLineNumber)
    return parse_from_lines(rough_)
