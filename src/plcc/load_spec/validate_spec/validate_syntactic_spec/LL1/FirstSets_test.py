from pytest import raises
from plcc.load_spec.load_rough_spec.parse_dividers import parse_dividers
from plcc.load_spec.load_rough_spec.parse_lines import Line
from .FirstSets import generate_first_sets
from .SpecGrammar import create_spec_grammar
from plcc.load_spec.parse_spec.parse_syntactic_spec.parse_syntactic_spec import parse_syntactic_spec
from .errors import LeftRecursionException

def test_first_set_terminal():
    checker = setupChecker(["<exp> ::= VAR"])
    assert checker["exp"] == {"VAR"}

def test_first_set_multiple_terminals():
    checker = setupChecker(["<exp> ::= VAR TWO THREE"])
    assert checker["exp"] == {"VAR"}

def test_first_set_nonterminal():
    checker = setupChecker(["<exp> ::= VAR", "<test> ::= <exp>"])
    assert checker["exp"] == {"VAR"}
    assert checker["test"] == {"VAR"}

def test_first_set_multiple_nonterminals_takes_first():
    checker = setupChecker(["<exp> ::= VAR", "<test> ::= <exp> <two>", "<two> ::= TWO"])
    assert checker["exp"] == {"VAR"}
    assert checker["test"] == {"VAR"}
    assert checker["two"] == {"TWO"}

def test_first_set_derives_epsilon():
    checker = setupChecker(["<exp> ::= "])
    assert checker["exp"] == {getEpsilon()}

def test_first_set_derives_epsilon_plus_terminal():
    checker = setupChecker(["<exp> ::= VAR", "<exp> ::= "])
    assert checker["exp"] == {"VAR", getEpsilon()}

def test_first_set_derives_epsilon_plus_nonterminal():
    checker = setupChecker(["<exp> ::= VAR", "<exp> ::= ", "<test> ::= <exp>"])
    assert checker["exp"] == {"VAR", getEpsilon()}
    assert checker["test"] == {"VAR", getEpsilon()}

def test_first_set_multiple_nonterminals_with_terminal():
    checker = setupChecker(["<exp> ::= ", "<exp> ::= VAR", "<test> ::= <exp> <two> THREE", "<two> ::= TWO", "<two> ::= "])
    assert checker["exp"] == {"VAR", getEpsilon()}
    assert checker["test"] == {"VAR", "TWO", "THREE"}
    assert checker["two"] == {"TWO", getEpsilon()}

def test_first_set_multiple_nonterminals_that_derive_epsilon():
    checker = setupChecker(["<exp> ::= ", "<exp> ::= VAR", "<test> ::= <exp> <two>", "<two> ::= TWO", "<two> ::= "])
    assert checker["exp"] == {"VAR", getEpsilon()}
    assert checker["test"] == {"VAR", "TWO", getEpsilon()}
    assert checker["two"] == {"TWO", getEpsilon()}

def test_direct_left_recursion_throws_error():
    with raises(LeftRecursionException):
        checker = setupChecker(["<exp> ::= <exp> TEST"])

def test_indirect_left_recursion_throws_error():
    with raises(LeftRecursionException):
        checker = setupChecker(["<exp> ::= <test>", "<test> ::= <exp>"])

def test_complex_indirect_left_recursion_throws_error():
    with raises(LeftRecursionException):
        checker = setupChecker(["<exp> ::= <test>", "<test> ::= <new>", "<new> ::= <exp>"])

def createGrammarWithSpec(lines):
    syntacticSpec = parse_syntactic_spec([makeDivider()] + [makeLine(line) for line in lines])
    return makeSpecGrammar(syntacticSpec)

def setupChecker(lines):
    grammar = createGrammarWithSpec(lines)
    checker = generate_first_sets(grammar)
    return checker

def makeDivider(string="%", lineNumber=0, file=""):
    return parse_dividers([makeLine(string, lineNumber, file)])

def makeLine(string, lineNumber=0, file=""):
    return Line(string, lineNumber, file)

def makeSpecGrammar(syntacticSpec):
    return create_spec_grammar(syntacticSpec)

def getEpsilon():
    syntacticSpec = parse_syntactic_spec([makeDivider(), makeLine("<epsilon> ::= THIS IS ONLY FOR GETTING EPSILON")])
    grammar = makeSpecGrammar(syntacticSpec)
    return grammar.getEpsilon().name
