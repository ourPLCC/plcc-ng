from .parse_from_string import parse_from_string


def test_lex_only():
    s = '''
token A 'a'
skip B 'b'
'''
    spec = parse_from_string(s)
    assert len(spec.lexical) == 2
    assert len(spec.syntax) == 0
    assert len(spec.semantics) == 0


def test_lexical_and_syntax_only():
    s = '''
token A 'a'
skip B 'b'
%
<a> ::= A <b>
<b> ::= B
'''
    spec = parse_from_string(s)
    assert len(spec.lexical) == 2
    assert len(spec.syntax) == 2
    assert len(spec.semantics) == 0


def test_full():
    s = '''
token A 'a'
skip B 'b'
%
<a> ::= A <b>
<b> ::= B
%
A
%%%
Hi
%%%
%
A
%%%
Bye
%%%
'''
    spec = parse_from_string(s)
    assert len(spec.lexical) == 2
    assert len(spec.syntax) == 2
    assert len(spec.semantics) == 2
