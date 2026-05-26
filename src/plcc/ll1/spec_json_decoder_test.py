import pytest
from plcc.ll1.spec_json_decoder import decode, Rule


def _spec(rules):
    return {"lexical": {"ruleList": []}, "syntax": {"rules": rules}, "semantics": []}


def _rule(lhs_name, rhs_syms, alt_name=None):
    return {
        "line": {"string": "", "number": 0, "file": ""},
        "lhs": {"name": lhs_name, "isTerminal": False, "altName": alt_name, "isCapturing": False},
        "rhsSymbolList": rhs_syms,
    }


def _terminal(name, capturing=False, alt_name=None):
    d = {"name": name, "isTerminal": True, "isCapturing": capturing}
    if alt_name is not None:
        d["altName"] = alt_name
    return d


def _nonterminal(name, capturing=False, alt_name=None):
    d = {"name": name, "isTerminal": False, "isCapturing": capturing}
    if alt_name is not None:
        d["altName"] = alt_name
    return d


def test_rule_is_dataclass_with_alt_and_fields():
    r = Rule(alt="Add", fields=["left", None])
    assert r.alt == "Add"
    assert r.fields == ["left", None]


def test_rule_alt_can_be_none():
    r = Rule(alt=None, fields=[])
    assert r.alt is None


def test_empty_grammar():
    grammar, productions, arbno_rules = decode(_spec([]))
    assert grammar.getStartSymbol() is None
    assert productions == {}


def test_single_rule_noncapturing():
    grammar, productions, arbno_rules = decode(_spec([
        _rule("program", [_terminal("NUM")])
    ]))
    assert grammar.getStartSymbol() == "program"
    assert list(grammar.getForms("program")) == [("NUM",)]
    assert productions == {("program", ("NUM",)): Rule(alt=None, fields=[None])}


def test_epsilon_rule():
    grammar, productions, arbno_rules = decode(_spec([
        _rule("empty", [])
    ]))
    assert grammar.getStartSymbol() == "empty"
    assert list(grammar.getForms("empty")) == [()]
    assert productions == {("empty", ()): Rule(alt=None, fields=[])}


def test_capturing_terminal_uses_name_lower():
    grammar, productions, arbno_rules = decode(_spec([
        _rule("E", [_terminal("NUM", capturing=True)])
    ]))
    assert productions == {("E", ("NUM",)): Rule(alt=None, fields=["num"])}


def test_capturing_terminal_uses_alt_name():
    grammar, productions, arbno_rules = decode(_spec([
        _rule("E", [_terminal("NUM", capturing=True, alt_name="value")])
    ]))
    assert productions == {("E", ("NUM",)): Rule(alt=None, fields=["value"])}


def test_capturing_nonterminal_uses_name_lower():
    grammar, productions, arbno_rules = decode(_spec([
        _rule("E", [_nonterminal("Term", capturing=True)])
    ]))
    assert productions == {("E", ("Term",)): Rule(alt=None, fields=["term"])}


def test_multiple_symbols():
    grammar, productions, arbno_rules = decode(_spec([
        _rule("E", [_nonterminal("T", capturing=True), _terminal("PLUS"), _nonterminal("E", capturing=True, alt_name="r")])
    ]))
    assert productions == {("E", ("T", "PLUS", "E")): Rule(alt=None, fields=["t", None, "r"])}


def test_start_symbol_is_first_rule_lhs():
    grammar, productions, arbno_rules = decode(_spec([
        _rule("first", [_terminal("A")]),
        _rule("second", [_terminal("B")]),
    ]))
    assert grammar.getStartSymbol() == "first"


def test_lhs_alt_name_captured_in_rule():
    grammar, productions, arbno_rules = decode(_spec([
        _rule("expr", [_terminal("PLUS"), _nonterminal("expr"), _nonterminal("expr")], alt_name="Add"),
        _rule("expr", [_terminal("NUM")], alt_name="Num"),
    ]))
    assert productions[("expr", ("PLUS", "expr", "expr"))].alt == "Add"
    assert productions[("expr", ("NUM",))].alt == "Num"


def test_lhs_alt_name_none_when_absent():
    grammar, productions, arbno_rules = decode(_spec([
        _rule("program", [_terminal("NUM")])
    ]))
    assert productions[("program", ("NUM",))].alt is None


def _arbno_rule(lhs_name, rhs_syms, separator_name):
    sep = None if separator_name is None else {
        "name": separator_name, "isTerminal": True, "isCapturing": False
    }
    return {
        "line": {"string": "", "number": 0, "file": ""},
        "lhs": {"name": lhs_name, "isTerminal": False, "altName": None, "isCapturing": False},
        "rhsSymbolList": rhs_syms,
        "separator": sep,
    }


def test_decode_returns_3_tuple():
    grammar, productions, arbno_rules = decode(_spec([]))
    assert isinstance(arbno_rules, dict)


def test_non_arbno_rules_not_in_arbno_rules():
    grammar, productions, arbno_rules = decode(_spec([
        _rule("program", [_terminal("NUM")])
    ]))
    assert arbno_rules == {}


def test_separator_arbno_in_arbno_rules():
    spec = _spec([
        _arbno_rule("rands",
                    [_nonterminal("expr", capturing=True, alt_name="expr")],
                    "COMMA"),
        _rule("expr", [_terminal("NUM")]),
    ])
    grammar, productions, arbno_rules = decode(spec)
    assert "rands" in arbno_rules


def test_separator_arbno_rhs_field_has_list_suffix():
    spec = _spec([
        _arbno_rule("rands",
                    [_nonterminal("expr", capturing=True, alt_name="expr")],
                    "COMMA"),
        _rule("expr", [_terminal("NUM")]),
    ])
    grammar, productions, arbno_rules = decode(spec)
    assert arbno_rules["rands"]["rhs"] == [
        {"field": "exprList", "symbol": "expr", "is_terminal": False}
    ]


def test_separator_arbno_separator_field():
    spec = _spec([
        _arbno_rule("rands",
                    [_nonterminal("expr", capturing=True, alt_name="expr")],
                    "COMMA"),
        _rule("expr", [_terminal("NUM")]),
    ])
    grammar, productions, arbno_rules = decode(spec)
    assert arbno_rules["rands"]["separator"] == "COMMA"


def test_plain_arbno_separator_is_none():
    spec = _spec([
        _arbno_rule("cmds",
                    [_nonterminal("cmd", capturing=True, alt_name="cmd")],
                    None),
        _rule("cmd", [_terminal("X")]),
    ])
    grammar, productions, arbno_rules = decode(spec)
    assert arbno_rules["cmds"]["separator"] is None


def test_arbno_expansion_adds_internal_rules_to_grammar():
    spec = _spec([
        _arbno_rule("rands",
                    [_nonterminal("expr", capturing=True, alt_name="expr")],
                    "COMMA"),
        _rule("expr", [_terminal("NUM")]),
    ])
    grammar, productions, arbno_rules = decode(spec)
    nts = grammar.getNonterminalSet()
    assert "rands" in nts
    assert "rands#" in nts


def test_arbno_terminal_rhs_item():
    spec = _spec([
        _arbno_rule("tokens",
                    [_terminal("NUM", capturing=True, alt_name="num")],
                    None),
    ])
    grammar, productions, arbno_rules = decode(spec)
    assert arbno_rules["tokens"]["rhs"] == [
        {"field": "numList", "symbol": "NUM", "is_terminal": True}
    ]
