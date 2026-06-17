import pytest

from ...lines import Line
from .. import rough
from .LanguageDeclaration import LanguageDeclaration
from .MissingLanguageDeclarationError import MissingLanguageDeclarationError
from .parse_semantic_spec import parse_semantic_spec


def test_language_extracted_from_first_non_blank_line():
    section = [make_divider('%'), make_line('Python'), make_block()]
    spec = parse_semantic_spec(section)
    assert spec.language == 'Python'


def test_language_extracted_skips_blank_lines():
    section = [make_divider('%'), make_line(''), make_line('  '), make_line('Java')]
    spec = parse_semantic_spec(section)
    assert spec.language == 'Java'


def test_language_extracted_skips_comment_lines():
    section = [make_divider('%'), make_line('# a comment'), make_line('Python')]
    spec = parse_semantic_spec(section)
    assert spec.language == 'Python'


def test_language_is_stripped():
    section = [make_divider('%'), make_line('  Python  ')]
    spec = parse_semantic_spec(section)
    assert spec.language == 'Python'


def test_code_fragments_follow_language_line():
    section = [make_divider('%'), make_line('Python'), make_line('Program'), make_block()]
    spec = parse_semantic_spec(section)
    assert len(spec.codeFragmentList) == 1
    assert spec.codeFragmentList[0].targetLocator.className == 'Program'


def test_no_code_fragments_is_valid():
    section = [make_divider('%'), make_line('Python')]
    spec = parse_semantic_spec(section)
    assert spec.codeFragmentList == []


def test_no_language_line_raises_error():
    section = [make_divider('%')]
    with pytest.raises(MissingLanguageDeclarationError):
        parse_semantic_spec(section)


def test_only_blank_lines_raises_error():
    section = [make_divider('%'), make_line(''), make_line('  ')]
    with pytest.raises(MissingLanguageDeclarationError):
        parse_semantic_spec(section)


def test_only_comment_lines_raises_error():
    section = [make_divider('%'), make_line('# comment')]
    with pytest.raises(MissingLanguageDeclarationError):
        parse_semantic_spec(section)


def test_spec_has_no_tool_attribute():
    section = [make_divider('%'), make_line('Python')]
    spec = parse_semantic_spec(section)
    assert not hasattr(spec, 'tool')


def make_divider(string, number=1):
    return rough.Divider(line=make_line(string, number))


def make_block():
    rough_, _ = rough.parseRough('%%%\nblock\n%%%\n')
    return rough_[0]


def make_line(string, number=1):
    return Line(string, number, None)
