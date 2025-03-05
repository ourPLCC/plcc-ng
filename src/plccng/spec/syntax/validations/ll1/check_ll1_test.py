from .check_ll1 import check_ll1
from .Grammar import Grammar


def test_integration_ll1():
    g = Grammar()
    g.addRule('a', ['t'])
    errors = check_ll1(g)
    assert not errors
