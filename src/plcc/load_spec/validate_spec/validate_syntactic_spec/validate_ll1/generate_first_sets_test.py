from pytest import raises
from plcc.load_spec.load_rough_spec.parse_dividers import parse_dividers
from plcc.load_spec.load_rough_spec.parse_lines import Line
from .generate_first_sets import generate_first_sets
from .create_spec_grammar import create_spec_grammar
from plcc.load_spec.parse_spec.parse_syntactic_spec.parse_syntactic_spec import parse_syntactic_spec
from .errors import LeftRecursionException

def test_first_set_terminal():
    checker = setupChecker(["<exp> ::= VAR"])
    assert checker["exp"] == {"VAR"}
    assert checker["VAR"] == {"VAR"}

def test_first_set_multiple_terminals():
    checker = setupChecker(["<exp> ::= VAR TWO THREE"])
    assert checker["exp"] == {"VAR"}
    assert checker["VAR"] == {"VAR"}
    assert checker["TWO"] == {"TWO"}
    assert checker["THREE"] == {"THREE"}
    assert checker["VAR TWO THREE"] == {"VAR"}

def test_first_set_nonterminal():
    checker = setupChecker(["<exp> ::= VAR", "<test> ::= <exp>"])
    assert checker["exp"] == {"VAR"}
    assert checker["test"] == {"VAR"}
    assert checker["VAR"] == {"VAR"}

def test_first_set_multiple_nonterminals_takes_first():
    checker = setupChecker(["<exp> ::= VAR", "<test> ::= <exp> <two>", "<two> ::= TWO"])
    assert checker["exp"] == {"VAR"}
    assert checker["test"] == {"VAR"}
    assert checker["two"] == {"TWO"}
    assert checker["VAR"] == {"VAR"}
    assert checker["TWO"] == {"TWO"}
    assert checker["exp two"] == {"VAR"}

def test_first_set_derives_epsilon():
    checker = setupChecker(["<exp> ::= "])
    assert checker["exp"] == {getEpsilon()}

def test_first_set_derives_epsilon_plus_terminal():
    checker = setupChecker(["<exp> ::= VAR", "<exp> ::= "])
    assert checker["exp"] == {"VAR", getEpsilon()}
    assert checker["VAR"] == {"VAR"}
    assert checker[""] == {getEpsilon()}

def test_first_set_derives_epsilon_plus_nonterminal():
    checker = setupChecker(["<exp> ::= VAR", "<exp> ::= ", "<test> ::= <exp>"])
    assert checker["exp"] == {"VAR", getEpsilon()}
    assert checker["test"] == {"VAR", getEpsilon()}
    assert checker["VAR"] == {"VAR"}

def test_first_set_multiple_nonterminals_with_terminal():
    checker = setupChecker(["<exp> ::= ", "<exp> ::= VAR", "<test> ::= <exp> <two> THREE", "<two> ::= TWO", "<two> ::= "])
    assert checker["exp"] == {"VAR", getEpsilon()}
    assert checker["test"] == {"VAR", "TWO", "THREE"}
    assert checker["two"] == {"TWO", getEpsilon()}
    assert checker["VAR"] == {"VAR"}
    assert checker["TWO"] == {"TWO"}
    assert checker["THREE"] == {"THREE"}
    assert checker["exp two THREE"] == {"VAR", "TWO", "THREE"}

def test_first_set_multiple_nonterminals_that_derive_epsilon():
    checker = setupChecker(["<exp> ::= ", "<exp> ::= VAR", "<test> ::= <exp> <two>", "<two> ::= TWO", "<two> ::= "])
    assert checker["exp"] == {"VAR", getEpsilon()}
    assert checker["test"] == {"VAR", "TWO", getEpsilon()}
    assert checker["two"] == {"TWO", getEpsilon()}
    assert checker["VAR"] == {"VAR"}
    assert checker["TWO"] == {"TWO"}
    assert checker["exp two"] == {"VAR", "TWO", getEpsilon()}

def test_first_set_multiple_rhs_first_sets():
    checker = setupChecker(["<b> ::= A B", "<b> ::= C <s>", "<d> ::= D", "<d> ::= ", "<s> ::= <b> C", "<s> ::= <d> <b>"])
    assert checker["d"] == {"D", getEpsilon()}
    assert checker["b"] == {"A", "C"}
    assert checker["s"] == {"A", "C", "D"}
    assert checker["A B"] == {"A"}
    assert checker["C s"] == {"C"}
    assert checker["D"] == {"D"}
    assert checker[""] == {getEpsilon()}
    assert checker["b C"] == {"A", "C"}
    assert checker["d b"] == {"D", "A", "C"}

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
