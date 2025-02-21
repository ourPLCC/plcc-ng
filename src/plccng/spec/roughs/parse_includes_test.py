from plccng.lines import Line
import plccng.lines as lines_
from plccng.spec.structs import Block, Include
from .parse_blocks import parse_blocks
from .parse_includes import parse_includes


def test_None_yields_nothing():
    assert list(parse_includes(None)) == []


def test_empty_yields_nothing():
    assert list(parse_includes([])) == []


def test_non_includes_pass_through():
    lines = list(parse_blocks(lines_.fromString('''\
one
%%%
two
%%%
three
''')))
    assert list(parse_includes(lines)) == lines


def test_include():
    lines = list(lines_.fromString('''\
%include file
'''))
    assert list(parse_includes(lines)) == [
        Include(
            file='file',
            line=Line('%include file', 1, None)
        )
    ]


def test_ignores_includes_in_blocks():
    lines = list(parse_blocks(lines_.fromString('''\
%%%
%include file
%%%
''')))
    assert list(parse_includes(lines)) == [
        Block(
            [
                Line('%%%', 1, None),
                Line('%include file', 2, None),
                Line('%%%', 3, None)
            ]
        )
    ]
