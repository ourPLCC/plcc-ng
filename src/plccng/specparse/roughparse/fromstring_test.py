from plccng.lineparse.Line import Line

from .Block import Block
from .Divider import Divider
from .fromstring import fromstring


def test_fromstring():
    assert list(fromstring('''\
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
