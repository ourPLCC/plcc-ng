from pytest import fixture, raises

from .Grammar import Grammar


@fixture
def grammar():
    return Grammar()

@fixture
def nonterminal():
    return 'nonTerminal'

@fixture
def terminal():
    return 'TERMINAL'

def test_empty_grammar(grammar):
    assert len(grammar.getNonterminalSet()) == 0
    assert len(grammar.getTerminals()) == 0
    assert grammar.getStartSymbol() == None

def test_add_rule(grammar, nonterminal, terminal):
    grammar.addRule(nonterminal, [terminal])
    assert grammar.getForms(nonterminal) == [tuple([terminal])]

def test_is_terminal(grammar, terminal):
    grammar.addRule('', [terminal])
    assert grammar.isTerminal(terminal) == True
    assert grammar.isNonterminal(terminal) == False

def test_is_nonterminal(grammar, nonterminal):
    grammar.addRule(nonterminal, [])
    assert grammar.isTerminal(nonterminal) == False
    assert grammar.isNonterminal(nonterminal) == True

def test_get_start_symbol_none(grammar):
    assert grammar.getStartSymbol() == None

def test_get_start_symbol(grammar, nonterminal):
    grammar.addRule(nonterminal, [])
    assert grammar.getStartSymbol() == nonterminal

def test_multiple_rules_one_nonterminal(grammar, nonterminal, terminal):
    grammar.addRule(nonterminal, [terminal])
    grammar.addRule(nonterminal, [])
    assert grammar.getForms(nonterminal) == [tuple([terminal]), tuple([])]

def test_add_multiple_nonterminals(grammar, nonterminal, terminal):
    grammar.addRule(nonterminal, [terminal])
    anotherNonterminal = getanotherNonterminal()
    grammar.addRule(anotherNonterminal, [])
    assert grammar.getForms(nonterminal) == [tuple([terminal])]
    assert grammar.getForms(anotherNonterminal) == [tuple([])]

def test_add_terminal_and_nonterminal_to_sets(grammar, nonterminal, terminal):
    anotherNonterminal = getanotherNonterminal()
    grammar.addRule(anotherNonterminal, [])
    grammar.addRule(nonterminal, [terminal, anotherNonterminal])
    assert grammar.getForms(anotherNonterminal) == [tuple([])]
    assert grammar.getForms(nonterminal) == [tuple([terminal, anotherNonterminal])]
    assert len(grammar.getNonterminalSet()) == 2
    assert len(grammar.getTerminals()) == 1
    assert nonterminal in grammar.getNonterminalSet()
    assert anotherNonterminal in grammar.getNonterminalSet()
    assert terminal in grammar.getTerminals()

def test_no_duplicate_terminals(grammar, nonterminal, terminal):
    grammar.addRule(nonterminal, [terminal])
    grammar.addRule(nonterminal, [terminal])
    assert len(grammar.getTerminals()) == 1
    assert terminal in grammar.getTerminals()

def test_no_duplicate_nonterminals(grammar, nonterminal, terminal):
    grammar.addRule(nonterminal, [terminal])
    grammar.addRule(nonterminal, [terminal])
    assert len(grammar.getNonterminalSet()) == 1
    assert nonterminal in grammar.getNonterminalSet()

def test_set_incompatible_nonterminal_raises_TypeError(grammar, terminal):
    with raises(TypeError):
        grammar.addRule([], [terminal])

def test_set_incompatible_symbols_in_form_raises_TypeError(grammar, nonterminal, terminal):
    with raises(TypeError):
        grammar.addRule(nonterminal, [[],terminal])

def test_non_iterable_form_raises_TypeError(grammar):
    valid_non_terminal = ''
    invalid_form = object()
    with raises(TypeError):
        grammar.addRule(valid_non_terminal, invalid_form)

def test_convert_terminals_to_nonterminals(grammar):
    grammar.addRule('a', ['b'])
    assertNonterminal(grammar, 'a')
    assertTerminal(grammar, 'b')
    grammar.addRule('b', ['a'])
    assertNonterminal(grammar, 'a')
    assertNonterminal(grammar, 'b')

def assertNonterminal(g: Grammar, nt):
    assert nt not in g.getTerminals()
    assert nt in g.getNonterminalSet()
    assert not g.isTerminal(nt)
    assert g.isNonterminal(nt)

def assertTerminal(g: Grammar, t):
    assert t in g.getTerminals()
    assert t not in g.getNonterminalSet()
    assert g.isTerminal(t)
    assert not g.isNonterminal(t)

def getanotherNonterminal():
    return 'nonTerminalDiff'
