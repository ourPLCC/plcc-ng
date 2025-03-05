from .resolve_includes import from_lines_unresolved, resolve_includes


def parse_from_lines(lines):
    return resolve_includes(from_lines_unresolved(lines))
