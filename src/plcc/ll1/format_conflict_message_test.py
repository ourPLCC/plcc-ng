import pytest
from plcc.ll1.format_conflict_message import format_conflict_message, _render_production, _longest_common_prefix

# Shared test fixtures
FIRST_FIRST_CONFLICT = {
    "nonterminal": "expr",
    "lookahead": "ID",
    "conflict_type": "first_first",
    "productions": [
        {"alt": None, "production": [
            {"symbol": "ID", "field": None},
            {"symbol": "PLUS", "field": None},
            {"symbol": "expr", "field": None},
        ]},
        {"alt": None, "production": [
            {"symbol": "ID", "field": None},
            {"symbol": "MINUS", "field": None},
            {"symbol": "expr", "field": None},
        ]},
    ],
}

FIRST_FOLLOW_CONFLICT = {
    "nonterminal": "elsePart",
    "lookahead": "ELSE",
    "conflict_type": "first_follow",
    "productions": [
        {"alt": None, "production": [
            {"symbol": "ELSE", "field": None},
            {"symbol": "stmt", "field": None},
        ]},
        {"alt": None, "production": []},
    ],
}


def test_render_production_nonempty():
    entry = {"alt": None, "production": [
        {"symbol": "ELSE", "field": None},
        {"symbol": "stmt", "field": None},
    ]}
    assert _render_production("elsePart", entry) == "<elsePart> ::= ELSE <stmt>"


def test_render_production_empty():
    entry = {"alt": None, "production": []}
    assert _render_production("elsePart", entry) == "<elsePart> ::=    (empty)"


def test_render_production_terminal_no_angle_brackets():
    entry = {"alt": None, "production": [{"symbol": "NUM", "field": None}]}
    result = _render_production("expr", entry)
    assert "NUM" in result
    assert "<NUM>" not in result


def test_render_production_nonterminal_gets_angle_brackets():
    entry = {"alt": None, "production": [{"symbol": "term", "field": None}]}
    result = _render_production("expr", entry)
    assert "<term>" in result


def test_render_production_field_is_ignored():
    entry = {"alt": "Add", "production": [
        {"symbol": "ID", "field": "name"},
    ]}
    assert _render_production("expr", entry) == "<expr> ::= ID"


def test_format_includes_header_line():
    msg = format_conflict_message(FIRST_FOLLOW_CONFLICT)
    assert "LL(1) conflict: <elsePart> on lookahead ELSE" in msg


def test_format_lists_all_productions():
    msg = format_conflict_message(FIRST_FOLLOW_CONFLICT)
    assert "<elsePart> ::= ELSE <stmt>" in msg
    assert "<elsePart> ::=    (empty)" in msg


def test_first_follow_identifies_conflict_type():
    msg = format_conflict_message(FIRST_FOLLOW_CONFLICT)
    assert "FIRST/FOLLOW" in msg


def test_first_follow_names_the_lookahead():
    msg = format_conflict_message(FIRST_FOLLOW_CONFLICT)
    # The explanation mentions the lookahead and the nonterminal
    assert "ELSE" in msg
    assert "FOLLOW set of <elsePart>" in msg


def test_first_follow_includes_tip_to_look_at_context():
    msg = format_conflict_message(FIRST_FOLLOW_CONFLICT)
    assert "look at the rule(s) that use <elsePart>" in msg


def test_lcp_single_shared_token():
    p1 = [{"symbol": "ID", "field": None}, {"symbol": "PLUS", "field": None}]
    p2 = [{"symbol": "ID", "field": None}, {"symbol": "MINUS", "field": None}]
    lcp = _longest_common_prefix([p1, p2])
    assert [s["symbol"] for s in lcp] == ["ID"]


def test_lcp_multiple_shared_tokens():
    p1 = [{"symbol": "ID", "field": None}, {"symbol": "DOT", "field": None}, {"symbol": "ID", "field": None}]
    p2 = [{"symbol": "ID", "field": None}, {"symbol": "DOT", "field": None}, {"symbol": "NUM", "field": None}]
    lcp = _longest_common_prefix([p1, p2])
    assert [s["symbol"] for s in lcp] == ["ID", "DOT"]


def test_lcp_with_three_productions():
    p1 = [{"symbol": "ID", "field": None}, {"symbol": "PLUS", "field": None}]
    p2 = [{"symbol": "ID", "field": None}, {"symbol": "MINUS", "field": None}]
    p3 = [{"symbol": "ID", "field": None}, {"symbol": "TIMES", "field": None}]
    lcp = _longest_common_prefix([p1, p2, p3])
    assert [s["symbol"] for s in lcp] == ["ID"]


def test_lcp_empty_input():
    assert _longest_common_prefix([]) == []


def test_first_first_identifies_conflict_type():
    msg = format_conflict_message(FIRST_FIRST_CONFLICT)
    assert "FIRST/FIRST" in msg


def test_first_first_names_the_lookahead():
    msg = format_conflict_message(FIRST_FIRST_CONFLICT)
    assert "ID" in msg
    assert "parser cannot choose" in msg


def test_first_first_includes_left_factoring_tip():
    msg = format_conflict_message(FIRST_FIRST_CONFLICT)
    assert "left-factor" in msg


def test_first_first_shows_tail_nonterminal():
    msg = format_conflict_message(FIRST_FIRST_CONFLICT)
    # tail is <exprTail> derived from nonterminal "expr"
    assert "<exprTail>" in msg


def test_first_first_shows_factored_lhs_rule():
    msg = format_conflict_message(FIRST_FIRST_CONFLICT)
    # The common prefix is ID; factored rule is <expr> ::= ID <exprTail>
    assert "<expr> ::= ID <exprTail>" in msg


def test_first_first_shows_factored_tail_rules():
    msg = format_conflict_message(FIRST_FIRST_CONFLICT)
    assert "<exprTail> ::= PLUS <expr>" in msg
    assert "<exprTail> ::= MINUS <expr>" in msg
