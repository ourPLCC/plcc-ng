import io

import pytest

from ..lines import Line
from .source import Source


def test_none_returns_empty():
    assert list(Source(None)) == []


def test_empty_returns_empty():
    assert list(Source([])) == []


def test_random_file_throws(fs):
    with pytest.raises(OSError):
        list(Source(['./whereami']))


def test_one_line_reads(fs):
    fs.create_file("./word", contents="<hello> ::= WORLD")
    source = Source(["./word"])
    assert list(source) == [makeLine("<hello> ::= WORLD",1,"./word")]


def test_two_lines_read(fs):
    fs.create_file("./word", contents='''
                   <hello> ::= WORLD
                   <clang> ::= SEGFAULT
                   ''')

    source = Source(["./word"])
    assert list(source) == [
        makeLine('',1,'./word'),
        makeLine("<hello> ::= WORLD",2,"./word"),
        makeLine("<clang> ::= SEGFAULT",3,"./word"),
        makeLine('',4,'./word')
    ]


def test_two_files_read(fs):
    fs.create_file("./hello", contents="<hello> ::= WORLD")
    fs.create_file("./world", contents="<clang> ::= SEGFAULT")

    source = Source(["./hello", "./world"])
    assert list(source) == [makeLine("<hello> ::= WORLD",1,"./hello"),
                            makeLine("<clang> ::= SEGFAULT",1,"./world")]


def test_stdin_works(monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO('<hello> ::= FROM STDIN'))
    source = Source(["-"])
    assert list(source) == [makeLine("<hello> ::= FROM STDIN",1,"-")]


def test_stdin_works_nestled(monkeypatch, fs):
    monkeypatch.setattr('sys.stdin', io.StringIO('<hello> ::= FROM STDIN'))
    fs.create_file("./hello", contents="<hello> ::= WORLD")
    fs.create_file("./world", contents="<clang> ::= SEGFAULT")
    source = Source(["./hello","-","./world"])
    assert list(source) == [makeLine("<hello> ::= WORLD",1,"./hello"),
                            makeLine("<hello> ::= FROM STDIN",1,"-"),
                            makeLine("<clang> ::= SEGFAULT",1,"./world")]


def test_stdin_works_first(monkeypatch, fs):
    monkeypatch.setattr('sys.stdin', io.StringIO('<hello> ::= FROM STDIN'))
    fs.create_file("./hello", contents="<hello> ::= WORLD")
    fs.create_file("./world", contents="<clang> ::= SEGFAULT")
    source = Source(["-","./hello","./world"])
    assert list(source) == [makeLine("<hello> ::= FROM STDIN",1,"-"),
                            makeLine("<hello> ::= WORLD",1,"./hello"),
                            makeLine("<clang> ::= SEGFAULT",1,"./world")]


def test_stdin_works_last(monkeypatch, fs):
    monkeypatch.setattr('sys.stdin', io.StringIO('<hello> ::= FROM STDIN'))
    fs.create_file("./hello", contents="<hello> ::= WORLD")
    fs.create_file("./world", contents="<clang> ::= SEGFAULT")
    source = Source(["./hello","./world", "-"])
    assert list(source) == [makeLine("<hello> ::= WORLD",1,"./hello"),
                            makeLine("<clang> ::= SEGFAULT",1,"./world"),
                            makeLine("<hello> ::= FROM STDIN",1,"-")]


def test_multi_line_stdin(monkeypatch, fs):
    monkeypatch.setattr('sys.stdin', io.StringIO('''
                                    <stda> ::= HELLO
                                    <stdb> ::= FROM STDIN
                                    '''))
    fs.create_file("./hello", contents="<hello> ::= WORLD")
    source = Source(["./hello", "-"])
    assert list(source) == [
        makeLine("<hello> ::= WORLD",1,"./hello"),
        makeLine("",1,"-"),
        makeLine("<stda> ::= HELLO",2,"-"),
        makeLine("<stdb> ::= FROM STDIN",3,"-"),
        makeLine("",4,"-")
    ]


def test_next_iterates(monkeypatch, fs):
    monkeypatch.setattr('sys.stdin', io.StringIO('''
                                    <stda> ::= HELLO
                                    <stdb> ::= FROM STDIN
                                    '''))
    fs.create_file("./hello", contents="<hello> ::= WORLD")
    source = Source(["./hello", "-"])
    assert next(source) ==  makeLine("<hello> ::= WORLD",1,"./hello")
    assert next(source) ==  makeLine("",1,"-")
    assert next(source) ==  makeLine("<stda> ::= HELLO",2,"-")
    assert next(source) ==  makeLine("<stdb> ::= FROM STDIN",3,"-")
    assert next(source) ==  makeLine("",4,"-")


def makeLine(string, number, file=None):
    return Line(string, number, file)
