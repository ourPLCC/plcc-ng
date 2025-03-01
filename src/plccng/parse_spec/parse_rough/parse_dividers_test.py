from ..structs import Block, Divider, Line
from . import parse_lines
from .parse_blocks import parse_blocks
from .parse_dividers import parse_dividers


def test_None_yields_nothing():
    assert list(parse_dividers(None)) == []


def test_empty_yields_nothing():
    assert list(parse_dividers([])) == []


def test_non_dividers_pass_through():
    lines = list(parse_blocks(parse_lines.from_string('''\
one
%%%
two
%%%
three
''')))
    assert list(parse_dividers(lines)) == lines


def test_one_divider():
    lines = list(parse_lines.from_string('%'))
    assert list(parse_dividers(lines)) == [
        make_divider(tool='Java', language='Java', line=lines[0])
    ]


def test_one_divider_with_same_language_tool():
    lines = list(parse_lines.from_string('% trailing'))
    assert list(parse_dividers(lines)) == [
        make_divider(tool='trailing', language='trailing', line=lines[0]),
    ]


def test_one_divider_with_different_language_tool():
    lines = list(parse_lines.from_string('% linter python '))
    assert list(parse_dividers(lines)) == [
        make_divider(tool='linter', language='python', line=lines[0]),
    ]


def test_one_divider_with_different_but_same_language_tool():
    lines = list(parse_lines.from_string('% python python'))
    assert list(parse_dividers(lines)) == [
        make_divider(tool='python', language='python', line=lines[0]),
    ]


def test_one_divider_only_takes_first_two_lines():
    lines = list(parse_lines.from_string('% java python c++'))
    assert list(parse_dividers(lines)) == [
        make_divider(tool='java', language='python', line=lines[0])
    ]


def test_two_percents_does_not_match():
    lines = list(parse_lines.from_string('%%'))
    assert list(parse_dividers(lines)) == [
        Line('%%', 1, None),
    ]


def test_blocks_mask_dividers():
    lines = list(parse_blocks(parse_lines.from_string('%%%\n%\n%%%')))
    assert list(parse_dividers(lines)) == [
        Block([
            lines[0].lines[0],
            lines[0].lines[1],
            lines[0].lines[2]
        ])
    ]


def make_divider(tool, language, line):
    return Divider(tool=tool, language=language, line=line)
