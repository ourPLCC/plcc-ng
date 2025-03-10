from .. import parse_from_string_without_validation
from .check_format_of_names import InvalidName, check_format_of_names


def test_all_upper_is_valid():
    spec = parse_from_string_without_validation.parse_from_string_without_validation("""
        token GOOD 'hi'
    """)
    e = check_format_of_names(spec.ruleList)
    assert e == []


def test_underscores_are_valid():
    spec = parse_from_string_without_validation.parse_from_string_without_validation("""
        token _GOOD_NAME_ 'hi'
    """)
    e = check_format_of_names(spec.ruleList)
    assert e == []


def test_numbers_are_valid():
    spec = parse_from_string_without_validation.parse_from_string_without_validation("""
        token GOOD_1 'hi'
    """)
    e = check_format_of_names(spec.ruleList)
    assert e == []


def test_lowercase_are_invalid():
    spec = parse_from_string_without_validation.parse_from_string_without_validation("""
        token bad_name 'hi'
    """)
    e = check_format_of_names(spec.ruleList)
    assert isinstance(e[0], InvalidName)


def test_starting_with_a_number_is_invalid():
    spec = parse_from_string_without_validation.parse_from_string_without_validation("""
        token 1_BAD_NAME 'hi'
    """)
    e = check_format_of_names(spec.ruleList)
    assert isinstance(e[0], InvalidName)


def test_hyphens_are_invalid():
    spec = parse_from_string_without_validation.parse_from_string_without_validation("""
        token BAD-NAME 'hi'
    """)
    e = check_format_of_names(spec.ruleList)
    assert isinstance(e[0], InvalidName)


def test_any_other_punctuation_is_invalid():
    spec = parse_from_string_without_validation.parse_from_string_without_validation("""
        token BAD!NAME 'hi'
    """)
    e = check_format_of_names(spec.ruleList)
    assert isinstance(e[0], InvalidName)
