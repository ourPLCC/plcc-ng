from ..lines import Line
from ..spec.lexical.TokenRule import TokenRule
from ..spec.lexical.SkipRule import SkipRule
from .UnclosedBlockError import UnclosedBlockError


def make_line(string='hello', number=1):
    return Line(string=string, number=number)


def make_token_rule(name='WORD', pattern=r'\w+', close_pattern=None):
    return TokenRule(line=make_line(), name=name, pattern=pattern, close_pattern=close_pattern)


def make_skip_rule(name='WS', pattern=r'\s+', close_pattern=None):
    return SkipRule(line=make_line(), name=name, pattern=pattern, close_pattern=close_pattern)


def test_instantiate_with_token_rule():
    rule = make_token_rule(name='STRING', pattern=r'"', close_pattern=r'"')
    line = make_line(string='"hello', number=3)
    err = UnclosedBlockError(line=line, column=1, rule=rule)
    assert err.line is line
    assert err.column == 1
    assert err.rule is rule


def test_instantiate_with_skip_rule():
    rule = make_skip_rule(name='COMMENT', pattern=r'#', close_pattern=r'\n')
    line = make_line(string='# unclosed', number=7)
    err = UnclosedBlockError(line=line, column=1, rule=rule)
    assert err.rule is rule


def test_equality():
    rule = make_token_rule(name='S', pattern=r'"', close_pattern=r'"')
    line = make_line()
    err1 = UnclosedBlockError(line=line, column=1, rule=rule)
    err2 = UnclosedBlockError(line=line, column=1, rule=rule)
    assert err1 == err2
