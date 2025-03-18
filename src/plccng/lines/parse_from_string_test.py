import pytest

from .Line import Line
from .parseLines import parseLines


def test_None_yields_nothing():
    assert list(parseLines(None)) == []


def test_empty_yields_nothing():
    assert list(parseLines('')) == []


def test_eol_yields_single_empty_line():
    assert list(parseLines('\n')) == [Line('', 1, None)]


def test_one_line_without_eol_yields_single_line():
    assert list(parseLines('one')) == [Line('one', 1, None)]


def test_one_line_with_eol_yields_single_line():
    assert list(parseLines('one\n')) == [Line('one', 1, None)]


def test_multiple_lines():
    assert list(parseLines('one\ntwo')) == [Line('one', 1, None), Line('two', 2, None)]


def test_set_start_of_numbering():
    assert list(parseLines('one\ntwo', startLineNumber=3)) == [Line('one', 3, None), Line('two', 4, None)]


def test_set_file():
    assert list(parseLines('one\ntwo', file='/f')) == [Line('one', 1, '/f'), Line('two', 2, '/f')]


def test_strings():
    lines = parseLines([
        'one',
        'two'
    ], file='/f')
    lines == [Line('one', 1, '/f'), Line('two', 2, '/f')]


def test_TypeError():
    with pytest.raises(TypeError):
        parseLines(3)


def test_file(fs):
    fs.create_file('/f', contents="one")
    assert parseLines(file='/f') == [Line(string='one', number=1, file='/f')]
