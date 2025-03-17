import pytest
from .scanner import Scanner, Matcher
from .structs import Line, Match, Token, Skip, LexError

def test_no_lines_given_returns_nothing():
    lines = None
    scanner = make_scanner()
    results = scanner.scan(lines)
    assert next(results) == None

def test_empty_lines_given_returns_nothing():
    lines = []
    scanner = make_scanner()
    results = scanner.scan(lines)
    assert next(results) == None 

def test_Lex_Error_moves_on_to_next_line():
    lines = makeLines(['blah blah blah', 'this is a new line'])
    scanner = make_scanner()
    results = scanner.scan(lines)
    check = next(results)
    assert isinstance(check, LexError) and check.line.text == 'blah blah blah'
    check = next(results)
    assert isinstance(check, LexError) and check.line.text == 'this is a new line'

def test_one_skip_matches():
    lines = [Line(" ", 1, None)]
    scanner = make_scanner()
    results = scanner.scan(lines)
    assert isinstance(next(results), Skip)

def make_scanner():
    matcher = make_matcher()
    scanner = Scanner(matcher)
    return scanner

def make_matcher():
    mock_speck = make_mock_spec()
    matcher = Matcher(mock_speck)
    return matcher

#This mock speck is currently not in use, I am just passing a dummy spec for now
#In the future it will be used in testing when a Matcher is implemented 
def make_mock_spec():
    spec = [
        {
            "type": "Token",
            "name": "MINUS",
            "regex": "-"
        },
        {
            "type": "Token",
            "name": "ADDING",
            "regex": "+"
        }
    ]

def makeLines(lines):
    line_objects=[]
    for line in lines:
        line_objects.append(Line(text=line, file=None, number=1))
    return line_objects

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