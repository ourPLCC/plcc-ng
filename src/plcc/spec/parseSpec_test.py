from .parseSpec import parseSpec
from .rough.UnclosedBlockError import UnclosedBlockError


def test_rough_errors_are_returned():
    # An unclosed %%% block triggers UnclosedBlockError at rough-parse time.
    # Before the fix, the errors variable was overwritten and rough errors dropped.
    _, errors = parseSpec("token NUM '\\d+'\n%\n<a> ::= NUM\n%\nA\n%%%\nhi")
    assert any(isinstance(e, UnclosedBlockError) for e in errors)


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
