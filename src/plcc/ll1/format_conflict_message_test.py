from plcc.ll1.format_conflict_message import format_conflict_message, _render_production, _longest_common_prefix, _render_symbol

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


def test_render_production_capturing_terminal_with_explicit_alt():
    # field "name" != "id" (default for ID), so renders as <ID>name
    entry = {"alt": "Add", "production": [
        {"symbol": "ID", "field": "name"},
    ]}
    assert _render_production("expr", entry) == "<expr> ::= <ID>name"


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


def test_render_production_underscore_terminal_no_angle_brackets():
    # Terminals can start with underscore in PLCC (e.g. _SKIP, _EOL)
    entry = {"alt": None, "production": [{"symbol": "_SKIP", "field": None}]}
    result = _render_production("expr", entry)
    assert "_SKIP" in result
    assert "<_SKIP>" not in result


# --- Field-aware rendering tests ---

def test_render_symbol_noncapturing_terminal():
    # field=None + terminal → bare token
    assert _render_symbol("NUM", None) == "NUM"


def test_render_symbol_noncapturing_nonterminal():
    # field=None + nonterminal → <nt>
    assert _render_symbol("expr", None) == "<expr>"


def test_render_symbol_capturing_terminal_default_field():
    # field == sym.lower() → default alt, render as <NUM>
    assert _render_symbol("NUM", "num") == "<NUM>"


def test_render_symbol_capturing_terminal_explicit_alt():
    # field != sym.lower() → render as <NUM>name
    assert _render_symbol("NUM", "n") == "<NUM>n"


def test_render_symbol_capturing_nonterminal_default_field():
    # field == sym.lower() → default alt, render as <expr>
    assert _render_symbol("expr", "expr") == "<expr>"


def test_render_symbol_capturing_nonterminal_explicit_alt():
    # field != sym.lower() → render as <ExprRest>rest
    assert _render_symbol("ExprRest", "rest") == "<ExprRest>rest"


def test_render_production_noncapturing_symbols():
    # When field=None for all symbols, non-capturing rendering
    entry = {"alt": None, "production": [
        {"symbol": "NUM", "field": None},
        {"symbol": "expr", "field": None},
    ]}
    assert _render_production("stmt", entry) == "<stmt> ::= NUM <expr>"


def test_render_production_capturing_nonterminal_default_field():
    # field "stmt" == "stmt".lower(), so render as <stmt> (no explicit alt)
    entry = {"alt": None, "production": [
        {"symbol": "stmt", "field": "stmt"},
    ]}
    assert _render_production("block", entry) == "<block> ::= <stmt>"


def test_first_first_left_factor_tip_uses_field_aware_rendering():
    # Capturing symbols in productions should appear with field annotations
    # in the left-factoring suggestion
    conflict = {
        "nonterminal": "expr",
        "lookahead": "NUM",
        "conflict_type": "first_first",
        "productions": [
            {"alt": None, "production": [
                {"symbol": "NUM", "field": "n"},
                {"symbol": "PLUS", "field": None},
                {"symbol": "expr", "field": "expr"},
            ]},
            {"alt": None, "production": [
                {"symbol": "NUM", "field": "n"},
                {"symbol": "MINUS", "field": None},
                {"symbol": "expr", "field": "expr"},
            ]},
        ],
    }
    msg = format_conflict_message(conflict)
    # LCP is NUM with field "n" (explicit alt, since "n" != "num")
    assert "<expr> ::= <NUM>n <exprTail>" in msg
    # Remainders: PLUS <expr> and MINUS <expr> (field "expr" == default)
    assert "<exprTail> ::= PLUS <expr>" in msg
    assert "<exprTail> ::= MINUS <expr>" in msg


def test_first_first_empty_lcp_shows_nullable_tip():
    # FIRST/FIRST conflict where productions share no visible prefix
    # (conflict arises through nullable leading symbols)
    conflict = {
        "nonterminal": "stmt",
        "lookahead": "ID",
        "conflict_type": "first_first",
        "productions": [
            {"alt": None, "production": [
                {"symbol": "ifPart", "field": None},
                {"symbol": "NUM", "field": None},
            ]},
            {"alt": None, "production": [
                {"symbol": "elsePart", "field": None},
                {"symbol": "NUM", "field": None},
            ]},
        ],
    }
    msg = format_conflict_message(conflict)
    assert "FIRST/FIRST" in msg
    assert "nullable" in msg
    assert "left-factor" not in msg
