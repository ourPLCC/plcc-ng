from .. import lexparse
from .check_format_of_patterns import check_format_of_patterns, InvalidPattern
from .check_for_unrecognized_lines import check_for_unrecognized_lines


def test_single_quotes():
    spec = lexparse.fromstring("""
                            token NAME 'single quotes'
                        """)
    errors = check_format_of_patterns(spec.ruleList)
    assert not errors


def test_double_quotes():
    spec = lexparse.fromstring("""
                            token NAME "double quotes"
                        """)
    errors = check_format_of_patterns(spec.ruleList)
    assert not errors


def test_other_delimiter():
    spec = lexparse.fromstring("""
                            token NAME [square quotes[
                        """)
    errors = check_format_of_patterns(spec.ruleList)
    assert not errors


def test_missmatch_delimiters_is_invalid_line():
    spec = lexparse.fromstring("""
                            token NAME [square quotes]
                        """)
    errors = check_format_of_patterns(spec.ruleList)
    assert not errors
    errors = check_for_unrecognized_lines(spec.ruleList)
    assert errors


def test_bad_re_syntax():
    spec = lexparse.fromstring("""
                            token NAME '(missing closing paren'
                        """)
    errors = check_format_of_patterns(spec.ruleList)
    assert errors
    assert isinstance(errors[0], InvalidPattern)
