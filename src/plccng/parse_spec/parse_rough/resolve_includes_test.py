from pytest import raises
from ..structs import Line
from . import parse_rough
from .parse_includes import parse_includes
from .resolve_includes import resolve_includes, CircularIncludeError


def test_None_yields_nothing():
    assert list(resolve_includes(None)) == []


def test_empty_yields_nothing():
    assert list(resolve_includes([])) == []


def test_unresolved_pass_through():
    lines = list(parse_rough.from_string_unresolved('one\ntwo\nthree'))
    assert list(resolve_includes(lines)) == lines


def test_include(fs):
    fs.create_file('/f', contents='hi')
    assert list(resolve_includes(parse_rough.from_string_unresolved('%include /f'))) == [
        Line('hi', 1, '/f')
    ]


def test_circular_include_errors(fs):
    fs.create_file('/f', contents='%include /f')
    with raises(CircularIncludeError):
        list(resolve_includes(parse_rough.from_string_unresolved('%include /f')))


def test_relative_path(fs):
    fs.create_file('/a/f', contents='%include ../b/g')
    fs.create_file('/b/g', contents='%include c/h')
    fs.create_file('/b/c/h', contents='hi')
    result = list(resolve_includes(parse_rough.from_string_unresolved('%include /a/f')))
    assert result == [
        Line('hi', 1, '/b/c/h')
    ]
