import pytest
from .structs import Line, Match, Skip, Token, LexError

class Scanner:
    def __init__(self, matcher):
        self.matcher = matcher

    def scan(self, lines):
        if not lines or lines == []:
            yield None
        for line in lines:
            indexes = self._getLineIndexes(line)
            for index in indexes:
                yield self.matcher.match(line, index)
    
    #Find the indexes of all the possible tokens and skips in a given line to feed to the matcher in "scan"
    #FIX : Currently doesn't find index of whitespace
    def _getLineIndexes(self, line):
        indexes = []
        line_text = line.text
        possible_tokens = line_text.split()        
        for token in possible_tokens:
            index = line_text.index(token)
            indexes.append(index)
        return indexes


#Temporary solution to "matching" tokens until scanner/matcher.py can be used directly
class Matcher:
    def __init__(self, spec):
        self.spec = spec
    
    def match(self, line, index):
        return None