from ... import lineparse
from .check_for_unrecognized_lines import UnrecognizedLine, check_for_unrecognized_lines


def test_a_residual_line_is_unrecognized():
    line = list(lineparse.fromstring("hello"))[0]
    e = check_for_unrecognized_lines([line])
    assert e[0] == UnrecognizedLine(line)


def test_ignores_any_non_line():
    e = check_for_unrecognized_lines([3])
    assert e == []

