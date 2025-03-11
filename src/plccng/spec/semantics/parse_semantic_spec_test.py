from pytest import raises

from ..lines.Line import Line
from .. import rough
from .parse_semantic_spec import parse_code_fragments, parse_semantic_spec


def test_basic():
    lines_divider_and_blocks = [make_divider('Java', 'Java', make_line('%')), make_line('Class:init'), make_block()]
    semantic_spec = parse_semantic_spec(lines_divider_and_blocks)
    assert semantic_spec.language, semantic_spec.tool == 'Java'
    assert semantic_spec.codeFragmentList == parse_code_fragments(lines_divider_and_blocks[1:])

def test_empty_list():
    with raises(IndexError):
        parse_semantic_spec([])

def test_no_CodeFragments():
    list_with_Divider = [make_divider('Java', 'Java', make_line('%'))]
    semantic_spec = parse_semantic_spec(list_with_Divider)
    assert semantic_spec.codeFragmentList == []
    assert semantic_spec.language, semantic_spec.tool == 'Java'

# def make_block():
#     return  Block(list(parse_lines.from_string('''\
# %%%
# block
# %%%
# ''')))

def make_block():
    rough_, errors = rough.parse_rough('''\
%%%
block
%%%
''')
    return  rough_[0]


def make_divider(tool, language, line):
    return rough.Divider(tool=tool, language=language, line=line)

def make_line(string, number=1, file=None):
    return Line(string, number, file)
