from .. import lines
from .parse_from_lines_without_validation import parse_from_lines_without_validation


def parse_from_string_without_validation(string, file=None, startLineNumber=1):
    lines_ = lines.parse_from_string(string, file=file, startLineNumber=startLineNumber)
    return parse_from_lines_without_validation(lines_)
