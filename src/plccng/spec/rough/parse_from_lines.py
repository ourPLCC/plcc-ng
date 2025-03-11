from .raise_handler import raise_handler
from .resolve_includes import from_lines_unresolved, resolve_includes


def parse_from_lines(lines, handler=raise_handler):
    return resolve_includes(from_lines_unresolved(lines, handler=handler), handler=handler)
