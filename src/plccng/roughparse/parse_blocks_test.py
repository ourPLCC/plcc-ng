from pytest import raises

from plccng.lineparse import Line
from plccng.roughparse.structs import Block
import plccng.lineparse as lines_
from .structs import UnclosedBlockError
from .parse_blocks import parse_blocks


def test_None_yields_nothing():
    assert list(parse_blocks(None)) == []


def test_empty_yields_nothing():
    assert list(parse_blocks([])) == []


def test_non_block_lines_are_passed_through():
    lines = list(lines_.fromString('one\ntwo'))
    assert list(parse_blocks(lines)) == lines


def test_unclosed_block_is_an_error():
    OPEN = '%%%'
    with raises(UnclosedBlockError) as info:
        list(parse_blocks(lines_.fromString(OPEN)))
    exception = info.value
    assert exception.line == Line('%%%', 1, None)


def test_tripple_percent_block():
    lines = list(lines_.fromString('''\
%%%
block
%%%
'''))
    assert list(parse_blocks(lines)) == [ Block(lines) ]


def test_curly_percent_block():
    lines = list(lines_.fromString('''\
%%{
block
%%}
'''))
    assert list(parse_blocks(lines)) == [ Block(lines) ]


def test_nested_blocks_produce_single_block():
    lines = list(lines_.fromString('''\
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
    lines = list(lines_.fromString('''\

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
        Block(list(lines_.fromString('%%%\none\ntwo\n%%%', startLineNumber=2))),
        Line('', 6, None),
        Block(list(lines_.fromString('%%{\nthree\n%%}', startLineNumber=7))),
        Line('', 10, None),
    ]
