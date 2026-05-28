import pytest
from plcc.parser.predictive_parser import parse, ParseError


# ll1.json dict for grammar: program → NUM  (NUM is non-capturing, field=null)
_TRIVIAL_LL1 = {
    "is_ll1": True,
    "start_symbol": "program",
    "parse_table": {
        "program": {
            "NUM": {"alt": None, "production": [{"symbol": "NUM", "field": None}]}
        }
    },
}

# ll1.json dict for grammar: E → t:Term; Term → n:NUM
_EXPR_LL1 = {
    "is_ll1": True,
    "start_symbol": "E",
    "parse_table": {
        "E": {
            "NUM": {"alt": None, "production": [{"symbol": "Term", "field": "t"}]}
        },
        "Term": {
            "NUM": {"alt": None, "production": [{"symbol": "NUM", "field": "n"}]}
        },
    },
}

# E → NUM PLUS NUM  (simple, no nesting, both NUMs captured)
_FLAT_EXPR_LL1 = {
    "is_ll1": True,
    "start_symbol": "E",
    "parse_table": {
        "E": {
            "NUM": {"alt": None, "production": [
                {"symbol": "NUM", "field": "left"},
                {"symbol": "PLUS", "field": None},
                {"symbol": "NUM", "field": "right"},
            ]}
        }
    },
}

# prefix expr grammar: <expr>:Add ::= PLUS <expr> <expr> | <expr>:Num ::= NUM
_PREFIX_LL1 = {
    "is_ll1": True,
    "start_symbol": "expr",
    "parse_table": {
        "expr": {
            "PLUS": {"alt": "Add", "production": [
                {"symbol": "PLUS", "field": None},
                {"symbol": "expr", "field": "left"},
                {"symbol": "expr", "field": "right"},
            ]},
            "NUM": {"alt": "Num", "production": [{"symbol": "NUM", "field": "val"}]},
        }
    },
}

def _tok(name, lexeme, line=1, col=1, file="<stdin>"):
    return {"kind": "token", "name": name, "lexeme": lexeme,
            "source": {"file": file, "line": line, "column": col}}


# --- trivial grammar tests ---

def test_trivial_parse_returns_tree_kind():
    tree, _ = parse(_TRIVIAL_LL1, [_tok("NUM", "42")])
    assert tree["kind"] == "tree"


def test_trivial_parse_rule_is_start_symbol():
    tree, _ = parse(_TRIVIAL_LL1, [_tok("NUM", "42")])
    assert tree["rule"] == "program"


def test_trivial_parse_elided_symbol_not_in_children():
    tree, _ = parse(_TRIVIAL_LL1, [_tok("NUM", "42")])
    assert tree["children"] == []


def test_trivial_parse_source_span():
    tree, _ = parse(_TRIVIAL_LL1, [_tok("NUM", "42", line=3, col=5)])
    src = tree["source"]
    assert src["line"] == 3
    assert src["column"] == 5
    assert src["endLine"] == 3
    assert src["endColumn"] == 6


def test_trivial_parse_source_file():
    tree, _ = parse(_TRIVIAL_LL1, [_tok("NUM", "42", file="prog.txt")])
    assert tree["source"]["file"] == "prog.txt"


# --- alt name tests ---

def test_alt_name_used_as_rule_in_tree():
    tree, _ = parse(_PREFIX_LL1, [_tok("PLUS", "+"), _tok("NUM", "2"), _tok("NUM", "3")])
    assert tree["rule"] == "Add"


def test_alt_name_on_leaf_node():
    tree, _ = parse(_PREFIX_LL1, [_tok("NUM", "42")])
    assert tree["rule"] == "Num"


def test_no_alt_name_uses_nonterminal_name():
    tree, _ = parse(_TRIVIAL_LL1, [_tok("NUM", "42")])
    assert tree["rule"] == "program"


# --- capturing symbol tests ---

def test_capturing_child_in_children():
    tree, _ = parse(_FLAT_EXPR_LL1, [
        _tok("NUM", "1", col=1),
        _tok("PLUS", "+", col=2),
        _tok("NUM", "2", col=3),
    ])
    fields = [child[0] for child in tree["children"]]
    assert "left" in fields
    assert "right" in fields


def test_capturing_children_are_token_dicts():
    tree, _ = parse(_FLAT_EXPR_LL1, [
        _tok("NUM", "1"),
        _tok("PLUS", "+"),
        _tok("NUM", "2"),
    ])
    left = dict(tree["children"])["left"]
    assert left["kind"] == "token"
    assert left["name"] == "NUM"
    assert left["lexeme"] == "1"


