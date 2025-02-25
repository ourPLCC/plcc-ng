from pytest import raises
from plccng.roughparse import fromlines
from plccng.lineparse import Line

from ...InvalidSyntacticSpecException import InvalidSyntacticSpecException
from ...InvalidSymbolException import InvalidSymbolException

from ...parse_syntactic_spec import parse_syntactic_spec
from .LL1Wrapper import wrap_ll1
from .build_spec_grammar import build_spec_grammar


def test_init():
    grammar = createGrammarWithSpec([""])
    assertInit(grammar)

def test_process_syntactic_spec():
    grammar = createGrammarWithSpec(['<exp> ::= VAR'])
    assertRuleCount(grammar, 1)

def test_get_start_symbol_name():
    grammar = createGrammarWithSpec(["<exp> ::= VAR", '<test> ::= TERM'])
    assert grammar.getStartSymbol() == getDefaultNonterminalName()

def test_add_rule():
    grammar = createGrammarWithSpec(["<exp> ::= VAR"])
    newRule = createRule('<test> ::= TWO')
    grammar.addRule(newRule.lhs, newRule.rhsSymbolList)
    assertRuleCount(grammar, 2)

def test_add_duplicate_rule():
    grammar = createGrammarWithSpec(["<exp> ::= VAR", "<exp> ::= VAR"])
    assertRuleCount(grammar, 1)

def test_multiple_rules_same_lhs():
    grammar = createGrammarWithSpec(["<noun> ::= ONE TWO", "<noun> ::= WORD WORD WORD"])
    assertRuleCount(grammar, 1)
    expectedSymbolRulesLength, expectedFormListLength = 2, 5
    assertRuleAndFormLength(grammar, expectedSymbolRulesLength, expectedFormListLength)
    assert len(grammar.getTerminals()) == 3

def test_get_terminals():
    grammar = createGrammarWithSpec(["<noun> ::= WORD <TERM> THIS"])
    assert len(grammar.getTerminals()) == 3

def test_get_duplicate_terminals():
    grammar = createGrammarWithSpec(["<noun> ::= WORD WORD WORD <TERM> THIS"])
    assert len(grammar.getTerminals()) == 3

def test_get_nonterminals():
    grammar = createGrammarWithSpec(["<noun> ::= WORD", "<test> ::= TERM <free>"])
    assert len(grammar.getNonterminals()) == 3

def test_get_duplicate_nonterminals():
    grammar = createGrammarWithSpec(["<noun> ::= WORD", "<test> ::= TERM <free>", "<free> ::= "])
    assert len(grammar.getNonterminals()) == 3

def test_invalid_form_parameter():
    grammar = createGrammarWithSpec(["<noun> ::= WORD"])
    with raises(InvalidSymbolException):
        grammar.addRule(grammar.getStartSymbol(), ["invalid"])

def test_add_rule_invalid_lhs_parameter():
    grammar = createGrammarWithSpec(["<exp> ::= VAR"])
    with raises(InvalidSymbolException):
        grammar.addRule("invalid", [])

def test_invalid_syntactic_spec_handling():
    with raises(InvalidSyntacticSpecException):
        makeSpecGrammar("syntactic_spec")


def assertInit(grammar):
    assert grammar.getEpsilon() == getEpsilon()
    assert grammar.getEOF() == getEOF()
    assertRuleCount(grammar, 0)
    assert grammar.getStartSymbol() is None

def assertRuleCount(grammar, count):
    assert len(grammar.getRules()) == count

def assertRuleAndFormLength(grammar, expectedSymbolRulesLength, expectedFormListLength):
    startSymbol = grammar.getStartSymbol()
    symbolRules = grammar.getRules()[startSymbol]
    assert len(symbolRules) == expectedSymbolRulesLength
    count = sum(len(form) for form in symbolRules)
    assert count == expectedFormListLength

def createRule(line):
    return parse_syntactic_spec([makeDivider(), makeLine(line)])[0]

def createGrammarWithSpec(lines):
    syntacticSpec = parse_syntactic_spec([makeDivider()] + [makeLine(line) for line in lines])
    return makeSpecGrammar(syntacticSpec)

def makeDivider(string="%", lineNumber=0, file=""):
    return fromlines([makeLine(string, lineNumber, file)])

def makeLine(string, lineNumber=0, file=""):
    return Line(string, lineNumber, file)

def makeSpecGrammar(syntacticSpec):
    return build_spec_grammar(syntacticSpec)

def getEpsilon():
    return wrap_ll1("", None)

def getEOF():
    return wrap_ll1(chr(26), None)

def getDefaultNonterminalName():
    return "exp"
