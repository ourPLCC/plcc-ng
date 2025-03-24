from .check_left_recursion import check_left_recursion
from .Grammar import Grammar

def test_no_left_recursion():
    g = setup([
        "x Y RIGHT",
        "x z RIGHT",
        "Z YUP"
    ])
    res = check_left_recursion(g)
    assert res is None

def test_direct_left_recursion():
    g = setup([
        "x x RIGHT"
    ])
    res = check_left_recursion(g)
    assert res == [('x', 'RIGHT')]

def test_indirect_left_recursion():
    g = setup([
        "x y RIGHT",
        "y x",
        "y z"
    ])
    res = check_left_recursion(g)
    assert res == [('y', 'RIGHT'), ('x',)]

def setup(lines):
    g = Grammar()
    for line in [line.split() for line in lines]:
        g.addRule(line[0], line[1:])
    return g
