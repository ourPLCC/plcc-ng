from plcc.spec.syntax.validations.ll1.Grammar import Grammar
from plcc.ll1.ll1_result_builder import build_ll1_result


def _simple_grammar():
    """program → NUM (not capturing)"""
    g = Grammar()
    g.addRule("program", ["NUM"])
    fm = {("program", ("NUM",)): [None]}
    return g, fm


def _epsilon_grammar():
    """rest →  (epsilon)"""
    g = Grammar()
    g.addRule("rest", [])
    fm = {("rest", ()): []}
    return g, fm


def _conflict_grammar():
    """A → X | X Y  (two productions with same first token → conflict)"""
    g = Grammar()
    g.addRule("A", ["X"])
    g.addRule("A", ["X", "Y"])
    fm = {("A", ("X",)): [None], ("A", ("X", "Y")): [None, None]}
    return g, fm


def _left_recursive_grammar():
    """A → A B | C  (direct left recursion)"""
    g = Grammar()
    g.addRule("A", ["A", "B"])
    g.addRule("A", ["C"])
    fm = {("A", ("A", "B")): [None, None], ("A", ("C",)): [None]}
    return g, fm


def test_is_ll1_true_for_simple_grammar():
    g, fm = _simple_grammar()
    result = build_ll1_result(g, fm)
    assert result["is_ll1"] is True


def test_start_symbol_present():
    g, fm = _simple_grammar()
    result = build_ll1_result(g, fm)
    assert result["start_symbol"] == "program"


def test_first_sets_correct():
    g, fm = _simple_grammar()
    result = build_ll1_result(g, fm)
    assert result["first_sets"]["program"] == ["NUM"]


def test_follow_sets_contain_dollar():
    g, fm = _simple_grammar()
    result = build_ll1_result(g, fm)
    assert "eof" in result["follow_sets"]["program"]


def test_predict_sets_correct():
    g, fm = _simple_grammar()
    result = build_ll1_result(g, fm)
    assert result["predict_sets"]["program"] == [["NUM"]]


def test_parse_table_entry_correct():
    g, fm = _simple_grammar()
    result = build_ll1_result(g, fm)
    assert result["parse_table"]["program"]["NUM"] == [{"symbol": "NUM", "field": None}]


def test_conflicts_empty_for_ll1_grammar():
    g, fm = _simple_grammar()
    result = build_ll1_result(g, fm)
    assert result["conflicts"] == []


def test_left_recursion_empty_for_ll1_grammar():
    g, fm = _simple_grammar()
    result = build_ll1_result(g, fm)
    assert result["left_recursion"] == []


def test_epsilon_production_in_parse_table():
    g, fm = _epsilon_grammar()
    result = build_ll1_result(g, fm)
    # epsilon rule: predict set contains $; parse table entry under $ is []
    assert result["parse_table"]["rest"]["eof"] == []


def test_epsilon_in_first_sets():
    g, fm = _epsilon_grammar()
    result = build_ll1_result(g, fm)
    assert "" in result["first_sets"]["rest"]


def test_is_ll1_false_for_conflict_grammar():
    g, fm = _conflict_grammar()
    result = build_ll1_result(g, fm)
    assert result["is_ll1"] is False
    assert len(result["conflicts"]) > 0


def test_conflict_cell_omitted_from_parse_table():
    g, fm = _conflict_grammar()
    result = build_ll1_result(g, fm)
    # Conflicting cell A/X must be absent from parse_table
    assert "X" not in result["parse_table"].get("A", {})


def test_conflict_entry_has_required_fields():
    g, fm = _conflict_grammar()
    result = build_ll1_result(g, fm)
    c = result["conflicts"][0]
    assert c["nonterminal"] == "A"
    assert c["lookahead"] == "X"
    assert len(c["productions"]) == 2


def test_left_recursion_detected():
    g, fm = _left_recursive_grammar()
    result = build_ll1_result(g, fm)
    assert result["is_ll1"] is False
    assert len(result["left_recursion"]) > 0


def test_left_recursion_cycle_format():
    g, fm = _left_recursive_grammar()
    result = build_ll1_result(g, fm)
    cycle = result["left_recursion"][0]["cycle"]
    # Direct self-loop: ["A", "A"] — first and last element are the same
    assert cycle[0] == cycle[-1]
    assert "A" in cycle


def test_capturing_symbol_field_in_parse_table():
    g = Grammar()
    g.addRule("E", ["NUM"])
    fm = {("E", ("NUM",)): ["num"]}  # NUM is capturing with field "num"
    result = build_ll1_result(g, fm)
    entry = result["parse_table"]["E"]["NUM"]
    assert entry == [{"symbol": "NUM", "field": "num"}]


def _arbno_grammar_and_rules():
    """
    Mimics <rands> **= <expr>expr +COMMA  with <expr> ::= NUM.
    Grammar is expanded: rands→expr rands#|ε, rands#→COMMA expr rands#|ε, expr→NUM.
    """
    g = Grammar()
    g.addRule("rands", ["expr", "rands#"])
    g.addRule("rands", [])
    g.addRule("rands#", ["COMMA", "expr", "rands#"])
    g.addRule("rands#", [])
    g.addRule("expr", ["NUM"])
    fm = {
        ("rands",  ("expr", "rands#")): [None, None],
        ("rands",  ()):                 [],
        ("rands#", ("COMMA", "expr", "rands#")): [None, None, None],
        ("rands#", ()):                 [],
        ("expr",   ("NUM",)):           [None],
    }
    arbno = {
        "rands": {
            "rhs": [{"field": "exprList", "symbol": "expr", "is_terminal": False}],
            "separator": "COMMA",
        }
    }
    return g, fm, arbno


def test_arbno_section_present_in_result():
    g, fm, arbno = _arbno_grammar_and_rules()
    result = build_ll1_result(g, fm, arbno)
    assert "arbno" in result


def test_arbno_nt_in_arbno_not_parse_table():
    g, fm, arbno = _arbno_grammar_and_rules()
    result = build_ll1_result(g, fm, arbno)
    assert "rands" in result["arbno"]
    assert "rands" not in result["parse_table"]


def test_arbno_internal_cont_not_in_parse_table():
    g, fm, arbno = _arbno_grammar_and_rules()
    result = build_ll1_result(g, fm, arbno)
    assert "rands#" not in result["parse_table"]


def test_arbno_internal_nts_not_in_first_sets():
    g, fm, arbno = _arbno_grammar_and_rules()
    result = build_ll1_result(g, fm, arbno)
    assert "rands" not in result["first_sets"]
    assert "rands#" not in result["first_sets"]


def test_arbno_lookahead_computed_from_first_of_first_item():
    g, fm, arbno = _arbno_grammar_and_rules()
    result = build_ll1_result(g, fm, arbno)
    assert result["arbno"]["rands"]["lookahead"] == ["NUM"]


def test_arbno_separator_preserved():
    g, fm, arbno = _arbno_grammar_and_rules()
    result = build_ll1_result(g, fm, arbno)
    assert result["arbno"]["rands"]["separator"] == "COMMA"


def test_arbno_rhs_preserved():
    g, fm, arbno = _arbno_grammar_and_rules()
    result = build_ll1_result(g, fm, arbno)
    assert result["arbno"]["rands"]["rhs"] == [
        {"field": "exprList", "symbol": "expr", "is_terminal": False}
    ]


def test_existing_grammar_unaffected_when_no_arbno():
    g, fm = _simple_grammar()
    result = build_ll1_result(g, fm)
    assert result["is_ll1"] is True
    assert result["arbno"] == {}
