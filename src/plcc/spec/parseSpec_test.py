import pytest

from .parseSpec import parseSpec
from .MultipleSemanticsError import MultipleSemanticsError
from .rough.UnclosedBlockError import UnclosedBlockError


def test_rough_errors_are_returned():
    _, errors = parseSpec("token NUM '\\d+'\n%\n<a> ::= NUM\n%\nPython\n%%%\nhi")
    assert any(isinstance(e, UnclosedBlockError) for e in errors)


def test_lex_only():
    spec, errors = parseSpec("token A 'a'\nskip B 'b'\n")
    assert len(spec.lexical) == 2
    assert len(spec.syntax) == 0
    assert spec.semantics is None


def test_lexical_and_syntax_only():
    spec, errors = parseSpec(
        "token A 'a'\nskip B 'b'\n%\n<a> ::= A <b>\n<b> ::= B\n"
    )
    assert len(spec.lexical) == 2
    assert len(spec.syntax) == 2
    assert spec.semantics is None


def test_full_with_single_semantic_section():
    s = '''\
token A 'a'
skip B 'b'
%
<a> ::= A <b>
<b> ::= B
%
Python
A
%%%
Hi
%%%
'''
    spec, errors = parseSpec(s)
    assert errors == []
    assert len(spec.lexical) == 2
    assert len(spec.syntax) == 2
    assert spec.semantics is not None
    assert spec.semantics.language == 'Python'


def test_multiple_semantic_sections_produces_error():
    s = '''\
token A 'a'
%
<a> ::= A
%
Python
%%%
one
%%%
%
Java
%%%
two
%%%
'''
    spec, errors = parseSpec(s)
    assert any(isinstance(e, MultipleSemanticsError) for e in errors)


def test_multiple_semantic_sections_returns_first_section():
    s = '''\
token A 'a'
%
<a> ::= A
%
Python
%
Java
'''
    spec, errors = parseSpec(s)
    assert spec.semantics is not None
    assert spec.semantics.language == 'Python'


def test_missing_language_declaration_produces_error():
    s = "token A 'a'\n%\n<a> ::= A\n%\n"
    spec, errors = parseSpec(s)
    assert len(errors) > 0
    assert spec.semantics is None
