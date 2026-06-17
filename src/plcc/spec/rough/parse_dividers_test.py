from pytest import raises
from ... import lines
from .Block import Block
from .Divider import Divider
from .UnexpectedTokensOnDividerError import UnexpectedTokensOnDividerError
from .parse_blocks import parse_blocks
from .parse_dividers import parse_dividers


def test_None_yields_nothing():
    assert list(parse_dividers(None)) == []


def test_empty_yields_nothing():
    assert list(parse_dividers([])) == []


def test_non_dividers_pass_through():
    lines_ = list(parse_blocks(lines.parseLines('''\
one
%%%
two
%%%
three
''')))
    assert list(parse_dividers(lines_)) == lines_


def test_bare_percent_yields_divider():
    lines_ = list(lines.parseLines('%'))
    result = list(parse_dividers(lines_))
    assert result == [Divider(line=lines_[0])]


def test_percent_with_trailing_whitespace_yields_divider():
    lines_ = list(lines.parseLines('%  '))
    result = list(parse_dividers(lines_))
    assert result == [Divider(line=lines_[0])]


def test_percent_with_token_raises_error():
    with raises(UnexpectedTokensOnDividerError):
        list(parse_dividers(list(lines.parseLines('% Java'))))


def test_percent_with_two_tokens_raises_error():
    with raises(UnexpectedTokensOnDividerError):
        list(parse_dividers(list(lines.parseLines('% tool Java'))))


def test_percent_with_three_tokens_raises_error():
    with raises(UnexpectedTokensOnDividerError):
        list(parse_dividers(list(lines.parseLines('% a b c'))))


def test_double_percent_does_not_match():
    lines_ = list(lines.parseLines('%%'))
    assert list(parse_dividers(lines_)) == [lines.Line('%%', 1, None)]


def test_blocks_mask_dividers():
    lines_ = list(parse_blocks(lines.parseLines('%%%\n%\n%%%')))
    assert list(parse_dividers(lines_)) == [
        Block([
            lines_[0].lines[0],
            lines_[0].lines[1],
            lines_[0].lines[2]
        ])
    ]
