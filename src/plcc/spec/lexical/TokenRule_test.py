import re

from ...lines import Line
from ...scan.Token import Token
from .TokenRule import TokenRule


def make_line(string='hello', number=1):
    return Line(string=string, number=number)


def make_rule(name='WORD', pattern=r'\w+'):
    return TokenRule(line=make_line(), name=name, pattern=pattern)


def test_make_match_returns_token():
    rule = make_rule(name='NUM', pattern=r'\d+')
    line = make_line(string='42 rest', number=3)
    m = re.match(r'\d+', '42 rest')
    result = rule.make_match(m, line, 0)
    assert isinstance(result, Token)
    assert result.lexeme == '42'
    assert result.name == 'NUM'
    assert result.line is line
    assert result.column == 1
    assert result.pattern == r'\d+'


def test_make_match_column_uses_index_offset():
    rule = make_rule(name='WORD', pattern=r'\w+')
    line = make_line(string='   abc', number=7)
    m = re.match(r'\w+', 'abc')
    result = rule.make_match(m, line, 3)
    assert result.column == 4
