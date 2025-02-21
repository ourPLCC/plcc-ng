from . import parse_lines
from .parse_blocks import parse_blocks
from .parse_dividers import parse_dividers
from .parse_includes import parse_includes
from .resolve_includes import resolve_includes


def from_file(file, startLineNumber=1):
    return resolve_includes(from_file_unresolved(file, startLineNumber))


def from_file_unresolved(file, startLineNumber=1):
    lines = parse_lines.from_file(file, startLineNumber=startLineNumber)
    return from_lines_unresolved(lines)


def from_string(string, file=None, startLineNumber=1):
    return resolve_includes(from_string_unresolved(string, file, startLineNumber))


def from_string_unresolved(string, file=None, startLineNumber=1):
    lines = parse_lines.from_string(string, file=file, startLineNumber=startLineNumber)
    return from_lines_unresolved(lines)


def from_lines(lines):
    return resolve_includes(from_lines_unresolved(lines))


def from_lines_unresolved(lines):
    blocks = parse_blocks(lines)
    includes = parse_includes(blocks)
    dividers = parse_dividers(includes)
    return dividers


def raise_exceptions(rough):
    '''
    Yields each thing from rough.
    However, if the thing is an Exception,
    it is raised and iteration halts.
    '''
    for thing in rough:
        if isinstance(thing, Exception):
            raise thing
        else:
            yield thing
