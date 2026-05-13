import pytest
from plcc.parser.predictive_parser import parse, ParseError


# ll1.json dict for grammar: program → NUM  (NUM is non-capturing, field=null)
_TRIVIAL_LL1 = {
    "is_ll1": True,
    "start_symbol": "program",
    "parse_table": {
        "program": {
            "NUM": [{"symbol": "NUM", "field": None}]
        }
    },
}

# ll1.json dict for grammar: E → t:Term; Term → n:NUM
# (tests nonterminal child appearing as tree node)
_EXPR_LL1 = {
    "is_ll1": True,
    "start_symbol": "E",
    "parse_table": {
        "E": {
            "NUM": [{"symbol": "Term", "field": "t"}]
        },
        "Term": {
            "NUM": [{"symbol": "NUM", "field": "n"}]
        },
    },
}

# E → NUM PLUS NUM  (simple, no nesting, both NUMs captured)
_FLAT_EXPR_LL1 = {
    "is_ll1": True,
    "start_symbol": "E",
    "parse_table": {
        "E": {
            "NUM": [
                {"symbol": "NUM", "field": "left"},
                {"symbol": "PLUS", "field": None},
                {"symbol": "NUM", "field": "right"},
            ]
        }
    },
}

def _tok(name, lexeme, line=1, col=1, file="<stdin>"):
    return {"kind": "token", "name": name, "lexeme": lexeme,
            "source": {"file": file, "line": line, "column": col}}


# --- trivial grammar tests ---

def test_trivial_parse_returns_tree_kind():
    result = parse(_TRIVIAL_LL1, [_tok("NUM", "42")])
    assert result["kind"] == "tree"


def test_trivial_parse_rule_is_start_symbol():
    result = parse(_TRIVIAL_LL1, [_tok("NUM", "42")])
    assert result["rule"] == "program"


def test_trivial_parse_elided_symbol_not_in_children():
    result = parse(_TRIVIAL_LL1, [_tok("NUM", "42")])
    assert result["children"] == []


def test_trivial_parse_source_span():
    result = parse(_TRIVIAL_LL1, [_tok("NUM", "42", line=3, col=5)])
    src = result["source"]
    assert src["line"] == 3
    assert src["column"] == 5
    assert src["endLine"] == 3
    # endColumn = col + len("42") - 1 = 5 + 2 - 1 = 6
    assert src["endColumn"] == 6


def test_trivial_parse_source_file():
    result = parse(_TRIVIAL_LL1, [_tok("NUM", "42", file="prog.txt")])
    assert result["source"]["file"] == "prog.txt"


# --- capturing symbol tests ---

def test_capturing_child_in_children():
    result = parse(_FLAT_EXPR_LL1, [
        _tok("NUM", "1", col=1),
        _tok("PLUS", "+", col=2),
        _tok("NUM", "2", col=3),
    ])
    fields = [child[0] for child in result["children"]]
    assert "left" in fields
    assert "right" in fields


def test_capturing_children_are_token_dicts():
    result = parse(_FLAT_EXPR_LL1, [
        _tok("NUM", "1"),
        _tok("PLUS", "+"),
        _tok("NUM", "2"),
    ])
    left = dict(result["children"])["left"]
    assert left["kind"] == "token"
    assert left["name"] == "NUM"
    assert left["lexeme"] == "1"


def test_elided_plus_not_in_children():
    result = parse(_FLAT_EXPR_LL1, [
        _tok("NUM", "1"),
        _tok("PLUS", "+"),
        _tok("NUM", "2"),
    ])
    fields = [child[0] for child in result["children"]]
    assert "PLUS" not in fields


# --- span across multiple tokens ---

def test_span_covers_all_tokens_including_elided():
    result = parse(_FLAT_EXPR_LL1, [
        _tok("NUM", "1", col=1),
        _tok("PLUS", "+", col=3),
        _tok("NUM", "2", col=5),
    ])
    src = result["source"]
    assert src["column"] == 1          # start of first token
    assert src["endColumn"] == 5       # endColumn of "2" at col 5, len 1 → 5


