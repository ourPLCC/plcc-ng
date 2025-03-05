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
    assert table.getCell('S', 'a') == set([('B', 'c'), ('D', 'B')])
    assert table.getCell('S', 'c') == set([('B', 'c'), ('D', 'B')])
    assert table.getCell('S', 'd') == set([('D', 'B')])
    assert table.getCell('B', 'a') == set([('a', 'b')])
    assert table.getCell('B', 'c') == set([('c', 'S')])
    assert table.getCell('D', 'a') == set([()])
    assert table.getCell('D', 'c') == set([()])
    assert table.getCell('D', 'd') == set([('d',)])



def createGrammar(rules: list[str]) -> Grammar:
    g = Grammar()
    for r in rules:
        symbols = r.split()
        nonterminal = symbols[0]
        production = symbols[1:]
        g.addRule(nonterminal, production)
    return g
