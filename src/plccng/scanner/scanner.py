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
        try:
            while index < len(line.string):
                result = self.matcher.match(line, index)
                index = result.column + len(result.lexeme)
                yield result
        except:
            yield result                    