# --- nested nonterminal tests ---

def test_nested_nonterminal_child_is_tree():
    result = parse(_EXPR_LL1, [
        _tok("NUM", "3"),
    ])
    assert result["rule"] == "E"
    children_dict = dict(result["children"])
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
        "parse_table": {"A": {"X": [{"symbol": "X", "field": None}]}},
    }
    with pytest.raises(ParseError):
        parse(ll1, [_tok("Y", "y")])


def test_extra_tokens_after_parse_raises_parse_error():
    with pytest.raises(ParseError):
        parse(_TRIVIAL_LL1, [_tok("NUM", "1"), _tok("NUM", "2")])


def test_empty_input_on_nonempty_grammar_raises_parse_error():
    with pytest.raises(ParseError):
        parse(_TRIVIAL_LL1, [])


# ll1 dict for: rands **= expr +COMMA, expr → NUM
_RANDS_LL1 = {
    "is_ll1": True,
    "start_symbol": "rands",
    "parse_table": {
        "expr": {
            "NUM": [{"symbol": "NUM", "field": "num"}]
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
            "X": [{"symbol": "X", "field": "x"}]
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
    result = parse(_RANDS_LL1, [
        _tok("NUM", "1"),
        _tok("COMMA", ","),
        _tok("NUM", "2"),
    ])
    children_dict = dict(result["children"])
    assert "exprList" in children_dict
    assert isinstance(children_dict["exprList"], list)
    assert len(children_dict["exprList"]) == 2


def test_arbno_separator_list_items_are_tree_nodes():
    result = parse(_RANDS_LL1, [
        _tok("NUM", "1"),
        _tok("COMMA", ","),
        _tok("NUM", "2"),
    ])
    expr_list = dict(result["children"])["exprList"]
    assert expr_list[0]["kind"] == "tree"
    assert expr_list[0]["rule"] == "expr"
    assert expr_list[1]["kind"] == "tree"


def test_arbno_separator_zero_items_on_no_match():
    result = parse(_RANDS_LL1, [])
    children_dict = dict(result["children"])
    assert children_dict["exprList"] == []


def test_arbno_separator_one_item():
    result = parse(_RANDS_LL1, [_tok("NUM", "42")])
    children_dict = dict(result["children"])
    assert len(children_dict["exprList"]) == 1


def test_arbno_plain_multiple_items():
    result = parse(_CMDS_LL1, [
        _tok("X", "a"),
        _tok("X", "b"),
        _tok("X", "c"),
    ])
    children_dict = dict(result["children"])
    assert len(children_dict["cmdList"]) == 3


def test_arbno_plain_zero_items():
    result = parse(_CMDS_LL1, [])
    children_dict = dict(result["children"])
    assert children_dict["cmdList"] == []


def test_arbno_result_is_tree_kind():
    result = parse(_RANDS_LL1, [_tok("NUM", "1")])
    assert result["kind"] == "tree"
    assert result["rule"] == "rands"


from plcc.parser.predictive_parser import IncompleteInputError


_ADDITION_LL1 = {
    "is_ll1": True,
    "start_symbol": "program",
    "parse_table": {
        "program": {
            "NUM": [
                {"symbol": "NUM", "field": None},
                {"symbol": "PLUS", "field": None},
                {"symbol": "NUM", "field": None},
            ]
        }
    },
}


def test_incomplete_raises_IncompleteInputError_when_table_misses_sentinel():
    # Grammar: program → NUM PLUS NUM
    # Tokens: [NUM] — parser needs PLUS next, gets $ instead
    with pytest.raises(IncompleteInputError):
        parse(_ADDITION_LL1, [_tok("NUM", "1")])


def test_bad_token_raises_ParseError_not_IncompleteInputError():
    # Grammar: program → NUM
    # Tokens: [PLUS] — wrong token, not EOF
    with pytest.raises(ParseError) as exc_info:
        parse(_TRIVIAL_LL1, [_tok("PLUS", "+")])
    assert not isinstance(exc_info.value, IncompleteInputError)
