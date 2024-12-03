from .Grammar import Grammar
from .build_first_sets import build_first_sets
from .build_follow_sets import build_follow_sets


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
    grammar, firsts, follows = setup(["exp ", "exp VAR word", "test ", "test TEST", "s exp test TWO", "word s NEW"])
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
