from ...lines import Line
from .MalformedBNFError import MalformedBNFError


def make_line(string, number=0, file=""):
    return Line(string, number, file)


def test_str_first_line_is_clickable_location():
    err = MalformedBNFError(make_line("<stmt>IfStmt ::= IF", number=25, file="grammar.plcc"))
    assert str(err).startswith("grammar.plcc:25:7: syntax error")


def test_str_includes_offending_line():
    err = MalformedBNFError(make_line("<stmt>IfStmt ::= IF", number=25, file="grammar.plcc"))
    assert "<stmt>IfStmt ::= IF" in str(err)


def test_str_caret_points_to_column():
    err = MalformedBNFError(make_line("<stmt>IfStmt ::= IF", number=25, file="grammar.plcc"))
    lines = str(err).splitlines()
    caret_line = lines[2]
    assert caret_line == "      ^"


def test_str_includes_examples_header():
    err = MalformedBNFError(make_line("<stmt>IfStmt ::= IF"))
    assert "Examples:" in str(err)


def test_str_includes_all_five_example_forms():
    err = MalformedBNFError(make_line("<stmt>IfStmt ::= IF"))
    s = str(err)
    assert "<nonTerminal> ::=" in s
    assert "<nonTerminal> ::= TOKEN <TOKEN> <rhs>" in s
    assert "<nonTerminal>:ClassName ::= TOKEN <TOKEN>:field1 <rhs>:field2" in s
    assert "<nonTerminal> **= <rhs>" in s
    assert "<nonTerminal> **= <rhs> +SEPARATOR" in s


def test_column_after_matched_lhs():
    # <stmt> ends at index 5 (0-based), so first bad char is at column 7 (1-based)
    err = MalformedBNFError(make_line("<stmt>IfStmt ::= IF"))
    assert err.column == 7


def test_column_no_lhs_defaults_to_first_nonwhitespace():
    err = MalformedBNFError(make_line("stmt ::= IF"))
    assert err.column == 1


def test_column_leading_whitespace_counted():
    # two leading spaces + <stmt> (6 chars) → column 9
    err = MalformedBNFError(make_line("  <stmt>IfStmt ::= IF"))
    assert err.column == 9


def test_column_no_lhs_with_leading_whitespace():
    # two leading spaces, no LHS → column 3
    err = MalformedBNFError(make_line("  stmt ::= IF"))
    assert err.column == 3
