import pytest

from ...lines import Line
from .Block import Block
from .Divider import Divider
from .UnexpectedTokensOnDividerError import UnexpectedTokensOnDividerError
from .parseRough import parseRough


def test_TypeError():
    with pytest.raises(TypeError):
        parseRough(3)


def test_parse_empty_list():
    rough_, errors = parseRough([])
    assert rough_ == []


def test_parse_None():
    rough_, errors = parseRough(None)
    assert rough_ == []


def test_parse_empty_string():
    rough_, errors = parseRough('')
    assert rough_ == []


def test_parse_happy():
    rough_, errors = parseRough('''\
one
%
two
%%%
%include nope
% nope
%%%
''')
    assert rough_ == [
        Line('one\n', 1, None),
        Divider(line=Line('%\n', 2, None)),
        Line('two\n', 3, None),
        Block([
            Line('%%%\n', 4, None),
            Line('%include nope\n', 5, None),
            Line('% nope\n', 6, None),
            Line('%%%\n', 7, None)
        ])
    ]


def test_percent_with_token_raises_error():
    with pytest.raises(UnexpectedTokensOnDividerError):
        parseRough('% java\n')


def test_parse_from_string_with_handler(fs):
    fs.create_file('/contains_circular_include', contents='%include /contains_circular_include')

    rough_, errors = parseRough('''\
%include /contains_circular_include
%%%
missing
closing
''')

    assert len(errors) == 2
    assert rough_[0].__class__ == Block
