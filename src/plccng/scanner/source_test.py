import io
import pytest
from ..load_spec.structs import Line

from .source import Source


def test_none_returns_empty():
    assert list(Source(None)) == []


def test_empty_returns_empty():
    assert list(Source([])) == []


def test_random_file_throws(fs):
    with pytest.raises(OSError):
        s = Source(['whereami'])
        assert list(s) == []


def test_one_line_reads(fs):
    createFile(fs)
    source = Source(["main"])
    assert list(source) == [createLine()]


def test_two_lines_read(fs):
    createFile(fs, contents='''
               <hello> ::= WORLD
               <plcc> ::= NEXTGEN
               ''')

    source = Source(["main"])
    assert list(source) == [createLine(),
                            createLine(string="<plcc> ::= NEXTGEN", number=2)]


def test_two_files_read(fs):
    createFile(fs)
    createFile(fs, name="./helper", contents="<plcc> ::= NEXTGEN")

    source = Source(["main", "helper"])
    assert list(source) == [createLine(),
                            createLine(string="<plcc> ::= NEXTGEN", file="helper")]


def test_stdin_works(monkeypatch):
    createStdin(monkeypatch)
    source = Source(["-"])
    assert list(source) == [createStdinLine()]


def test_stdin_works_nestled(monkeypatch, fs):
    createFile(fs)
    createStdin(monkeypatch)
    createFile(fs, name="./helper", contents="<plcc> ::= NEXTGEN")

    source = Source(["main", "-", "helper"])
    assert list(source) == [createLine(),
                            createStdinLine(),
                            createLine(string="<plcc> ::= NEXTGEN", file="helper")]


def test_stdin_works_first(monkeypatch, fs):
    createStdin(monkeypatch)
    createFile(fs)
    createFile(fs, name="./helper", contents="<plcc> ::= NEXTGEN")

    source = Source(["-", "main", "helper"])
    assert list(source) == [createStdinLine(),
                            createLine(),
                            createLine(string="<plcc> ::= NEXTGEN", file="helper")]


def test_stdin_works_last(monkeypatch, fs):
    createFile(fs)
    createFile(fs, name="./helper", contents="<plcc> ::= NEXTGEN")
    createStdin(monkeypatch)

    source = Source(["main", "helper", "-"])
    assert list(source) == [createLine(),
                            createLine(string="<plcc> ::= NEXTGEN",
                                       file="helper"),
                            createStdinLine()]


def test_multi_line_stdin(monkeypatch):
    createStdin(monkeypatch, '''
                <stda> ::= HELLO
                <stdb> ::= FROM STDIN
                ''')

    source = Source(["-"])
    assert list(source) == [createStdinLine(string="<stda> ::= HELLO", number=1),
                            createStdinLine(string="<stdb> ::= FROM STDIN", number=2)]


def test_stdin_escapes(monkeypatch):
    createStdin(monkeypatch, "<stda> ::= HELLO\n<stdb> ::= FROM STDIN")

    source = Source(["-"])
    assert list(source) == [createStdinLine(string="<stda> ::= HELLO", number=1),
                            createStdinLine(string="<stdb> ::= FROM STDIN", number=2)]


def test_next_iterates(monkeypatch, fs):
    createFile(fs)
    createStdin(monkeypatch, '''
                <stda> ::= HELLO
                <stdb> ::= FROM STDIN
                ''')

    source = Source(["main", "-"])
    assert next(source) == createLine()
    assert next(source) == createStdinLine(string="<stda> ::= HELLO", number=1)
    assert next(source) == createStdinLine(
        string="<stdb> ::= FROM STDIN", number=2)


def createFile(fs, name="./main", contents="<hello> ::= WORLD"):
    fs.create_file(name, contents=contents)


def createStdin(monkeypatch, contents="<hello> ::= FROM STDIN"):
    monkeypatch.setattr('sys.stdin', io.StringIO(contents))


def createLine(string="<hello> ::= WORLD", number=1, file="main"):
    return Line(string=string,
                number=number,
                file=file)


def createStdinLine(string="<hello> ::= FROM STDIN", number=1):
    return createLine(string=string,
                      number=number,
                      file="-")