def test_elided_plus_not_in_children():
    tree, _ = parse(_FLAT_EXPR_LL1, [
        _tok("NUM", "1"),
        _tok("PLUS", "+"),
        _tok("NUM", "2"),
    ])
    fields = [child[0] for child in tree["children"]]
    assert "PLUS" not in fields


# --- span across multiple tokens ---

def test_span_covers_all_tokens_including_elided():
    tree, _ = parse(_FLAT_EXPR_LL1, [
        _tok("NUM", "1", col=1),
        _tok("PLUS", "+", col=3),
        _tok("NUM", "2", col=5),
    ])
    src = tree["source"]
    assert src["column"] == 1
    assert src["endColumn"] == 5


# --- nested nonterminal tests ---

def test_nested_nonterminal_child_is_tree():
    tree, _ = parse(_EXPR_LL1, [
        _tok("NUM", "3"),
    ])
    assert tree["rule"] == "E"
    children_dict = dict(tree["children"])
    assert "t" in children_dict
    assert children_dict["t"]["kind"] == "tree"
    assert children_dict["t"]["rule"] == "Term"


# --- error cases ---

def test_wrong_terminal_raises_parse_error():
    with pytest.raises(ParseError):
        parse(_TRIVIAL_LL1, [_tok("IDENTIFIER", "x")])


def test_no_production_for_lookahead_raises_parse_error():
    ll1 = {
        "is_ll1": True,
        "start_symbol": "A",
        "parse_table": {"A": {"X": {"alt": None, "production": [{"symbol": "X", "field": None}]}}},
    }
    with pytest.raises(ParseError):
        parse(ll1, [_tok("Y", "y")])


def test_empty_input_on_nonempty_grammar_raises_parse_error():
    with pytest.raises(ParseError):
        parse(_TRIVIAL_LL1, [])


# ll1 dict for: rands **= expr +COMMA, expr → NUM
_RANDS_LL1 = {
    "is_ll1": True,
    "start_symbol": "rands",
    "parse_table": {
        "expr": {
            "NUM": {"alt": None, "production": [{"symbol": "NUM", "field": "num"}]}
        }
    },
    "arbno": {
        "rands": {
            "rhs": [{"field": "exprList", "symbol": "expr", "is_terminal": False}],
            "separator": "COMMA",
            "lookahead": ["NUM"],
        }
    }
}

# ll1 dict for: cmds **= cmd (no separator), cmd → X
_CMDS_LL1 = {
    "is_ll1": True,
    "start_symbol": "cmds",
    "parse_table": {
        "cmd": {
            "X": {"alt": None, "production": [{"symbol": "X", "field": "x"}]}
        }
    },
    "arbno": {
        "cmds": {
            "rhs": [{"field": "cmdList", "symbol": "cmd", "is_terminal": False}],
            "separator": None,
            "lookahead": ["X"],
        }
    }
}


def test_arbno_separator_two_items_produces_list():
    tree, _ = parse(_RANDS_LL1, [
        _tok("NUM", "1"),
        _tok("COMMA", ","),
        _tok("NUM", "2"),
    ])
    children_dict = dict(tree["children"])
    assert "exprList" in children_dict
    assert isinstance(children_dict["exprList"], list)
    assert len(children_dict["exprList"]) == 2


def test_arbno_separator_list_items_are_tree_nodes():
    tree, _ = parse(_RANDS_LL1, [
        _tok("NUM", "1"),
        _tok("COMMA", ","),
        _tok("NUM", "2"),
    ])
    expr_list = dict(tree["children"])["exprList"]
    assert expr_list[0]["kind"] == "tree"
    assert expr_list[0]["rule"] == "expr"
    assert expr_list[1]["kind"] == "tree"


def test_arbno_separator_zero_items_on_no_match():
    tree, _ = parse(_RANDS_LL1, [])
    children_dict = dict(tree["children"])
    assert children_dict["exprList"] == []


def test_arbno_separator_one_item():
    tree, _ = parse(_RANDS_LL1, [_tok("NUM", "42")])
    children_dict = dict(tree["children"])
    assert len(children_dict["exprList"]) == 1


def test_arbno_plain_multiple_items():
    tree, _ = parse(_CMDS_LL1, [
        _tok("X", "a"),
        _tok("X", "b"),
        _tok("X", "c"),
    ])
    children_dict = dict(tree["children"])
    assert len(children_dict["cmdList"]) == 3


def test_arbno_plain_zero_items():
    tree, _ = parse(_CMDS_LL1, [])
    children_dict = dict(tree["children"])
    assert children_dict["cmdList"] == []


