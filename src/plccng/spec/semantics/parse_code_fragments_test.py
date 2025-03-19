from pytest import raises

from .. import rough
from ...lines import Line
from .CodeFragment import CodeFragment
from .parse_code_fragments import parse_code_fragments
from .TargetLocator import TargetLocator


def test_basic():
    lines_and_blocks = [make_line('Class:init'), make_block()]
    assert parse_code_fragments(lines_and_blocks) == [
        CodeFragment(make_target_locator(lines_and_blocks[0], 'Class', 'init'), make_block())]

def test_consecutive():
    lines_and_blocks = [make_line('Class:init'), make_block(), make_line('Main'), make_block()]
    assert parse_code_fragments(lines_and_blocks) == [
        CodeFragment(make_target_locator(lines_and_blocks[0], 'Class', 'init'), make_block()),
        CodeFragment(make_target_locator(lines_and_blocks[2], 'Main', None), make_block())]

def test_input_must_be_Lines_and_Blocks():
    invalid_input = ["Only Lines and Dividers Work!", make_line('Class'), make_block()]
    with raises(TypeError):
        parse_code_fragments(invalid_input)

def test_empty_lines_ignored():
    lines = [make_line('Class:init'), make_line('\n'), make_line(''), None, make_block()]
    assert parse_code_fragments(lines) == [
        CodeFragment(make_target_locator(lines[0], 'Class', 'init'), make_block())]

def test_consecutive_target_locators_generate_code_fragment_with_undefined_block():
    lines_and_blocks = [make_line('Class:init'), make_line('AnotherClass:init'), make_block()]
    assert parse_code_fragments(lines_and_blocks) == [
        CodeFragment(make_target_locator(lines_and_blocks[0], 'Class', 'init'), None),
        CodeFragment(make_target_locator(lines_and_blocks[1], 'AnotherClass', 'init'), lines_and_blocks[2])]

def test_adjacent_blocks_parses_undefined_target_locator():
    lines_and_blocks = [make_line('Class:init'), make_block(), make_block()]
    assert parse_code_fragments(lines_and_blocks) == [
        CodeFragment(make_target_locator(lines_and_blocks[0], 'Class', 'init'), lines_and_blocks[1]),
        CodeFragment(None, lines_and_blocks[2])
    ]

def test_single_block_parses_undefined_target_locator():
    lines_and_blocks = [make_block()]
    assert parse_code_fragments(lines_and_blocks) == [
        CodeFragment(None, lines_and_blocks[0])
    ]

def test_consecutive_blocks_parse_undefined_target_lacators():
    blocks = [make_block(), make_block()]
    code_fragments = parse_code_fragments(blocks)
    assert code_fragments == [
        CodeFragment(None, blocks[0]),
        CodeFragment(None, blocks[1])
    ]

def test_mismatched_target_locator_and_block_make_two_code_fragments():
    lines_and_blocks = [make_block(), make_line('Class:init')]
    code_fragments = parse_code_fragments(lines_and_blocks)
    assert code_fragments == [
        CodeFragment(None, lines_and_blocks[0]),
        CodeFragment(make_target_locator(lines_and_blocks[1], 'Class', 'init'), None)
    ]

def test_missing_blocks_are_defined_as_None():
    lines_and_blocks = [make_line('Class:init')]
    assert parse_code_fragments(lines_and_blocks) == [
        CodeFragment(make_target_locator(lines_and_blocks[0], 'Class', 'init'), None)]

def make_target_locator(line, className, modifier):
    return TargetLocator(line, className, modifier)

def make_block():
    rough_, errors = rough.parseRough('''\
%%%
block
%%%
''')
    return  rough_[0]

def make_line(string, number=1, file=None):
    return Line(string, number, file)
