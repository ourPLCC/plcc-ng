import pytest

from ...lines import Line
from .Block import Block
from .Divider import Divider
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
% java
three
% python
four
% c++
%%%
%include nope
% nope
%%%
''')
    assert rough_ == [
        Line('one', 1, None),
        Divider(tool='Java', language='Java', line=Line('%', 2, None)),
        Line('two', 3, None),
        Divider(tool='java', language='java', line=Line('% java', 4, None)),
        Line('three', 5, None),
        Divider(tool='python', language='python', line=Line('% python', 6, None)),
        Line('four', 7, None),
        Divider(tool='c++', language='c++', line=Line('% c++', 8, None)),
        Block([
            Line('%%%', 9, None),
            Line('%include nope', 10, None),
            Line('% nope', 11, None),
            Line('%%%', 12, None)
        ])
    ]


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


