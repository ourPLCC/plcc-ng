from .Spec import Spec
from .parse_from_string import parse_from_string

def test_lex_only():
    s = '''
token A 'a'
skip B 'b'
'''
    spec = parse_from_string(s)
    assert len(spec.lex) == 2
    assert len(spec.syn) == 0
    assert len(spec.sems) == 0


def test_lexical_and_syntax_only():
    s = '''
token A 'a'
skip B 'b'
%
<a> ::= A <b>
<b> ::= B
'''
