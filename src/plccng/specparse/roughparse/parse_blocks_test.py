from pytest import raises

from .. import lineparse
from .Block import Block
from .parse_blocks import parse_blocks
from .UnclosedBlockError import UnclosedBlockError


def test_None_yields_nothing():
    assert list(parse_blocks(None)) == []


def test_empty_yields_nothing():
    assert list(parse_blocks([])) == []


def test_non_block_lines_are_passed_through():
    lines = list(lineparse.fromstring('one\ntwo'))
    assert list(parse_blocks(lines)) == lines


def test_unclosed_block_is_an_error():
    OPEN = '%%%'
    with raises(UnclosedBlockError) as info:
        list(parse_blocks(lineparse.fromstring(OPEN)))
    exception = info.value
    assert exception.line == lineparse.Line('%%%', 1, None)


def test_tripple_percent_block():
    lines = list(lineparse.fromstring('''\
%%%
block
%%%
'''))
    assert list(parse_blocks(lines)) == [ Block(lines) ]


def test_curly_percent_block():
    lines = list(lineparse.fromstring('''\
%%{
block
%%}
'''))
    assert list(parse_blocks(lines)) == [ Block(lines) ]


def test_nested_blocks_produce_single_block():
    lines = list(lineparse.fromstring('''\
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
    lines = list(lineparse.fromstring('''\

%%%
one
two
%%%

%%{
three
%%}

'''))

    assert list(parse_blocks(lines)) == [
        lineparse.Line('', 1, None),
        Block(list(lineparse.fromstring('%%%\none\ntwo\n%%%', startLineNumber=2))),
        lineparse.Line('', 6, None),
        Block(list(lineparse.fromstring('%%{\nthree\n%%}', startLineNumber=7))),
        lineparse.Line('', 10, None),
    ]
