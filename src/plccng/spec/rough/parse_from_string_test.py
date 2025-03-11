from ..lines.Line import Line
from .Block import Block
from .Divider import Divider
from .parse_from_string import parse_from_string


def test_parse_from_string():
    assert list(parse_from_string('''\
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
''')) == [
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
    errors = 0
    def count(_):
        nonlocal errors
        errors += 1

    fs.create_file('/contains_circular_include', contents='%include /contains_circular_include')

    results = list(parse_from_string(handler=count, string='''\
%include /contains_circular_include
%%%
missing
closing
'''))

    assert errors == 2
    assert results[0].__class__ == Block
