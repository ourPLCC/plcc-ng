import plccng.lineparse as lineparse
from .UnrecognizedLineValidator import UnrecognizedLineValidator, UnrecognizedLine


def test_a_residual_line_is_unrecognized():
    line = list(lineparse.fromstring("hello"))[0]
    e = UnrecognizedLineValidator().validate(line)
    assert e == UnrecognizedLine(line)


def test_ignores_any_other_type():
    e = UnrecognizedLineValidator().validate(3)
    assert e == None
