from pytest import raises
from .build_parsing_table import build_parsing_table, Table
from collections import defaultdict



def test_left_recursion_results_in_multiple_cell_entries():
    firstSets = {
        "s" : {"","A","C","D"},
        "x" : {"","A","C","D"},
        "y" : {"","A"},
        "z" : {"C","D"},
        "" : {""},
        "x y z" : {"A","C","D"},
        "x s" : {"A", "C", "D"},
        "A y B" : {"A"},
        "C z" : {"C"},
        "D" : {"D"}
    }
    followSets = {
        "s" : {chr(26), "A","C","D"},
        "x" : {"A","C","D"},
        "y" : {"B","C","D"},
        "z" : {chr(26), "A","C","D"}
    }
    rules = {
        "s" : ["","x y z"],
        "x" : ["","x s"], # the rule <x> ::= <x> <s> is left recursive
        "y" : ["","A y B"],
        "z" : ["C z", "D"]
    }
    table = build_parsing_table(firstSets, followSets, rules)

    assert table.getCell('s','A') == ["", "x y z"]
    assert table.getCell('s','C') == ["", "x y z"]
    assert table.getCell('s', 'D') == ["", "x y z"]
    assert table.getCell('s', '\x1a') == [""]

    # multiple cell entries due to left recursion
    assert table.getCell('x', 'A') == ["", "x s"]
    assert table.getCell('x', 'C') == ["", "x s"]
    assert table.getCell('x', 'D') == ["", "x s"]

    assert table.getCell('y', 'A') == ["A y B"]
    assert table.getCell('y', 'B') == [""]
    assert table.getCell('y', 'C') == [""]
    assert table.getCell('y', 'D') == [""]

    assert table.getCell('z', 'C') == ["C z"]
    assert table.getCell('z', 'D') == ["D"]
    assert len(table.getFilledCellLocations()) == 13

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
    rules = {
        "b": ["A B", 'C s'],
        "d": ["D", ""],
        "s": ["b C", "d b"] # rule which contains productions that share firstSet terminals
    }
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
