import pytest
from .registry import Registry
from .base import Node


class FakeProgram(Node):
    _rule_name = 'program'
    _fields = ['expr']

    def __init__(self, expr):
        self.expr = expr


class FakeAddRest(Node):
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


class FakeAbstract(Node):
    _rule_name = 'ExprRest'
    _fields = []
    _abstract = True


def test_registry_lookup_simple():
    reg = Registry()
    reg.register(FakeProgram)
    cls = reg.lookup('program', ['expr'])
    assert cls is FakeProgram


def test_registry_lookup_by_field_set_disambiguation():
    reg = Registry()
    reg.register(FakeAddRest, FakeNilRest)
    assert reg.lookup('ExprRest', ['term', 'rest']) is FakeAddRest
    assert reg.lookup('ExprRest', []) is FakeNilRest


def test_registry_lookup_field_order_independent():
    reg = Registry()
    reg.register(FakeAddRest)
    assert reg.lookup('ExprRest', ['rest', 'term']) is FakeAddRest


def test_registry_lookup_unknown_rule_raises():
    reg = Registry()
    with pytest.raises(KeyError):
        reg.lookup('unknown', [])


def test_registry_skips_abstract_classes():
    reg = Registry()
    reg.register(FakeAbstract, FakeNilRest)
    # FakeAbstract._abstract=True so NilRest should win for empty field set
    assert reg.lookup('ExprRest', []) is FakeNilRest
