
from .lines import Line

from .ValidationError2 import ValidationError2


def test_basic():
    e = ValidationError2(line=Line("hi", 1, "example.plcc"), message="This is an example.", column=1)
    assert str(e) == '''\
ValidationError2: example.plcc:1:1
hi
^
This is an example.
'''


def test_inheritance():
    class Hi(ValidationError2):
        ...

    e = Hi(line=Line("hi", 1, "example.plcc"), message="This is an example.", column=1)
    assert str(e) == '''\
Hi: example.plcc:1:1
hi
^
This is an example.
'''


def test_no_message():
    e = ValidationError2(line=Line("hi", 1, "example.plcc"), message=None, column=1)
    assert str(e) == '''\
ValidationError2: example.plcc:1:1
hi
^
'''
