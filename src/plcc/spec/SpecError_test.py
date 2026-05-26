from ..lines import Line
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


def _line(string='test line', number=1, file='test.plcc'):
    return Line(string=string, number=number, file=file)


def test_kind_returns_message_when_set():
    err = SpecError(line=_line(), message="pattern is invalid", column=1)
    assert err.kind == "pattern is invalid"


def test_kind_returns_class_name_when_message_is_none():
    err = SpecError(line=_line(), column=1)
    assert err.kind == "SpecError"


def test_hint_returns_none():
    err = SpecError(line=_line(), message="anything", column=1)
    assert err.hint is None
