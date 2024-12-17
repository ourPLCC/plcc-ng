from .Grammar import Grammar
from .build_first_sets import build_first_sets
from .build_follow_sets import build_follow_sets


def test_example():
    '''
    This is an acceptance test based on the example given
    for building FOLLOW sets from
    https://pages.cs.wisc.edu/~hasti/cs536/readings/Topdown.html#follow
    '''
    g, FIRST, FOLLOW = setup([
        'S B c',
        'S D B',
        'B a b',
        'B c S',
        'D d',
        'D'
    ])

    assert FIRST['D'] == {'d', g.getEpsilon()}
    assert FIRST['B'] == {'a', 'c'}
    assert FIRST['S'] == {'a', 'c', 'd'}

    assert FOLLOW['D'] == {'a', 'c'}
    assert FOLLOW['B'] == {'c', g.getEof()}
    assert FOLLOW['S'] == {'c', g.getEof()}


def test_test_yourself_3():
    '''
    This is an acceptance test based on "Test yourself #3" from
    https://pages.cs.wisc.edu/~hasti/cs536/readings/Topdown.html#follow
    '''
    grammar, firsts, follows = setup([
        'methodHeader VOID ID LPAREN paramList RPAREN',
        'paramList',
        'paramList nonEmptyParamList',
        'nonEmptyParamList ID ID',
        'nonEmptyParamList ID ID COMMA nonEmptyParamList'
    ])
    assert follows['methodHeader'] == {grammar.getEof()}
    assert follows['paramList'] == {'RPAREN'}
    assert follows['nonEmptyParamList'] == {'RPAREN'}


def test_derives_epsilon():
    grammar, firsts, follows = setup([
        'B A C',
        'A',
        'C'
    ])
    # C follows A. But C can derive epsilon.
    # So A's follow includes B's follow, which contains EOF.
    assert follows['A'] == {grammar.getEof()}


def test_follow_set_one_rule():
    grammar, firsts, follows = setup(["exp VAR"])
    assert follows["exp"] == {grammar.getEof()}


def test_follow_set_captured_nonterminal():
    grammar, firsts, follows = setup(["exp VAR", "test exp TEST"])
    assert follows["exp"] == {grammar.getEof(), "TEST"}


def test_follow_set_one_nonterminal():
    grammar, firsts, follows = setup(["exp VAR exp TEST exp", "exp TEST exp VAR exp", "exp "])
    assert follows["exp"] == {grammar.getEof(), "TEST", "VAR"}


def test_derive_empty():
    grammar, firsts, follows = setup([
        "exp",
        "exp VAR word",
        "test",
        "test TEST",
        "s exp test TWO",
        "word s NEW"
    ])
    assert follows["exp"] == {grammar.getEof(), "TEST"}
    assert follows["test"] == {"TWO"}
    assert follows["s"] == {"NEW"}
    assert follows["word"] == {grammar.getEof(), "TEST"}


def test_follow_set_empty_rule():
    grammar, firsts, follows = setup(["exp "])
    assert follows["exp"] == {grammar.getEof()}


def test__follow_set_with_terminal_after_captured_rule():
    grammar, firsts, follows = setup(["s b C", "s d b", "b A B", "b C s", "d D", "d "])
    assert follows["s"] == {grammar.getEof(), "C"}
    assert follows["b"] == {grammar.getEof(), "C"}
    assert follows["d"] == {"A", "C"}


def setup(lines):
    g = Grammar()
    for line in [line.split() for line in lines]:
        g.addRule(line[0], line[1:])
    firsts = build_first_sets(g)
    follows = build_follow_sets(g, firsts)
    return g, firsts, follows
