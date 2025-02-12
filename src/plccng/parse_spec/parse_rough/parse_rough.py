from . import parse_lines
from .parse_blocks import parse_blocks
from .parse_dividers import parse_dividers
from .parse_includes import parse_includes


def from_file(file, startLineNumber=1):
    lines = parse_lines.from_file(file, startLineNumber=startLineNumber)
    return from_lines(lines)


def from_string(string, file=None, startLineNumber=1):
    lines = parse_lines.from_string(string, file=file, startLineNumber=startLineNumber)
    return from_lines(lines)


def from_lines(lines):
    blocks = parse_blocks(lines)
    includes = parse_includes(blocks)
    dividers = parse_dividers(includes)
    return dividers
