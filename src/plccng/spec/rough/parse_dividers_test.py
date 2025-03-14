from .. import lines
from .Block import Block
from .Divider import Divider
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


def test_one_divider():
    lines_ = list(lines.parseLines('%'))
    assert list(parse_dividers(lines_)) == [
        make_divider(tool='Java', language='Java', line=lines_[0])
    ]


def test_one_divider_with_same_language_tool():
    lines_ = list(lines.parseLines('% trailing'))
    assert list(parse_dividers(lines_)) == [
        make_divider(tool='trailing', language='trailing', line=lines_[0]),
    ]


def test_one_divider_with_different_language_tool():
    lines_ = list(lines.parseLines('% linter python '))
    assert list(parse_dividers(lines_)) == [
        make_divider(tool='linter', language='python', line=lines_[0]),
    ]


def test_one_divider_with_different_but_same_language_tool():
    lines_ = list(lines.parseLines('% python python'))
    assert list(parse_dividers(lines_)) == [
        make_divider(tool='python', language='python', line=lines_[0]),
    ]


def test_one_divider_only_takes_first_two_lines():
    lines_ = list(lines.parseLines('% java python c++'))
    assert list(parse_dividers(lines_)) == [
        make_divider(tool='java', language='python', line=lines_[0])
    ]


def test_two_percents_does_not_match():
    lines_ = list(lines.parseLines('%%'))
    assert list(parse_dividers(lines_)) == [
        lines.Line('%%', 1, None),
    ]


def test_blocks_mask_dividers():
    lines_ = list(parse_blocks(lines.parseLines('%%%\n%\n%%%')))
    assert list(parse_dividers(lines_)) == [
        Block([
            lines_[0].lines[0],
            lines_[0].lines[1],
            lines_[0].lines[2]
        ])
    ]


def make_divider(tool, language, line):
    return Divider(tool=tool, language=language, line=line)