def test_arbno_result_is_tree_kind():
    tree, _ = parse(_RANDS_LL1, [_tok("NUM", "1")])
    assert tree["kind"] == "tree"
    assert tree["rule"] == "rands"


_ADDITION_LL1 = {
    "is_ll1": True,
    "start_symbol": "program",
    "parse_table": {
        "program": {
            "NUM": {"alt": None, "production": [
                {"symbol": "NUM", "field": None},
                {"symbol": "PLUS", "field": None},
                {"symbol": "NUM", "field": None},
            ]}
        }
    },
}


def test_incomplete_raises_ParseError():
    with pytest.raises(ParseError):
        parse(_ADDITION_LL1, [_tok("NUM", "1")])


def test_bad_token_raises_ParseError():
    with pytest.raises(ParseError):
        parse(_TRIVIAL_LL1, [_tok("PLUS", "+")])


def test_parse_error_carries_source():
    with pytest.raises(ParseError) as exc_info:
        parse(_TRIVIAL_LL1, [_tok("PLUS", "+", line=3, col=7)])
    assert exc_info.value.source["line"] == 3
    assert exc_info.value.source["column"] == 7


def test_parse_returns_consumed_count():
    _, consumed = parse(_TRIVIAL_LL1, [_tok("NUM", "42")])
    assert consumed == 1


def test_parse_stops_at_first_unconsumed_token():
    tree, consumed = parse(_TRIVIAL_LL1, [_tok("NUM", "1"), _tok("NUM", "2")])
    assert consumed == 1
    assert tree["kind"] == "tree"


def test_incomplete_raises_ParseError_not_IncompleteInputError():
    with pytest.raises(ParseError):
        parse(_ADDITION_LL1, [_tok("NUM", "1")])


def test_parse_error_found_is_set_for_wrong_terminal():
    with pytest.raises(ParseError) as exc_info:
        parse(_TRIVIAL_LL1, [_tok("PLUS", "+")])
    assert exc_info.value.found == "PLUS"


def test_parse_error_found_is_eof_for_premature_end_of_input():
    with pytest.raises(ParseError) as exc_info:
        parse(_ADDITION_LL1, [_tok("NUM", "1")])
    assert exc_info.value.found == "eof"


def test_parse_error_found_is_none_by_default():
    e = ParseError("something went wrong")
    assert e.found is None


from plcc.parser.predictive_parser import Tracer


def test_tracer_depth_is_zero_initially():
    t = Tracer()
    t.predict("x", "Y", "x")
    assert t.events[0]["depth"] == 0


def test_tracer_push_increases_depth():
    t = Tracer()
    t.push("x")
    t.predict("x", "Y", "x")
    assert t.events[0]["depth"] == 1


def test_tracer_pop_decreases_depth():
    t = Tracer()
    t.push("x")
    t.pop()
    t.predict("x", "Y", "x")
    assert t.events[0]["depth"] == 0


def test_tracer_predict_event_fields():
    t = Tracer()
    t.predict("expr", "NUM", "Num")
    assert t.events[0] == {
        "event": "predict", "sym": "expr", "lookahead": "NUM",
        "production": "Num", "depth": 0,
    }


def test_tracer_predict_none_production():
    t = Tracer()
    t.predict("rands", "NUM", None)
    assert t.events[0]["production"] is None


def test_tracer_shift_event_fields():
    t = Tracer()
    tok = {"name": "NUM", "lexeme": "42", "source": {"file": "-", "line": 1, "column": 1}}
    t.shift(tok)
    e = t.events[0]
    assert e["event"] == "shift"
    assert e["name"] == "NUM"
    assert e["lexeme"] == "42"
    assert e["source"] == {"file": "-", "line": 1, "column": 1}
    assert e["depth"] == 0


def test_tracer_complete_event_fields():
    t = Tracer()
    t.complete("Num")
    assert t.events[0] == {"event": "complete", "rule": "Num", "depth": 0}


def test_tracer_events_returns_copy():
    t = Tracer()
    t.predict("x", "Y", "x")
    copy = t.events
    copy.clear()
    assert len(t.events) == 1


def test_tracer_records_sequence_of_events():
    t = Tracer()
    tok = {"name": "NUM", "lexeme": "1", "source": {}}
    t.predict("program", "NUM", "program")
    t.push("program")
    t.shift(tok)
    t.pop()
    t.complete("program")
    kinds = [e["event"] for e in t.events]
    assert kinds == ["predict", "shift", "complete"]


