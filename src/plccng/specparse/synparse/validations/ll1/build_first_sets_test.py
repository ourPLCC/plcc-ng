from .build_first_sets import build_first_sets
from .Grammar import Grammar


def test_first_set_terminal():
    grammar, checker = setupChecker(["exp VAR"])
    assert checker["exp"] == {"VAR"}
    assert checker["VAR"] == {"VAR"}

def test_first_set_multiple_terminals():
    grammar, checker = setupChecker(["exp VAR TWO THREE"])
    assert checker["exp"] == {"VAR"}
    assert checker["VAR"] == {"VAR"}
    assert checker["TWO"] == {"TWO"}
    assert checker["THREE"] == {"THREE"}
    assert checker[("VAR", "TWO", "THREE")] == {"VAR"}


def test_first_set_nonterminal():
    grammar, checker = setupChecker(["exp VAR", "test exp"])
    assert checker["exp"] == {"VAR"}
    assert checker["test"] == {"VAR"}
    assert checker["VAR"] == {"VAR"}


def test_first_set_multiple_nonterminals_takes_first():
    grammar, checker = setupChecker(["exp VAR", "test exp two", "two TWO"])
    assert checker["exp"] == {"VAR"}
    assert checker["test"] == {"VAR"}
    assert checker["two"] == {"TWO"}
    assert checker["VAR"] == {"VAR"}
    assert checker["TWO"] == {"TWO"}
    assert checker[("exp", "two")] == {"VAR"}


def test_first_set_derives_epsilon():
    grammar, checker = setupChecker(["exp"])
    assert checker["exp"] == {grammar.getEpsilon()}


def test_first_set_derives_epsilon_plus_terminal():
    grammar, checker = setupChecker(["exp VAR", "exp"])
    assert checker["exp"] == {"VAR", grammar.getEpsilon()}
    assert checker["VAR"] == {"VAR"}
    assert checker[grammar.getEpsilon()] == {grammar.getEpsilon()}


def test_first_set_derives_epsilon_plus_nonterminal():
    grammar, checker = setupChecker(["exp VAR", "exp", "test exp"])
    assert checker["exp"] == {"VAR", grammar.getEpsilon()}
    assert checker["test"] == {"VAR", grammar.getEpsilon()}
    assert checker["VAR"] == {"VAR"}


def test_first_set_multiple_nonterminals_with_terminal():
    grammar, checker = setupChecker(["exp", "exp VAR", "test exp two THREE", "two TWO", "two"])
    assert checker["exp"] == {"VAR", grammar.getEpsilon()}
    assert checker["test"] == {"VAR", "TWO", "THREE"}
    assert checker["two"] == {"TWO", grammar.getEpsilon()}
    assert checker["VAR"] == {"VAR"}
    assert checker["TWO"] == {"TWO"}
    assert checker["THREE"] == {"THREE"}
    assert checker[("exp", "two", "THREE")] == {"VAR", "TWO", "THREE"}


def test_first_set_multiple_nonterminals_that_derive_epsilon():
    grammar, checker = setupChecker(["exp", "exp VAR", "test exp two", "two TWO", "two"])
    assert checker["exp"] == {"VAR", grammar.getEpsilon()}
    assert checker["test"] == {"VAR", "TWO", grammar.getEpsilon()}
    assert checker["two"] == {"TWO", grammar.getEpsilon()}
    assert checker["VAR"] == {"VAR"}
    assert checker["TWO"] == {"TWO"}
    assert checker[("exp", "two")] == {"VAR", "TWO", grammar.getEpsilon()}


def test_first_set_multiple_rhs_first_sets():
    grammar, checker = setupChecker(["b A B", "b C s", "d D", "d ", "s b C", "s d b"])
    assert checker["d"] == {"D", grammar.getEpsilon()}
    assert checker["b"] == {"A", "C"}
    assert checker["s"] == {"A", "C", "D"}
    assert checker[("A", "B")] == {"A"}
    assert checker[("C", "s")] == {"C"}
    assert checker["D"] == {"D"}
    assert checker[grammar.getEpsilon()] == {grammar.getEpsilon()}
    assert checker[("b", "C")] == {"A", "C"}
    assert checker[("d", "b")] == {"D", "A", "C"}


def setupChecker(lines):
    g = Grammar()
    for line in [line.split() for line in lines]:
        g.addRule(line[0], line[1:])
    checker = build_first_sets(g)
    return g, checker
