from .. import lines
from .Block import Block
from .Include import Include
from .parse_blocks import parse_blocks
from .parse_includes import parse_includes


def test_None_yields_nothing():
    assert list(parse_includes(None)) == []


def test_empty_yields_nothing():
    assert list(parse_includes([])) == []


def test_non_includes_pass_through():
    lines_ = list(parse_blocks(lines.parse_from_string('''\
one
%%%
two
%%%
three
''')))
    assert list(parse_includes(lines_)) == lines_


def test_include():
    lines_ = list(lines.parse_from_string('''\
%include file
'''))
    assert list(parse_includes(lines_)) == [
        Include(
            file='file',
            line=lines.Line('%include file', 1, None)
        )
    ]


def test_ignores_includes_in_blocks():
    lines_ = list(parse_blocks(lines.parse_from_string('''\
%%%
%include file
%%%
''')))
    assert list(parse_includes(lines_)) == [
        Block(
            [
                lines.Line('%%%', 1, None),
                lines.Line('%include file', 2, None),
                lines.Line('%%%', 3, None)
            ]
        )
    ]
