from .resolve_includes import from_string_unresolved, resolve_includes


def parse_from_string(string, file=None, startLineNumber=1):
    return resolve_includes(from_string_unresolved(string, file, startLineNumber))
