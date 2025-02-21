from plccng import lines as lines_
from plccng.spec.roughs.parse_blocks import parse_blocks
from plccng.spec.roughs.parse_dividers import parse_dividers
from plccng.spec.roughs.parse_includes import parse_includes
from plccng.spec.roughs.resolve_includes import resolve_includes


def from_lines_unresolved(lines):
    blocks = parse_blocks(lines)
    includes = parse_includes(blocks)
    dividers = parse_dividers(includes)
    return dividers


def from_lines(lines):
    return resolve_includes(from_lines_unresolved(lines))


def from_string_unresolved(string, file=None, startLineNumber=1):
    lines = lines_.fromString(string, file=file, startLineNumber=startLineNumber)
    return from_lines_unresolved(lines)


def from_string(string, file=None, startLineNumber=1):
    return resolve_includes(from_string_unresolved(string, file, startLineNumber))


def from_file_unresolved(file, startLineNumber=1):
    lines = lines_.fromFile(file, startLineNumber=startLineNumber)
    return from_lines_unresolved(lines)


def from_file(file, startLineNumber=1):
    return resolve_includes(from_file_unresolved(file, startLineNumber))
