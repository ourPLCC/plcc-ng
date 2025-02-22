import plccng.lineparse as lineparse

from plccng.roughparse.Block import Block
from plccng.roughparse.Include import Include
from .parse_blocks import parse_blocks
from .parse_includes import parse_includes


def test_None_yields_nothing():
    assert list(parse_includes(None)) == []


def test_empty_yields_nothing():
    assert list(parse_includes([])) == []


def test_non_includes_pass_through():
    lines = list(parse_blocks(lineparse.fromstring('''\
one
%%%
two
%%%
three
''')))
    assert list(parse_includes(lines)) == lines


def test_include():
    lines = list(lineparse.fromstring('''\
%include file
'''))
    assert list(parse_includes(lines)) == [
        Include(
            file='file',
            line=lineparse.Line('%include file', 1, None)
        )
    ]


def test_ignores_includes_in_blocks():
    lines = list(parse_blocks(lineparse.fromstring('''\
%%%
%include file
%%%
''')))
    assert list(parse_includes(lines)) == [
        Block(
            [
                lineparse.Line('%%%', 1, None),
                lineparse.Line('%include file', 2, None),
                lineparse.Line('%%%', 3, None)
            ]
        )
    ]
