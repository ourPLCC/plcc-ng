from plccng.lineparse.fromstrings import fromstrings


def fromstring(string, file=None, startLineNumber=1):
    if string is None:
        return iter(())
    return fromstrings(string.splitlines(), file=file, startLineNumber=startLineNumber)
