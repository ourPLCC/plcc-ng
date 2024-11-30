from plcc.load_spec.load_rough_spec.parse_dividers import parse_dividers
from plcc.load_spec.load_rough_spec.parse_lines import Line
from .build_follow_sets import build_follow_sets
from .build_spec_grammar import build_spec_grammar
from plcc.load_spec.parse_spec.parse_syntactic_spec.parse_syntactic_spec import parse_syntactic_spec

def test_follow_set_one_rule():
    checker = setupChecker(["<exp> ::= VAR"])
    assert checker["exp"] == {getEOF()}

def test_follow_set_captured_nonterminal():
    checker = setupChecker(["<exp> ::= VAR", "<test> ::= <exp> TEST"])
    assert checker["exp"] == {getEOF(), "TEST"}

def test_follow_set_one_nonterminal():
    checker = setupChecker(["<exp> ::= VAR <exp> TEST <exp>", "<exp> ::= TEST <exp> VAR <exp>", "<exp> ::= "])
    assert checker["exp"] == {getEOF(), "TEST", "VAR"}

def test_derive_empty():
    checker = setupChecker(["<exp> ::= ", "<exp> ::= VAR <word>", "<test> ::= ", "<test> ::= TEST", "<s> ::= <exp> <test> TWO", "<word> ::= <s> NEW"])
    assert checker["exp"] == {getEOF(), "TEST"}
    assert checker["test"] == {"TWO"}
    assert checker["s"] == {"NEW"}
    assert checker["word"] == {getEOF(), "TEST"}

def test_follow_set_empty_rule():
    checker = setupChecker(["<exp> ::= "])
    assert checker["exp"] == {getEOF()}

def test__follow_set_with_terminal_after_captured_rule():
    checker = setupChecker(["<s> ::= <b> C", "<s> ::= <d> <b>", "<b> ::= A B", "<b> ::= C <s>", "<d> ::= D", "<d> ::= "])
    assert checker["s"] == {getEOF(), "C"}
    assert checker["b"] == {getEOF(), "C"}
    assert checker["d"] == {"A", "C"}


def createGrammarWithSpec(lines):
    syntacticSpec = parse_syntactic_spec([makeDivider()] + [makeLine(line) for line in lines])
    return makeSpecGrammar(syntacticSpec)

def setupChecker(lines):
    grammar = createGrammarWithSpec(lines)
    checker = build_follow_sets(grammar)
    return checker

def makeDivider(string="%", lineNumber=0, file=""):
    return parse_dividers([makeLine(string, lineNumber, file)])

def makeLine(string, lineNumber=0, file=""):
    return Line(string, lineNumber, file)

def makeSpecGrammar(syntacticSpec):
    return build_spec_grammar(syntacticSpec)

def getEOF():
    syntacticSpec = parse_syntactic_spec([makeDivider(), makeLine("<eof> ::= THIS IS ONLY FOR GETTING EOF")])
    grammar = makeSpecGrammar(syntacticSpec)
    return grammar.getEOF().name
