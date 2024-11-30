from pytest import raises
from .build_parsing_table import build_parsing_table, Table
from collections import defaultdict

from .build_spec_grammar import build_spec_grammar
from plcc.load_spec.load_rough_spec.parse_lines import Line
from plcc.load_spec.load_rough_spec.parse_dividers import parse_dividers
from plcc.load_spec.parse_spec.parse_syntactic_spec.parse_syntactic_spec import parse_syntactic_spec
from .LL1Wrapper import LL1Wrapper

def test_productions_which_share_both_rule_and_firstSet_terminals_result_in_multiple_cell_entries():
    firstSets = {
        'd' : {"D", ""},
        'b' : {"A", "C"},
        's' : {"A", "C", "D"},
        'A B' : {"A"},
        'C s' : {"C"},
        "D" : {"D"},
        "" : {""},

        # productions in same rule that share terminals "A" and "C" in firstSet
        'b C' :  {"A", "C"},
        'd b' : {"D", "A", "C"},
    }
    followSets = {
        'd' : {"A", "C"},
        'b' : {"C", chr(26)},
        's' : {chr(26), "C"}
    }

    rules = createRules([
        "<s> ::= <b> C", "<s> ::= <d> <b>", # productions that share firstSet terminals
        "<b> ::= A B", "<b> ::= C <s>", "<d> ::= D", "<d> ::= "])
    table = build_parsing_table(firstSets, followSets, rules)
    assert table.getCell('s', 'D') == ["d b"]
    assert table.getCell('b', 'A') == ["A B"]
    assert table.getCell('b', 'C') == ["C s"]
    assert table.getCell('d', 'A') == [""]
    assert table.getCell('d', 'C') == [""]
    assert table.getCell('d', 'D') == ["D"]

    # multiple cell entries for each matching firstSet terminal and rule's LHS nonterminal
    assert table.getCell('s', 'A') == ["b C", 'd b']
    assert table.getCell('s', 'C') == ["b C", 'd b']
    assert len(table.getFilledCellLocations()) == 8

def createRules(rules: list[str]) -> dict[LL1Wrapper, list[list[LL1Wrapper]]]:
    return createGrammarWithSpec(rules).getRules()

def createGrammarWithSpec(lines):
    syntacticSpec = parse_syntactic_spec([makeDivider()] + [makeLine(line) for line in lines])
    return build_spec_grammar(syntacticSpec)

def makeDivider(string="%", lineNumber=0, file=""):
    return parse_dividers([makeLine(string, lineNumber, file)])

def makeLine(string, lineNumber=0, file=""):
    return Line(string, lineNumber, file)


