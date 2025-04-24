from .check_ll1 import check_ll1
from .Grammar import Grammar


def test_integration_ll1():
    g = Grammar()
    g.addRule('a', ['t'])
    errors = check_ll1(g)
    assert not errors

def test_left_factoring_ll1():
    g = Grammar()
    g.addRule('a', ['(', 'T', ')'])
    g.addRule('a', ['(', ')'])
    errors = check_ll1(g)
    assert errors

def test_direct_left_recursion_not_ll1():
    g = Grammar()
    g.addRule('a', ['a'])
    errors = check_ll1(g)
    assert errors


def test_indirect_left_recursion_not_ll1():
    g = Grammar()
    g.addRule('a', ['b'])
    g.addRule('b', ['a'])
    errors = check_ll1(g)
    assert errors
