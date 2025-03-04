import pytest
from .structs import Line, Match, Skip, Token, LexError

class Scanner:
    def __init__(self, matcher):
        self.matcher = matcher

    def scan(self, lines):
        if not lines or lines == []:
            yield None
        for line in lines:
            index = 0
            while index < len(line.text):
                result = self.matcher.match(line, index)                
                if isinstance(result, LexError):
                    yield result
                    break
                else:
                    index = result.column + 1
                    yield result 

#Placeholder matcher, either needs to be developed or matcher needs to be merged in
class Matcher:
    def __init__(self, spec):
        self.spec = spec
    
    def match(self, line, index):
        return LexError(line=line, column=index + 1)