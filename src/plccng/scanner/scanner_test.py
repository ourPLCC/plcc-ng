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

def test_one_token_matches():
    lines = [Line("-", 1, None)]
    scanner = make_scanner()
    results = scanner.scan(lines)
    assert isinstance(next(results), Token)

def test_one_skip_matches():
    lines = [Line(" ", 1, None)]
    scanner = make_scanner()
    results = scanner.scan(lines)
    assert isinstance(next(results), Skip)

def test_one_skip_and_one_token_yielded_in_correct_order():
    #a is defined as token in scanner.py Matcher and " " after it is defined as a skip
    lines = [Line("a ", 1, None)]
    scanner = make_scanner()
    results = scanner.scan(lines)
    assert isinstance(next(results), Token)
    assert isinstance(next(results), Skip)

def make_scanner():
    matcher = make_matcher()
    scanner = Scanner(matcher)
    return scanner

def make_matcher():
    mock_speck = make_mock_spec
    matcher = Matcher(mock_speck)
    return matcher

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


