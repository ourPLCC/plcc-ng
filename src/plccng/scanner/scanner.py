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
                index = result.column + 1 #(Currently Matcher only yields the very next index after LexError)
                yield result 

#Temporary solution to "matching" tokens until scanner/matcher.py can be used directly,
#since the actual matching algorithm does not seem to matter to scanner, scanner is only concerned about 
#all possible matches and their index, not how it matches them.
#So, for now, Matcher will ID any whitespace as a skip token, "error" as a LexError, and then any other single character as a token.
class Matcher:
    def __init__(self, spec):
        self.spec = spec
    
    def match(self, line, index):
        if line.text[index: ] == " ":
            return Skip(lexeme="filler", name="Skip", line="filler", column=index)
        elif line.text[index: ] == "error":
            return LexError(line=line, column=index+5)
        else:
            return Token(lexeme="filler", name="Token", line="filler", column=index)