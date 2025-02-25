from types import NoneType
from .. import lexparse
from .NameValidator import NameValidator, InvalidName


def test_all_upper_is_valid():
    spec = lexparse.fromstring("""
        token GOOD 'hi'
    """)
    e = NameValidator().validate(spec.ruleList[0])
    assert isinstance(e, NoneType)


def test_underscores_are_valid():
    spec = lexparse.fromstring("""
        token _GOOD_NAME_ 'hi'
    """)
    e = NameValidator().validate(spec.ruleList[0])
    assert isinstance(e, NoneType)


def test_numbers_are_valid():
    spec = lexparse.fromstring("""
        token GOOD_1 'hi'
    """)
    e = NameValidator().validate(spec.ruleList[0])
    assert isinstance(e, NoneType)


def test_lowercase_are_invalid():
    spec = lexparse.fromstring("""
        token bad_name 'hi'
    """)
    e = NameValidator().validate(spec.ruleList[0])
    assert isinstance(e, InvalidName)


def test_starting_with_a_number_is_invalid():
    spec = lexparse.fromstring("""
        token 1_BAD_NAME 'hi'
    """)
    e = NameValidator().validate(spec.ruleList[0])
    assert isinstance(e, InvalidName)


def test_hyphens_are_invalid():
    spec = lexparse.fromstring("""
        token BAD-NAME 'hi'
    """)
    e = NameValidator().validate(spec.ruleList[0])
    assert isinstance(e, InvalidName)


def test_any_other_punctuation_is_invalid():
    spec = lexparse.fromstring("""
        token BAD!NAME 'hi'
    """)
    e = NameValidator().validate(spec.ruleList[0])
    assert isinstance(e, InvalidName)
