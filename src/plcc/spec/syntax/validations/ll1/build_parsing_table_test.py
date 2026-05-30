from .build_first_sets import build_first_sets
from .build_follow_sets import build_follow_sets
from .build_parsing_table import build_parsing_table
from .Grammar import Grammar


def test_productions_which_share_both_rule_and_firstSet_terminals_result_in_multiple_cell_entries():
    grammar = createGrammar([
        'S B c',
        'S D B',
        'B a b',
        'B c S',
        'D d',
        'D'
    ])
    firsts = build_first_sets(grammar)
    follows = build_follow_sets(grammar, firsts)
    table = build_parsing_table(firsts, follows, grammar)
    assert set(table.getCell('S', 'a')) == {('B', 'c'), ('D', 'B')}
    assert set(table.getCell('S', 'c')) == {('B', 'c'), ('D', 'B')}
    assert set(table.getCell('S', 'd')) == {('D', 'B')}
    assert set(table.getCell('B', 'a')) == {('a', 'b')}
    assert set(table.getCell('B', 'c')) == {('c', 'S')}
    assert set(table.getCell('D', 'a')) == {()}
    assert set(table.getCell('D', 'c')) == {()}
    assert set(table.getCell('D', 'd')) == {('d',)}



def test_two_rules_with_identical_bodies_produce_two_cell_entries():
    grammar = createGrammar([
        'E x',
        'E x'
    ])
    firsts = build_first_sets(grammar)
    follows = build_follow_sets(grammar, firsts)
    table = build_parsing_table(firsts, follows, grammar)
    assert len(table.getCell('E', 'x')) == 2


def test_first_follow_overlap_does_not_create_false_conflict():
    # Grammar: C → A x | A → B | B → x | B → (epsilon)
    # FIRST(A→B) = {x, ε}; FOLLOW(A) = {x}
    # Rule (A→B) predicts x via both FIRST and FOLLOW — must appear in cell (A,x) only once.
    grammar = createGrammar([
        'C A x',
        'A B',
        'B x',
        'B'
    ])
    firsts = build_first_sets(grammar)
    follows = build_follow_sets(grammar, firsts)
    table = build_parsing_table(firsts, follows, grammar)
    assert len(table.getCell('A', 'x')) == 1


def createGrammar(rules: list[str]) -> Grammar:
    g = Grammar()
    for r in rules:
        symbols = r.split()
        nonterminal = symbols[0]
        production = symbols[1:]
        g.addRule(nonterminal, production)
    return g
