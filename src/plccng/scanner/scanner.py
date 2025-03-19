from .structs import LexError


class Scanner:
    def __init__(self, matcher):
        self.matcher = matcher

    def scan(self, lines):
        if lines is None:
            return StopIteration
        for line in lines:
            index = 0
            while index < len(line.string):
                result = self.matcher.match(line, index)
                if isinstance(result, LexError):
                    yield result
                    break           #If a LexError is given at any point, just move on to the next line
                else:
                    index = result.column + 1
                    yield result
