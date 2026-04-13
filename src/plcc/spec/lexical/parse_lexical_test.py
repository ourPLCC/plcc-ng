import pytest

from .parseLexicalSpec import parseLexicalSpec
from .Parser import NameExpected, PatternExpected, PatternDelimiterExpected, UnexpectedContent
from .check_for_duplicate_names import DuplicateName

def test_TypeError():
    with pytest.raises(TypeError):
        parseLexicalSpec(3)


def test_None():
    spec, errors = parseLexicalSpec(None)
    assert errors == []
    assert spec.ruleList == []


def test_empty():
    spec, errors = parseLexicalSpec('')
    assert errors == []
    assert spec.ruleList == []


def test_blank_lines():
    spec, errors = parseLexicalSpec('\n\n\n\n')
    assert errors == []
    assert spec.ruleList == []


def test_comments():
    spec, errors = parseLexicalSpec('''
# comment
    # another
''')
    assert errors == []
    assert spec.ruleList == []


def test_skip():
    spec, errors = parseLexicalSpec('''
        skip SPACE ' '
    ''')
    assert errors == []
    assert len(spec.ruleList) == 1
    assert spec.ruleList[0].isSkip


def test_token_rule():
    spec, errors = parseLexicalSpec('''
        token SPACE ' '
    ''')
    assert errors == []
    assert len(spec.ruleList) == 1
    assert not spec.ruleList[0].isSkip


def test_implicit_token_rule():
    spec, errors = parseLexicalSpec('''
        SPACE ' '
    ''')
    assert errors == []
    assert len(spec.ruleList) == 1
    assert not spec.ruleList[0].isSkip


def test_choice_of_pattern_delimiter():
    spec, errors = parseLexicalSpec('''
        SPACE [ [
    ''')
    assert errors == []
    assert len(spec.ruleList) == 1
    assert not spec.ruleList[0].isSkip


def test_pattern_must_compile():
    spec, errors = parseLexicalSpec('''
        SPACE '[ '
    ''')
    assert len(errors) == 1
    assert len(spec.ruleList) == 0


def test_trailing_comment():
    spec, errors = parseLexicalSpec('''
        SPACE ' ' # comment
    ''')
    assert errors == []
    assert len(spec.ruleList) == 1
    assert not spec.ruleList[0].isSkip


def test_no_space():
    spec, errors = parseLexicalSpec('''
        tokenSPACE' '# comment
    ''')
    assert errors == []
    assert len(spec.ruleList) == 1
    assert not spec.ruleList[0].isSkip


def test_names_start_with_uppercase_or_underscore_and_may_contain_numbers():
    spec, errors = parseLexicalSpec('''
        SPACE_3 ' '
    ''')
    assert errors == []
    assert len(spec.ruleList) == 1
    assert not spec.ruleList[0].isSkip

    spec, errors = parseLexicalSpec('''
        _SPACE3_ ' '
    ''')
    assert errors == []
    assert len(spec.ruleList) == 1
    assert not spec.ruleList[0].isSkip


def test_names_must_be_uppercase():
    spec, errors = parseLexicalSpec('''
        space ' '
    ''')
    assert len(errors) == 1
    assert errors[0].__class__ == NameExpected
    assert len(spec.ruleList) == 0


def test_names_must_start_with_uppercase():
    spec, errors = parseLexicalSpec('''
        3SPACE ' '
    ''')
    assert len(errors) == 1
    assert errors[0].__class__ == NameExpected
    assert len(spec.ruleList) == 0

    spec, errors = parseLexicalSpec('''
        :SPACE ' '
    ''')
    assert len(errors) == 1
    assert errors[0].__class__ == NameExpected
    assert len(spec.ruleList) == 0


def test_pattern_is_required():
    spec, errors = parseLexicalSpec('''
        SPACE
    ''')
    assert len(errors) == 1
    assert errors[0].__class__ == PatternExpected
    assert len(spec.ruleList) == 0


def test_pattern_must_have_closing_delimiter():
    spec, errors = parseLexicalSpec('''
        SPACE '
    ''')
    assert len(errors) == 1
    assert errors[0].__class__ == PatternDelimiterExpected
    assert len(spec.ruleList) == 0


def test_junk_at_the_end_of_a_line():
    spec, errors = parseLexicalSpec('''
        SPACE ' ' junk
    ''')
    assert len(errors) == 1
    assert errors[0].__class__ == UnexpectedContent
    assert len(spec.ruleList) == 1


def test_hash_in_pattern_is_not_a_comment():
    spec, errors = parseLexicalSpec('''
        HASH '#'
    ''')
    assert len(errors) == 0
    assert len(spec.ruleList) == 1


def test_no_leading_space_required():
    spec, errors = parseLexicalSpec('''
HASH '#'
    ''')
    assert len(errors) == 0
    assert len(spec.ruleList) == 1


def test_no_duplicate_token_names():
    spec, errors = parseLexicalSpec('''
        token ONE 'one'
        token ONE 'two'
    ''')
    assert len(errors) == 1
    assert errors[0].__class__ == DuplicateName
    assert len(spec.ruleList) == 2

def test_no_duplicate_skip_names():
    spec, errors = parseLexicalSpec('''
        skip ONE 'one'
        skip ONE 'two'
    ''')
    assert len(errors) == 1
    assert errors[0].__class__ == DuplicateName
    assert len(spec.ruleList) == 2


def test_no_duplicate_token_skip_names():
    spec, errors = parseLexicalSpec('''
        token ONE 'one'
        skip ONE 'two'
    ''')
    assert len(errors) == 1
    assert errors[0].__class__ == DuplicateName
    assert len(spec.ruleList) == 2


def test_no_duplicate_skip_token_names():
    spec, errors = parseLexicalSpec('''
        token ONE 'one'
        skip ONE 'two'
    ''')
    assert len(errors) == 1
    assert errors[0].__class__ == DuplicateName
    assert len(spec.ruleList) == 2


def test_two_duplicate_names():
    spec, errors = parseLexicalSpec('''
        ONE 'one1'
        TWO 'two1'
        NOT 'duplicate'
        ONE 'one2'
        TWO 'two2'
    ''')
    assert len(errors) == 2
    assert errors[0].__class__ == DuplicateName
    assert errors[1].__class__ == DuplicateName
    assert len(spec.ruleList) == 5


def test_multiple_of_same_duplication():
    spec, errors = parseLexicalSpec('''
        ONE 'one1'
        ONE 'one2'
        ONE 'one3'
    ''')
    assert len(errors) == 2
    assert errors[0].__class__ == DuplicateName
    assert errors[1].__class__ == DuplicateName
    assert len(spec.ruleList) == 3
