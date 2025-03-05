from plccng.spec import rough
from plccng.spec.lexical.parse_from_lines_without_validation import parse_from_lines_without_validation


def parse_from_string_without_validation(string, file=None, startLineNumber=1):
    rough_ = rough.parse_from_string(string, file=file, startLineNumber=startLineNumber)
    return parse_from_lines_without_validation(rough_)
