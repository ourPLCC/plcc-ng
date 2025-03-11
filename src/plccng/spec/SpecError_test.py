
from .lines import Line
from .SpecError import SpecError


def test_basic():
    e = SpecError(line=Line("hi", 1, "example.plcc"), message="This is an example.", column=1)
    assert str(e) == '''\
SpecError: example.plcc:1:1
hi
^
This is an example.
'''


def test_inheritance():
    class Hi(SpecError):
        ...

    e = Hi(line=Line("hi", 1, "example.plcc"), message="This is an example.", column=1)
    assert str(e) == '''\
Hi: example.plcc:1:1
hi
^
This is an example.
'''


def test_no_message():
    e = SpecError(line=Line("hi", 1, "example.plcc"), message=None, column=1)
    assert str(e) == '''\
SpecError: example.plcc:1:1
hi
^
'''
