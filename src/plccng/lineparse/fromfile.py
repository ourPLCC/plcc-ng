from plccng.lineparse.fromstrings import fromstrings


def fromfile(file, startLineNumber=1):
    with open(file) as f:
        yield from fromstrings(f, file=file, startLineNumber=startLineNumber)
