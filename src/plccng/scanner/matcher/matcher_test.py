
from ..structs import Line, LexError, Skip, Token

from plccng.scanner.matcher import matcher


def test_empty_line():
    matcher = make_matcher()
    line = Line(text="", file=None, number = 1)
    result = matcher.match(line = line, index = 0)
    assert result == LexError(line=line, column = 1)

def test_match_rule():
    matcher = make_matcher()
    line = Line(text="-", file=None, number=1)
    result = matcher.match(line=line, index=0)
    assert result == Token(lexeme="-", name="MINUS")

def test_match_first_rule():
    matcher = make_matcher()
    line = Line(text="113--", file=None, number=1)
    result = matcher.match(line=line, index=0)
    assert result == Token(lexeme="113", name="NUMBER")

def test_match_skip_rule():
    matcher = make_matcher()
    line = Line(text="   555", file=None, number=1)
    result = matcher.match(line=line, index=0)
    assert result == Skip(lexeme="   ")

def test_match_longest_rule():
    matcher = make_matcher()
    line = Line(text="1235564", file=None, number=1)
    result = matcher.match(line=line, index=0)
    assert result == Token(lexeme="1235564", name="NUMBER")

def test_match_first_longest_rule():
    matcher = make_matcher()
    line = Line(text="123", file=None, number=1)
    result = matcher.match(line=line, index=0)
    assert result == Token(lexeme="123", name = "ONETWOTHREE")


#helper methods

def make_matcher():
    spec = [
        {
            "type": "Token",
            "name": "MINUS",
            "regex": "-"
        },

        {
            "type": "Skip",
            "name": "WHITESPACE",
            "regex": "\\s+"
        },
        {
            "type": "Token",
            "name": "ONETWOTHREE",
            "regex": "123"
        },
        {
            "type": "Token",
            "name": "NUMBER",
            "regex": "\\d+"
        }
    ]
    my_matcher = matcher.Matcher(spec)
    return my_matcher

