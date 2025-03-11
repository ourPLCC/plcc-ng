from pytest import raises

from .. import lines
from .Block import Block
from .parse_blocks import parse_blocks
from .UnclosedBlockError import UnclosedBlockError


def test_None_yields_nothing():
    assert list(parse_blocks(None)) == []


def test_empty_yields_nothing():
    assert list(parse_blocks([])) == []


def test_non_block_lines_are_passed_through():
    lines_ = list(lines.parse_from_string('one\ntwo'))
    assert list(parse_blocks(lines_)) == lines_


def test_unclosed_block_is_an_error():
    OPEN = '%%%'
    with raises(UnclosedBlockError) as info:
        list(parse_blocks(lines.parse_from_string(OPEN)))
    exception = info.value
    assert exception.line == lines.Line('%%%', 1, None)


def test_handler():
    def ignore(_):
        pass
    OPEN = '%%%'
    results = list(parse_blocks(lines.parse_from_string(OPEN), handler=ignore))
    assert results[0].__class__ == Block    # A Block was produced.
    assert len(results[0].lines) == 2       # A closing line was added.


def test_triple_percent_block():
    lines_ = list(lines.parse_from_string('''\
%%%
block
%%%
'''))
    assert list(parse_blocks(lines_)) == [ Block(lines_) ]


def test_curly_percent_block():
    lines_ = list(lines.parse_from_string('''\
%%{
block
%%}
'''))
    assert list(parse_blocks(lines_)) == [ Block(lines_) ]


def test_nested_blocks_produce_single_block():
    lines_ = list(lines.parse_from_string('''\
%%{
what
%%%
block
%%%
ever
%%}
'''))
    assert list(parse_blocks(lines_)) == [ Block(lines_) ]


def test_mixed():
    lines_ = list(lines.parse_from_string('''\

%%%
one
two
%%%

%%{
three
%%}

'''))

    assert list(parse_blocks(lines_)) == [
        lines.Line('', 1, None),
        Block(list(lines.parse_from_string('%%%\none\ntwo\n%%%', startLineNumber=2))),
        lines.Line('', 6, None),
        Block(list(lines.parse_from_string('%%{\nthree\n%%}', startLineNumber=7))),
        lines.Line('', 10, None),
    ]
