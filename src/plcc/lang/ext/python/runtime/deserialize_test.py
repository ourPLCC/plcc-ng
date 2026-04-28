from .deserialize import deserialize
from .registry import Registry
from .base import Node, Token


class FakeProgram(Node):
    _rule_name = 'program'
    _fields = ['num']

    def __init__(self, num):
        self.num = num


class FakeExprRest(Node):
    _rule_name = 'ExprRest'
    _fields = ['term', 'rest']

    def __init__(self, term, rest):
        self.term = term
        self.rest = rest


class FakeNilRest(Node):
    _rule_name = 'ExprRest'
    _fields = []

    def __init__(self):
        pass


class FakeRands(Node):
    _rule_name = 'rands'
    _fields = ['exprList']

    def __init__(self, exprList):
        self.exprList = exprList


def _make_registry():
    reg = Registry()
    reg.register(FakeProgram, FakeExprRest, FakeNilRest)
    return reg


def test_deserialize_token_node():
    tree = {"kind": "token", "name": "NUM", "lexeme": "42"}
    reg = _make_registry()
    result = deserialize(tree, reg)
    assert isinstance(result, Token)
    assert result.kind == 'NUM'
    assert result.lexeme == '42'


def test_deserialize_leaf_nonterminal():
    tree = {"kind": "tree", "rule": "program", "children": [
        ["num", {"kind": "token", "name": "NUM", "lexeme": "7"}]
    ]}
    reg = _make_registry()
    result = deserialize(tree, reg)
    assert isinstance(result, FakeProgram)
    assert isinstance(result.num, Token)
    assert result.num.lexeme == '7'


def test_deserialize_empty_children_nonterminal():
    tree = {"kind": "tree", "rule": "ExprRest", "children": []}
    reg = _make_registry()
    result = deserialize(tree, reg)
    assert isinstance(result, FakeNilRest)


def test_deserialize_nested():
    tree = {"kind": "tree", "rule": "ExprRest", "children": [
        ["term", {"kind": "token", "name": "NUM", "lexeme": "1"}],
        ["rest", {"kind": "tree", "rule": "ExprRest", "children": []}],
    ]}
    reg = _make_registry()
    result = deserialize(tree, reg)
    assert isinstance(result, FakeExprRest)
    assert isinstance(result.term, Token)
    assert isinstance(result.rest, FakeNilRest)


def test_deserialize_list_field_of_tokens():
    tree = {
        "kind": "tree",
        "rule": "rands",
        "children": [
            ["exprList", [
                {"kind": "token", "name": "NUM", "lexeme": "1"},
                {"kind": "token", "name": "NUM", "lexeme": "2"},
            ]]
        ]
    }
    reg = Registry()
    reg.register(FakeRands)
    result = deserialize(tree, reg)
    assert isinstance(result, FakeRands)
    assert len(result.exprList) == 2
    assert isinstance(result.exprList[0], Token)
    assert result.exprList[0].lexeme == '1'
    assert isinstance(result.exprList[1], Token)
    assert result.exprList[1].lexeme == '2'


def test_deserialize_empty_list_field():
    tree = {
        "kind": "tree",
        "rule": "rands",
        "children": [["exprList", []]]
    }
    reg = Registry()
    reg.register(FakeRands)
    result = deserialize(tree, reg)
    assert result.exprList == []
