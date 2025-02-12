from pytest import raises
from ..structs import Line
from . import parse_lines
from .parse_includes import parse_includes
from .load_rough_spec import process_includes, CircularIncludeError


def test_None_yields_nothing():
    assert list(process_includes(None)) == []


def test_empty_yields_nothing():
    assert list(process_includes([])) == []


def test_no_includes_pass_through():
    lines = list(parse_lines.from_string('one\ntwo\nthree'))
    assert list(process_includes(lines)) == lines


def test_include(fs):
    fs.create_file('/f', contents='hi')
    assert list(process_includes(parse_includes(parse_lines.from_string('%include /f')))) == [
        Line('hi', 1, '/f')
    ]


def test_circular_include_errors(fs):
    fs.create_file('/f', contents='%include /f')
    with raises(CircularIncludeError):
        list(process_includes(parse_includes(parse_lines.from_string('%include /f'))))
