from plccng.roughparse.resolve_includes import from_string_unresolved, resolve_includes


def fromstring(string, file=None, startLineNumber=1):
    return resolve_includes(from_string_unresolved(string, file, startLineNumber))
