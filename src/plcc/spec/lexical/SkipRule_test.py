import re

from ...lines import Line
from ...scan.Skip import Skip
from .SkipRule import SkipRule


def make_line(string='hello', number=1):
    return Line(string=string, number=number)


def make_rule(name='SPACE', pattern=r'\s+', close_pattern=None):
    return SkipRule(line=make_line(), name=name, pattern=pattern, close_pattern=close_pattern)


def test_make_match_returns_skip_when_no_close_pattern():
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


def test_make_block_result_returns_skip_with_correct_fields():
    rule = make_rule(name='COMMENT', pattern=r'#.*')
    line = make_line(string='# a comment', number=9)
    result = rule.make_block_result(lexeme='# a comment', line=line, column=1)
    assert isinstance(result, Skip)
    assert result.lexeme == '# a comment'
    assert result.name == 'COMMENT'
    assert result.line is line
    assert result.column == 1
    assert result.pattern == r'#.*'