def test_parse_with_tracer_predict_fired():
    t = Tracer()
    parse(_TRIVIAL_LL1, [_tok("NUM", "42")], tracer=t)
    assert any(e["event"] == "predict" for e in t.events)


def test_parse_with_tracer_predict_sym_is_start():
    t = Tracer()
    parse(_TRIVIAL_LL1, [_tok("NUM", "42")], tracer=t)
    predicts = [e for e in t.events if e["event"] == "predict"]
    assert predicts[0]["sym"] == "program"


def test_parse_with_tracer_predict_production_is_sym_when_no_alt():
    t = Tracer()
    parse(_TRIVIAL_LL1, [_tok("NUM", "42")], tracer=t)
    predicts = [e for e in t.events if e["event"] == "predict"]
    assert predicts[0]["production"] == "program"


def test_parse_with_tracer_predict_production_is_alt_name():
    t = Tracer()
    parse(_PREFIX_LL1, [_tok("NUM", "42")], tracer=t)
    predicts = [e for e in t.events if e["event"] == "predict"]
    assert predicts[0]["production"] == "Num"


def test_parse_with_tracer_shift_fired():
    t = Tracer()
    parse(_TRIVIAL_LL1, [_tok("NUM", "42")], tracer=t)
    assert any(e["event"] == "shift" for e in t.events)


def test_parse_with_tracer_shift_carries_lexeme():
    t = Tracer()
    parse(_TRIVIAL_LL1, [_tok("NUM", "42")], tracer=t)
    shifts = [e for e in t.events if e["event"] == "shift"]
    assert shifts[0]["lexeme"] == "42"


def test_parse_with_tracer_complete_fired():
    t = Tracer()
    parse(_TRIVIAL_LL1, [_tok("NUM", "42")], tracer=t)
    assert any(e["event"] == "complete" for e in t.events)


def test_parse_with_tracer_complete_rule_matches_predict_production():
    t = Tracer()
    parse(_TRIVIAL_LL1, [_tok("NUM", "42")], tracer=t)
    predicts = [e for e in t.events if e["event"] == "predict"]
    completes = [e for e in t.events if e["event"] == "complete"]
    assert predicts[0]["production"] == completes[0]["rule"]


def test_parse_with_no_tracer_still_works():
    tree, _ = parse(_TRIVIAL_LL1, [_tok("NUM", "42")])
    assert tree["kind"] == "tree"


def test_parse_with_tracer_nested_depths():
    # _EXPR_LL1: E → t:Term; Term → n:NUM
    # predict("E", ...) depth=0, predict("Term", ...) depth=1
    t = Tracer()
    parse(_EXPR_LL1, [_tok("NUM", "42")], tracer=t)
    predicts = [e for e in t.events if e["event"] == "predict"]
    assert predicts[0]["sym"] == "E"
    assert predicts[0]["depth"] == 0
    assert predicts[1]["sym"] == "Term"
    assert predicts[1]["depth"] == 1


def test_parse_with_tracer_predict_and_complete_same_depth():
    t = Tracer()
    parse(_TRIVIAL_LL1, [_tok("NUM", "42")], tracer=t)
    predict_depth = next(e["depth"] for e in t.events if e["event"] == "predict")
    complete_depth = next(e["depth"] for e in t.events if e["event"] == "complete")
    assert predict_depth == complete_depth


def test_parse_with_tracer_events_on_error_include_partial_trace():
    # _ADDITION_LL1: program → NUM PLUS NUM; input [NUM] only → ParseError
    # predict and shift for NUM were recorded before the error
    t = Tracer()
    with pytest.raises(ParseError):
        parse(_ADDITION_LL1, [_tok("NUM", "1")], tracer=t)
    assert any(e["event"] == "predict" for e in t.events)
    assert any(e["event"] == "shift" for e in t.events)


def test_parse_with_tracer_arbno_predict_per_iteration():
    # _RANDS_LL1: rands **= expr +COMMA; parse 2 exprs → 2 arbno predicts
    t = Tracer()
    parse(_RANDS_LL1, [_tok("NUM", "1"), _tok("COMMA", ","), _tok("NUM", "2")], tracer=t)
    arbno_predicts = [e for e in t.events if e["event"] == "predict" and e["sym"] == "rands"]
    assert len(arbno_predicts) == 2


def test_parse_with_tracer_arbno_predict_production_is_none():
    t = Tracer()
    parse(_RANDS_LL1, [_tok("NUM", "1")], tracer=t)
    arbno_predicts = [e for e in t.events if e["event"] == "predict" and e["sym"] == "rands"]
    assert arbno_predicts[0]["production"] is None
