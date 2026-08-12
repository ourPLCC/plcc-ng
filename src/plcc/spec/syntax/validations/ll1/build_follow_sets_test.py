from .build_first_sets import build_first_sets
from .build_follow_sets import build_follow_sets
from .Grammar import Grammar


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
    assert follows["exp"] == {grammar.getEof(), "TEST", "TWO"}
    assert follows["test"] == {"TWO"}
    assert follows["s"] == {"NEW"}
    assert follows["word"] == {grammar.getEof(), "TEST", "TWO"}


def test_follow_set_empty_rule():
    grammar, firsts, follows = setup(["exp "])
    assert follows["exp"] == {grammar.getEof()}


def test__follow_set_with_terminal_after_captured_rule():
    grammar, firsts, follows = setup(["s b C", "s d b", "b A B", "b C s", "d D", "d "])
    assert follows["s"] == {grammar.getEof(), "C"}
    assert follows["b"] == {grammar.getEof(), "C"}
    assert follows["d"] == {"A", "C"}


def test_left_recursive_nonterminal_inside_nullable_does_not_crash():
    """
    build_follow_sets should not raise RecursionError when a nullable
    nonterminal's first production expands into a left-recursive one.
    Reproduces the crash from: prog **= exp  with  exp ::= exp PLUS exp | NUM.
    """
    grammar, firsts, follows = setup([
        'prog explist',
        'explist exp explist',
        'explist',
        'exp exp PLUS exp',
        'exp NUM',
    ])
    assert follows is not None


def test_follow_propagates_eof_through_nullable_registered_second():
    """
    Regression test for issue #170: a nonterminal's nullability must be
    recognized even when its epsilon-producing alternative is registered
    after a non-empty one - the order arbno's internal desugaring always
    uses for its continuation nonterminal. Y needs its own production
    (`Y B`) so the Grammar model classifies it as a nonterminal at all -
    without one, Y auto-classifies as a terminal and never gets a FOLLOW
    entry computed in the first place, which would make this test pass
    for the wrong reason (an empty set is not `{'A', eof}`, but it would
    also not literally raise - always assert against a nonzero-length
    expected set to catch this class of test-authoring mistake).
    """
    grammar, firsts, follows = setup([
        'Start Y Z',
        'Y B',
        'Z A',
        'Z',
    ])
    assert follows['Y'] == {'A', grammar.getEof()}


def test_follow_propagates_eof_regardless_of_alternative_registration_order():
    """
    Same grammar, Z's two alternatives registered in opposite order in
    each of the two separate Grammar instances below. Compare each
    result against its OWN grammar's getEof() (not against each other
    directly) - Grammar.getEof() returns a fresh sentinel object() per
    instance, so follows-sets from two different setup() calls are never
    == to each other even when they're semantically identical.
    """
    g1, _, follows_epsilon_first = setup([
        'Start Y Z',
        'Y B',
        'Z',
        'Z A',
    ])
    g2, _, follows_epsilon_second = setup([
        'Start Y Z',
        'Y B',
        'Z A',
        'Z',
    ])
    assert follows_epsilon_first['Y'] == {'A', g1.getEof()}
    assert follows_epsilon_second['Y'] == {'A', g2.getEof()}


def test_follow_propagates_eof_through_arbno_desugared_continuation():
    """
    Mirrors _handle_arbno's desugaring of `<Prog> **= <Expr>` where Expr
    itself has a nested epsilon alternative (issue #166's original,
    abandoned grammar shape) - the continuation nonterminal (here Prog#)
    is always registered non-empty-form-first.
    """
    grammar, firsts, follows = setup([
        'Prog Expr Prog#',
        'Prog',
        'Prog# Expr Prog#',
        'Prog#',
        'Expr NUM ExprTail',
        'ExprTail PLUS NUM',
        'ExprTail',
    ])
    assert grammar.getEof() in follows['ExprTail']


def test_follow_set_walks_past_nullable_symbol_to_next_non_nullable():
    """
    Regression test for issue #188: the forward walk from a nonterminal's
    occurrence must continue past a nullable next symbol and add FIRST of
    each subsequent symbol until it hits one that cannot derive empty,
    rather than stopping after the single next symbol.

    S -> A B C, A -> a | epsilon, B -> b | epsilon, C -> c.
    B is nullable, so FOLLOW(A) must include FIRST(B) - {epsilon} = {b}
    AND FIRST(C) = {c}, not just {b}.
    """
    grammar, firsts, follows = setup([
        'S A B C',
        'A a',
        'A',
        'B b',
        'B',
        'C c',
    ])
    assert follows['A'] == {'b', 'c'}


def setup(lines):
    g = Grammar()
    for line in [line.split() for line in lines]:
        g.addRule(line[0], line[1:])
    firsts = build_first_sets(g)
    follows = build_follow_sets(g, firsts)
    return g, firsts, follows
