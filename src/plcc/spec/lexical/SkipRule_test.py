import re

from ...lines import Line
from ...scan.Skip import Skip
from .SkipRule import SkipRule


def make_line(string='hello', number=1):
    return Line(string=string, number=number)


def make_rule(name='SPACE', pattern=r'\s+'):
    return SkipRule(line=make_line(), name=name, pattern=pattern)


def test_make_match_returns_skip():
    rule = make_rule(name='SPACE', pattern=r'\s+')
    line = make_line(string='   abc', number=5)
    m = re.match(r'\s+', '   abc')
    result = rule.make_match(m, line, 0)
    assert isinstance(result, Skip)
    assert result.lexeme == '   '
    assert result.name == 'SPACE'
    assert result.line is line
    assert result.column == 1
    assert result.pattern == r'\s+'


def test_make_match_column_uses_index_offset():
    rule = make_rule(name='WS', pattern=r'\s+')
    line = make_line(string='x   y', number=2)
    m = re.match(r'\s+', '   y')
    result = rule.make_match(m, line, 1)
    assert result.column == 2
