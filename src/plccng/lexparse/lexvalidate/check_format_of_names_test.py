from .. import lexparse
from .check_format_of_names import check_format_of_names, InvalidName


def test_all_upper_is_valid():
    spec = lexparse.fromstring("""
        token GOOD 'hi'
    """)
    e = check_format_of_names(spec.ruleList)
    assert e == []


def test_underscores_are_valid():
    spec = lexparse.fromstring("""
        token _GOOD_NAME_ 'hi'
    """)
    e = check_format_of_names(spec.ruleList)
    assert e == []


def test_numbers_are_valid():
    spec = lexparse.fromstring("""
        token GOOD_1 'hi'
    """)
    e = check_format_of_names(spec.ruleList)
    assert e == []


def test_lowercase_are_invalid():
    spec = lexparse.fromstring("""
        token bad_name 'hi'
    """)
    e = check_format_of_names(spec.ruleList)
    assert isinstance(e[0], InvalidName)


def test_starting_with_a_number_is_invalid():
    spec = lexparse.fromstring("""
        token 1_BAD_NAME 'hi'
    """)
    e = check_format_of_names(spec.ruleList)
    assert isinstance(e[0], InvalidName)


def test_hyphens_are_invalid():
    spec = lexparse.fromstring("""
        token BAD-NAME 'hi'
    """)
    e = check_format_of_names(spec.ruleList)
    assert isinstance(e[0], InvalidName)


def test_any_other_punctuation_is_invalid():
    spec = lexparse.fromstring("""
        token BAD!NAME 'hi'
    """)
    e = check_format_of_names(spec.ruleList)
    assert isinstance(e[0], InvalidName)
