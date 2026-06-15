from .base import Node, Token


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
