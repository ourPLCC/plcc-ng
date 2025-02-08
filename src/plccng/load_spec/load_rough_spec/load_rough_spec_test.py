from pytest import raises, mark, fixture

from ..structs import Line, RoughSpec
from ..structs import Block, Divider
from .parse_dividers import parse_dividers
from .load_rough_spec import load_rough_spec
from .split_rough_spec import split_rough_spec


def test_load_rough_spec(fs):
    fs.create_file('A.java', contents='hi in java')
    fs.create_file('B.py', contents='hi in python')
    fs.create_file('test.py', contents='''\
one
%
two
% java
%include /A.java
% python
%include /B.py
% c++
%%%
%include nope
% nope
%%%
''')
    assert load_rough_spec('test.py') == split_rough_spec([
        makeLine('one', 1, 'test.py'),
        makeDivider('%', 2, 'test.py'),
        makeLine('two', 3, 'test.py'),
        makeDivider('% java', 4, 'test.py'),
        makeLine('hi in java', 1, '/A.java'),
        makeDivider('% python', 6, 'test.py'),
        makeLine('hi in python', 1, '/B.py'),
        makeDivider('% c++', 8, 'test.py'),
        makeBlock('''
            %%%
            %include nope
            % nope
            %%%
        ''', 9, 12, 'test.py')
    ])


def test_include_with_relative_path(fs):
    fs.create_file('A.java', contents='hi in java')
    fs.create_file('test.py', contents='''\
%include A.java
''')
    assert load_rough_spec('test.py') == split_rough_spec([
        makeLine('hi in java', 1, '/A.java')
    ])


def makeLine(string, lineNumber=None, file=None):
    return Line(string, lineNumber, file)


def makeDivider(string, lineNumber=None, file=None):
    return next(parse_dividers([makeLine(string, lineNumber, file)]))

def makeBlock(string, startLine, endLine, file=None):
    return Block([makeLine(s.strip(), num, file) for s, num in zip(string.strip().split('\n'), range(startLine, endLine + 1))])

