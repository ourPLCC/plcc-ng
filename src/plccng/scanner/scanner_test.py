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

def test_index_subroutine_finds_all_indexes():
    line = Line("Plus Minus   PlusAGAIN", 1, None)
    scanner = make_scanner()
    results = scanner._getLineIndexes(line)
    assert results == [0, 5, 13]

@pytest.mark.skip(reason="This test is not yet covered. Where we are headed")
def test_one_token_matches():
    lines = [Line("-", 1, None)]
    scanner = make_scanner()
    results = scanner.scan(lines)
    assert next(results) == Token(lexeme="-", name="MINUS", line=Line("-", 1, None), column=0)  

@pytest.mark.skip(reason="This test is not yet covered. Where we are headed")
def test_multiple_tokens_match():
    lines = [   Line("-", 1, None),
                Line("+", 2, None),
                Line("-", 3, None)]
    scanner = make_scanner()
    results = scanner.scan(lines)
    assert next(results) == Token(lexeme="-", name="MINUS", line=Line("-", 1, None), column=0)  
    assert next(resutls) == Token(lexeme="+", name="MINUS", line=Line("+", 2, None), column=0)
    assert next(results) == Token(lexeme="-", name="MINUS", line=Line("-", 3, None), column=0)  

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


