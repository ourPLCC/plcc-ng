import pytest

from .base import Node, Token, LanguageError


def test_node_is_base_class():
    n = Node()
    assert isinstance(n, Node)


def test_token_stores_kind_and_lexeme():
    t = Token(kind='NUM', lexeme='42')
    assert t.kind == 'NUM'
    assert t.lexeme == '42'


def test_token_is_not_node():
    t = Token(kind='NUM', lexeme='1')
    assert not isinstance(t, Node)


def test_token_str_returns_lexeme():
    t = Token(kind='NUM', lexeme='42')
    assert str(t) == '42'


def test_token_repr_returns_lexeme():
    t = Token(kind='NUM', lexeme='42')
    assert repr(t) == '42'


def test_language_error_is_exception():
    assert issubclass(LanguageError, Exception)


def test_language_error_can_be_raised_and_caught():
    with pytest.raises(LanguageError, match="type mismatch"):
        raise LanguageError("type mismatch")


def test_language_error_subclass_is_caught_as_language_error():
    class TypeError(LanguageError):
        pass
    with pytest.raises(LanguageError):
        raise TypeError("bad type")
