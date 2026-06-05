from ..lines import Line
from ..spec.lexical.TokenRule import TokenRule
from ..spec.lexical.SkipRule import SkipRule
from .BlockOpened import BlockOpened


def make_line(string='hello', number=1):
    return Line(string=string, number=number)


def make_token_rule(name='WORD', pattern=r'\w+', close_pattern=None):
    return TokenRule(line=make_line(), name=name, pattern=pattern, close_pattern=close_pattern)


def make_skip_rule(name='WS', pattern=r'\s+', close_pattern=None):
    return SkipRule(line=make_line(), name=name, pattern=pattern, close_pattern=close_pattern)


def test_instantiate_with_token_rule():
    rule = make_token_rule(name='STRING', pattern=r'"', close_pattern=r'"')
    line = make_line(string='"hello"', number=2)
    bo = BlockOpened(rule=rule, lexeme='"', line=line, column=1)
    assert bo.rule is rule
    assert bo.lexeme == '"'
    assert bo.line is line
    assert bo.column == 1


def test_name_delegates_to_rule():
    rule = make_token_rule(name='STRING', pattern=r'"', close_pattern=r'"')
    line = make_line()
    bo = BlockOpened(rule=rule, lexeme='"', line=line, column=1)
    assert bo.name == 'STRING'


def test_pattern_delegates_to_rule():
    rule = make_token_rule(name='STRING', pattern=r'"', close_pattern=r'"')
    line = make_line()
    bo = BlockOpened(rule=rule, lexeme='"', line=line, column=1)
    assert bo.pattern == r'"'


def test_instantiate_with_skip_rule():
    rule = make_skip_rule(name='COMMENT', pattern=r'#', close_pattern=r'\n')
    line = make_line(string='# note', number=5)
    bo = BlockOpened(rule=rule, lexeme='#', line=line, column=1)
    assert bo.name == 'COMMENT'


def test_attempts_defaults_to_empty_list():
    rule = make_token_rule()
    line = make_line()
    bo = BlockOpened(rule=rule, lexeme='x', line=line, column=1)
    assert bo.attempts == []


def test_equality_ignores_attempts():
    rule = make_token_rule()
    line = make_line()
    bo1 = BlockOpened(rule=rule, lexeme='x', line=line, column=1, attempts=[1, 2])
    bo2 = BlockOpened(rule=rule, lexeme='x', line=line, column=1, attempts=[])
    assert bo1 == bo2
