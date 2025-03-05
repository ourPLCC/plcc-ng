from .. import parse_from_string_without_validation
from .check_for_unrecognized_lines import check_for_unrecognized_lines
from .check_format_of_patterns import InvalidPattern, check_format_of_patterns


def test_single_quotes():
    spec = parse_from_string_without_validation.parse_from_string_without_validation("""
                            token NAME 'single quotes'
                        """)
    errors = check_format_of_patterns(spec.ruleList)
    assert not errors


def test_double_quotes():
    spec = parse_from_string_without_validation.parse_from_string_without_validation("""
                            token NAME "double quotes"
                        """)
    errors = check_format_of_patterns(spec.ruleList)
    assert not errors


def test_other_delimiter():
    spec = parse_from_string_without_validation.parse_from_string_without_validation("""
                            token NAME [square quotes[
                        """)
    errors = check_format_of_patterns(spec.ruleList)
    assert not errors


def test_missmatch_delimiters_is_invalid_line():
    spec = parse_from_string_without_validation.parse_from_string_without_validation("""
                            token NAME [square quotes]
                        """)
    errors = check_format_of_patterns(spec.ruleList)
    assert not errors
    errors = check_for_unrecognized_lines(spec.ruleList)
    assert errors


def test_bad_re_syntax():
    spec = parse_from_string_without_validation.parse_from_string_without_validation("""
                            token NAME '(missing closing paren'
                        """)
    errors = check_format_of_patterns(spec.ruleList)
    assert errors
    assert isinstance(errors[0], InvalidPattern)
