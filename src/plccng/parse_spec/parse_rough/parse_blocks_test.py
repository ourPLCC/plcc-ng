from pytest import raises
from ..structs import Block, Line
from . import parse_lines
from .parse_blocks import parse_blocks, UnclosedBlockError


def test_None_yields_nothing():
    assert list(parse_blocks(None)) == []


def test_empty_yields_nothing():
    assert list(parse_blocks([])) == []


def test_non_block_lines_are_passed_through():
    lines = list(parse_lines.from_string('one\ntwo'))
    assert list(parse_blocks(lines)) == lines


def test_unclosed_block_is_an_error():
    OPEN = '%%%'
    with raises(UnclosedBlockError) as info:
        list(parse_blocks(parse_lines.from_string(OPEN)))
    exception = info.value
    assert exception.line == Line('%%%', 1, None)


def test_tripple_percent_block():
    lines = list(parse_lines.from_string('''\
%%%
block
%%%
'''))
    assert list(parse_blocks(lines)) == [ Block(lines) ]


def test_curly_percent_block():
    lines = list(parse_lines.from_string('''\
%%{
block
%%}
'''))
    assert list(parse_blocks(lines)) == [ Block(lines) ]


def test_nested_blocks_produce_single_block():
    lines = list(parse_lines.from_string('''\
%%{
what
%%%
block
%%%
ever
%%}
'''))
    assert list(parse_blocks(lines)) == [ Block(lines) ]


def test_mixed():
    lines = list(parse_lines.from_string('''\

%%%
one
two
%%%

%%{
three
%%}

'''))

    assert list(parse_blocks(lines)) == [
        Line('', 1, None),
        Block(list(parse_lines.from_string('%%%\none\ntwo\n%%%', startLineNumber=2))),
        Line('', 6, None),
        Block(list(parse_lines.from_string('%%{\nthree\n%%}', startLineNumber=7))),
        Line('', 10, None),
    ]
