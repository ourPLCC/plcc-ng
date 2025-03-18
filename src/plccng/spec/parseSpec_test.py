from .parseSpec import parseSpec


def test_lex_only():
    s = '''
token A 'a'
skip B 'b'
'''
    spec, errors = parseSpec(s)
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
    spec, errors = parseSpec(s)
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
    spec, errors = parseSpec(s)
    assert len(spec.lexical) == 2
    assert len(spec.syntax) == 2
    assert len(spec.semantics) == 2
