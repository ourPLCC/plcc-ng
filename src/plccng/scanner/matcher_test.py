from ..spec import parse_lexical_from_string
from ..spec import Line, parse_lines_from_string
from .Skip import Skip
from .Token import Token
from .LexError import LexError

from . import matcher


def test_empty_line():
    spec, errors = parse_lexical_from_string(string = '''token MINUS '-' ''')
    matcher = make_matcher(spec=spec.ruleList)
    result = matcher.match(line=Line(string="", number=0), index = 0)
    assert result.__class__ == LexError

def test_empty_spec():
    matcher = make_matcher(spec = [])
    line = list(parse_lines_from_string("This is a test."))[0]
    result = matcher.match(line = line, index = 0)
    assert result.__class__ == LexError

def test_match_rule():
    spec, errors = parse_lexical_from_string(string='''token MINUS '-' ''')
    matcher = make_matcher(spec=spec.ruleList)
    line = list(parse_lines_from_string("-"))[0]
    result = matcher.match(line=line, index=0)
    assert result == Token(lexeme="-", name="MINUS", column=1)

def test_match_first_rule_in_file():
    spec, errors = parse_lexical_from_string(string='''
        token MINUS '-'
        token NUMBER '\\d+'
    ''')
    matcher = make_matcher(spec=spec.ruleList)
    line = list(parse_lines_from_string("11--"))[0]
    result = matcher.match(line=line, index=0)
    assert result == Token(lexeme="11", name="NUMBER", column=2)

def test_match_skip_rule():
    spec, errors = parse_lexical_from_string(string='''
        skip WHITESPACE '\\s+'
    ''')
    matcher = make_matcher(spec = spec.ruleList)
    line = list(parse_lines_from_string("   555"))[0]
    result = matcher.match(line=line, index=0)
    assert result == Skip(lexeme="   ", name="WHITESPACE", column=3)

def test_match_longest_rule():
    spec, errors = parse_lexical_from_string(string='''
        token NUMBER '\\d+'
        token ONETWOTHREE '123'
    ''')
    matcher = make_matcher(spec=spec.ruleList)
    line = list(parse_lines_from_string("1235564"))[0]
    result = matcher.match(line=line, index=0)
    assert result == Token(lexeme="1235564", name="NUMBER", column=7)

def test_match_first_longest_rule():
    spec, errors = parse_lexical_from_string(string='''
        token ONETWOTHREE '123'
        token NUMBER '\\d+'
    ''')
    matcher = make_matcher(spec=spec.ruleList)
    line = list(parse_lines_from_string("123"))[0]
    result = matcher.match(line=line, index=0)
    assert result == Token(lexeme="123", name = "ONETWOTHREE", column=3)

def test_match_later_index():
    spec, errors = parse_lexical_from_string(string='''
        token ONETWOTHREE '123'
        token NUMBER '\\d+'
    ''')
    matcher = make_matcher(spec=spec.ruleList)
    line = list(parse_lines_from_string("123456789"))[0]
    result = matcher.match(line=line, index=3)
    assert result == Token(lexeme="456789", name = "NUMBER", column=9)

def test_skip_ignored():
    spec, errors = parse_lexical_from_string(string='''
        skip ONE '1'
        token NUMBER '\\d+'
    ''')
    matcher = make_matcher(spec=spec.ruleList)
    line = list(parse_lines_from_string("123"))[0]
    result = matcher.match(line=line, index=0)
    assert result == Skip(lexeme='1', name='ONE', column=1)



#helper methods

def make_matcher(spec):
    my_matcher = matcher.Matcher(spec)
    return my_matcher
