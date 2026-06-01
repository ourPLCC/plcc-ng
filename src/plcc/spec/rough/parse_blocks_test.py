from pytest import raises

from ... import lines
from .Block import Block
from .parse_blocks import parse_blocks
from .UnclosedBlockError import UnclosedBlockError


def test_None_yields_nothing():
    assert list(parse_blocks(None)) == []


def test_empty_yields_nothing():
    assert list(parse_blocks([])) == []


def test_non_block_lines_are_passed_through():
    lines_ = list(lines.parseLines('one\ntwo'))
    assert list(parse_blocks(lines_)) == lines_


def test_unclosed_block_is_an_error():
    OPEN = '%%%'
    with raises(UnclosedBlockError) as info:
        list(parse_blocks(lines.parseLines(OPEN)))
    exception = info.value
    assert exception.line == lines.Line('%%%', 1, None)


def test_handler():
    def ignore(_):
        pass
    OPEN = '%%%'
    results = list(parse_blocks(lines.parseLines(OPEN), handler=ignore))
    assert results[0].__class__ == Block    # A Block was produced.
    assert len(results[0].lines) == 2       # A closing line was added.


def test_triple_percent_block():
    lines_ = list(lines.parseLines('''\
%%%
block
%%%
'''))
    assert list(parse_blocks(lines_)) == [ Block(lines_) ]


def test_triple_percent_with_trailing_space_is_block_delimiter():
    lines_ = list(lines.parseLines('%%% \nblock\n%%% \n'))
    assert list(parse_blocks(lines_)) == [Block(lines_)]


def test_pplc_is_a_plain_line():
    lines_ = list(lines.parseLines('%%{'))
    assert list(parse_blocks(lines_)) == lines_


def test_pprc_is_a_plain_line():
    lines_ = list(lines.parseLines('%%}'))
    assert list(parse_blocks(lines_)) == lines_
