from .structs import LexError


class Scanner:
    def __init__(self, matcher):
        self.matcher = matcher

    def scan(self, lines):
        if lines is None:
            return StopIteration
        for line in lines:
            yield from self._lineScanner(line)

    def _lineScanner(self, line):
        index = 0
        while index < len(line.string):
            result = self.matcher.match(line, index)
            if isinstance(result, LexError):
                yield result
                index += 1
            else:
                index += len(result.lexeme)
                yield result
