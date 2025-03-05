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
                    break           #If a LexError is given at any point, just move on to the next line
                else:
                    index = result.column + 1
                    yield result 

#Placeholder Matcher "algorithm" since Scanner does not care about the algorithm, it just cares that a LexError, Skip, or Token
#is thrown. Scanner does not care about algorithm, but it does care about results.
class Matcher:
    def __init__(self, spec):
        self.spec = spec
    
    def match(self, line, index):
        if line.text[index] == " ":
            return Skip(name="whitespace", lexeme=" ", line=line, column=index)
        else:
            return LexError(line=line, column=index)