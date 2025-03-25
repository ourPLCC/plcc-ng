from ..lines import parseLines
from ..spec import parseSpec
from . import matcher
from .LexError import LexError
from .Skip import Skip
from .Token import Token


def test_empty_line():
    matcher = makeMatcher(r'''token MINUS '-' ''')
    emptyLine = parseLine('')
    result = matcher.match(emptyLine, index = 0)
    assert result.__class__ == LexError

def test_empty_spec():
    emptySpec = []
    matcher = makeMatcher(emptySpec)
    line = parseLine("This is a test.")
    result = matcher.match(line, index=0)
    assert result.__class__ == LexError

def test_match_token():
    matcher = makeMatcher(r'''token MINUS '-' ''')
    line = parseLine("-")
    result = matcher.match(line, index=0)
    assert result == Token(lexeme="-", name="MINUS", column=1)

def test_match_skip():
    matcher = makeMatcher(r'''skip MINUS '-' ''')
    line = parseLine("-")
    result = matcher.match(line, index=0)
    assert result == Skip(lexeme="-", name="MINUS", column=1)

def test_match_token_with_multiple_rules():
    matcher = makeMatcher(r'''
        token MINUS '-'
        token NUMBER '\d+'
    ''')
    line = parseLine("11--")
    result = matcher.match(line, index=0)
    assert result == Token(lexeme="11", name="NUMBER", column=2)

def test_match_longest_rule():
    matcher = makeMatcher(r'''
        token NUMBER '\d+'
        token ONETWOTHREE '123'
    ''')
    line = parseLine("1235564")
    result = matcher.match(line, index=0)
    assert result == Token(lexeme="1235564", name="NUMBER", column=7)

    # order should not matter
    matcher = makeMatcher(r'''
        token ONETWOTHREE '123'
        token NUMBER '\d+'
    ''')
    line = parseLine("1235564")
    result = matcher.match(line, index=0)
    assert result == Token(lexeme="1235564", name="NUMBER", column=7)

def test_match_first_longest_rule():
    matcher = makeMatcher(r'''
        token ONETWOTHREE '123'
        token NUMBER '\d+'
    ''')
    line = parseLine("123")
    result = matcher.match(line, index=0)
    assert result == Token(lexeme="123", name = "ONETWOTHREE", column=3)

    # order matters
    matcher = makeMatcher(r'''
        token NUMBER '\d+'
        token ONETWOTHREE '123'
    ''')
    line = parseLine("123")
    result = matcher.match(line, index=0)
    assert result == Token(lexeme="123", name = "NUMBER", column=3)

def test_skip_wins_if_it_matches_before_any_token_rules():
    matcher = makeMatcher(r'''
        skip ONE '1'
        token NUMBER '\d+'
    ''')
    line = parseLine("123")
    result = matcher.match(line, index=0)
    assert result == Skip(lexeme='1', name='ONE', column=1)

    # Now token ONETWO matches before skip ONE, so skip is ignored.
    # But then token NUMBER wins because it matches longest.
    matcher = makeMatcher(r'''
        token ONETWO '12'
        skip ONE '1'
        token NUMBER '\d+'
    ''')
    line = parseLine("123")
    result = matcher.match(line, index=0)
    assert result == Token(lexeme='123', name='NUMBER', column=1)


#helper methods

def makeMatcher(spec):
    if isinstance(spec, str):
        spec, errors = parseSpec(spec)
        return matcher.Matcher(spec.lexical.ruleList)
    else:
        return matcher.Matcher(spec)


def parseLine(string):
    return list(parseLines(string + '\n'))[0]
