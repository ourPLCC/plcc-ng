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
    assert res == [[('x', ('x', 'RIGHT'))]]

def test_indirect_left_recursion():
    g = setup([
        "x y RIGHT",
        "y x",
        "y TWO"
    ])
    res = check_left_recursion(g)
    assert res == [[('y', ('x',)), ('x', ('y', 'RIGHT'))]]

def test_multiple_direct_left_recursion():
    g = setup([
        "x x RIGHT",
        "x x LEFT"
    ])
    res = check_left_recursion(g)
    assert res == [[('x', ('x', 'RIGHT')), ('x', ('x', 'LEFT'))]]

def test_multiple_indirect_left_recursion():
    g = setup([
        "x y A",
        "x y B",
        "y x C"
    ])
    res = check_left_recursion(g)
    assert res == [[('y', ('x', 'C')), ('x', ('y', 'A')), ('x', ('y', 'B'))]]

def test_layered_indirect_left_recursion():
    g = setup([
        "x y RIGHT",
        "y z LEFT",
        "z a THERE",
        "a x HA"
    ])
    res = check_left_recursion(g)
    assert res == [[('z', ('a', 'THERE')), ('y', ('z', 'LEFT')), ('a', ('x', 'HA')), ('x', ('y', 'RIGHT'))]]

def test_both_direct_and_indirect_left_recursion():
    g = setup([
        "x y RIGHT",
        "y x LEFT",
        "z z ZEE",
    ])
    res = check_left_recursion(g)
    assert res == [[('y', ('x', 'LEFT')), ('x', ('y', 'RIGHT'))], [('z', ('z', 'ZEE'))]]

def setup(lines):
    g = Grammar()
    for line in [line.split() for line in lines]:
        g.addRule(line[0], line[1:])
    return g
