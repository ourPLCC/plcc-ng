import pytest
from .structs import Line, Match, Skip, Token, LexError

class Scanner:
    def __init__(self, matcher):
        self.matcher = matcher


    def scan(self, lines):
        if not lines or lines == []:
            yield None
        for line in lines:
            index = 0 #Placeholder value
            yield self.matcher.match(line, index)
    

#Temporary solution to "matching" tokens until scanner/matcher.py can be used directly
class Matcher:
    def __init__(self, spec):
        self.spec = spec
    
    def match(self, line, index):
        return None

            