from ..spec import parse_lexical_from_string
from ..spec import Line
from .Skip import Skip
from .Token import Token
from .LexError import LexError

from . import matcher


def test_empty_line():
    matcher = make_matcher(spec=[
        {
            "type": "Token",
            "name": "MINUS",
            "regex": "-"
        }
    ])
    line = Line(string="", file=None, number = 1)
    result = matcher.match(line = line, index = 0)
    assert result == LexError(line=line, column = 1)

def test_empty_spec():
    matcher = make_matcher(spec = [])
    line = Line(string="This is a test", file=None, number=1)
    result = matcher.match(line = line, index = 0)
    assert result == LexError(line=line, column=1)

def test_match_rule():
    matcher = make_matcher(spec = [
        {
            "type": "Token",
            "name": "MINUS",
            "regex": "-"
        }
    ])
    line = Line(string="-", file=None, number=1)
    result = matcher.match(line=line, index=0)
    assert result == Token(lexeme="-", name="MINUS", column=1)

def test_match_first_rule():
    matcher = make_matcher(spec = [
        {
            "type": "Token",
            "name": "MINUS",
            "regex": "-"
        },
        {
            "type": "Token",
            "name": "NUMBER",
            "regex": "\\d+"
        }
    ])
    line = Line(string="113--", file=None, number=1)
    result = matcher.match(line=line, index=0)
    assert result == Token(lexeme="113", name="NUMBER", column=3)

def test_match_skip_rule():
    matcher = make_matcher(spec = [
        {
            "type": "Token",
            "name": "NUMBER",
            "regex": "\\d+"
        },
        {
            "type": "Skip",
            "name": "WHITESPACE",
            "regex": "\\s+"
        }
    ])
    line = Line(string="   555", file=None, number=1)
    result = matcher.match(line=line, index=0)
    assert result == Skip(lexeme="   ", name="WHITESPACE", column=4)

def test_match_longest_rule():
    matcher = make_matcher(spec = [
        {
            "type": "Token",
            "name": "NUMBER",
            "regex": "\\d+"
        },
        {
            "type": "Token",
            "name": "ONETWOTHREE",
            "regex": "123"
        }
    ])
    line = Line(string="1235564", file=None, number=1)
    result = matcher.match(line=line, index=0)
    assert result == Token(lexeme="1235564", name="NUMBER", column=7)

def test_match_first_longest_rule():
    matcher = make_matcher(spec = [
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
    ])
    line = Line(string="123", file=None, number=1)
    result = matcher.match(line=line, index=0)
    assert result == Token(lexeme="123", name = "ONETWOTHREE", column=3)

def test_match_later_index():
    matcher = make_matcher(spec=[
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
    ])
    line = Line(string="123456789", file=None, number=1)
    result = matcher.match(line=line, index=3)
    assert result == Token(lexeme="456789", name = "NUMBER", column=9)



#helper methods

def make_matcher(spec):
    my_matcher = matcher.Matcher(spec)
    return my_matcher
