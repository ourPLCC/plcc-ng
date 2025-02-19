from pytest import raises
from ..structs import Line
from . import parse_lines
from .parse_includes import parse_includes
from .resolve_includes import resolve_includes, CircularIncludeError


def test_None_yields_nothing():
    assert list(resolve_includes(None)) == []


def test_empty_yields_nothing():
    assert list(resolve_includes([])) == []


def test_no_includes_pass_through():
    lines = list(parse_lines.from_string('one\ntwo\nthree'))
    assert list(resolve_includes(lines)) == lines


def test_include(fs):
    fs.create_file('/f', contents='hi')
    assert list(resolve_includes(parse_includes(parse_lines.from_string('%include /f')))) == [
        Line('hi', 1, '/f')
    ]


def test_circular_include_errors(fs):
    fs.create_file('/f', contents='%include /f')
    with raises(CircularIncludeError):
        list(resolve_includes(parse_includes(parse_lines.from_string('%include /f'))))

def test_relative_path(fs):
    fs.create_file('/a/f', contents='%include ../b/g')
    fs.create_file('/b/g', contents='%include c/h')
    fs.create_file('/b/c/h', contents='hi')
    result = list(resolve_includes(parse_includes(parse_lines.from_string('%include /a/f'))))
    assert result == [
        Line('hi', 1, '/b/c/h')
    ]
