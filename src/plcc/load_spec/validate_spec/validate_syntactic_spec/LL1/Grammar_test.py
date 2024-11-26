from pytest import raises, fixture
from .Grammar import generate_grammar
from .errors import InvalidFormException, InvalidNonterminalException

@fixture
def grammar():
    return generate_grammar()

@fixture
def nonterminal():
    return 'nonTerminal'

@fixture
def terminal():
    return 'TERMINAL'

def test_empty_grammar(grammar):
    assert len(grammar.getRules()) == 0
    assert grammar.getStartSymbol() == None

def test_add_rule(grammar, nonterminal, terminal):
    grammar.addRule(nonterminal, [terminal])
    assert grammar.getRules() == {nonterminal: [[terminal]]}

def test_is_terminal(grammar, terminal):
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
    assert grammar.getRules() == {nonterminal: [[terminal], []]}

def test_add_multiple_nonterminals(grammar, nonterminal, terminal):
    grammar.addRule(nonterminal, [terminal])
    anotherNonterminal = getanotherNonterminal()
    grammar.addRule(anotherNonterminal, [])
    assert grammar.getRules() == {nonterminal: [[terminal]], anotherNonterminal: [[]]}

def test_add_terminal_and_nonterminal_to_sets(grammar, nonterminal, terminal):
    anotherNonterminal = getanotherNonterminal()
    grammar.addRule(anotherNonterminal, [])
    grammar.addRule(nonterminal, [terminal, anotherNonterminal])
    assert grammar.getRules() == {anotherNonterminal: [[]], nonterminal: [[terminal, anotherNonterminal]]}
    assert len(grammar.getNonterminals()) == 2
    assert len(grammar.getTerminals()) == 1
    assert nonterminal in grammar.getNonterminals()
    assert anotherNonterminal in grammar.getNonterminals()
    assert terminal in grammar.getTerminals()

def test_no_duplicate_terminals(grammar, nonterminal, terminal):
    grammar.addRule(nonterminal, [terminal])
    grammar.addRule(nonterminal, [terminal])
    assert len(grammar.getTerminals()) == 1
    assert terminal in grammar.getTerminals()

def test_no_duplicate_nonterminals(grammar, nonterminal, terminal):
    grammar.addRule(nonterminal, [terminal])
    grammar.addRule(nonterminal, [terminal])
    assert len(grammar.getNonterminals()) == 1
    assert nonterminal in grammar.getNonterminals()

def test_invalid_nonterminal_throws_invalid_nonterminal_error(grammar, terminal):
    with raises(InvalidNonterminalException):
        grammar.addRule('', [terminal])

def test_invalid_form_list_throws_invalid_form_error(grammar, nonterminal, terminal):
    with raises(InvalidFormException):
        grammar.addRule(nonterminal, terminal)

def test_unhashable_form_list_symbol_throws_invalid_form_error(grammar, nonterminal, terminal):
    with raises(InvalidFormException):
        grammar.addRule(nonterminal, [[],terminal])

def getanotherNonterminal():
    return 'nonTerminalDiff'
