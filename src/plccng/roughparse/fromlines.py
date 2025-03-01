from plccng.roughparse.resolve_includes import from_lines_unresolved, resolve_includes


def fromlines(lines):
    return resolve_includes(from_lines_unresolved(lines))
