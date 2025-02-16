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
    fs.create_file("./word", contents="<hello> ::= WORLD")
    source = Source(["word"])
    assert list(source) == [Line("<hello> ::= WORLD",1,"word")]

def test_two_lines_read(fs):
    fs.create_file("./word", contents='''
                   <hello> ::= WORLD
                   <clang> ::= SEGFAULT
                   ''')

    source = Source(["word"])
    assert list(source) == [Line("<hello> ::= WORLD",1,"word"),
                            Line("<clang> ::= SEGFAULT",2,"word")]

def test_two_files_read(fs):
    fs.create_file("./hello", contents="<hello> ::= WORLD")
    fs.create_file("./world", contents="<clang> ::= SEGFAULT")

    source = Source(["hello", "world"])
    assert list(source) == [Line("<hello> ::= WORLD",1,"hello"),
                            Line("<clang> ::= SEGFAULT",1,"world")]

def test_stdin_works(monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO('<hello> ::= FROM STDIN'))
    source = Source(["-"])
    assert list(source) == [Line("<hello> ::= FROM STDIN",1,"-")]

def test_stdin_works_nestled(monkeypatch, fs):
    monkeypatch.setattr('sys.stdin', io.StringIO('<hello> ::= FROM STDIN'))
    fs.create_file("./hello", contents="<hello> ::= WORLD")
    fs.create_file("./world", contents="<clang> ::= SEGFAULT")
    source = Source(["hello","-","world"])
    assert list(source) == [Line("<hello> ::= WORLD",1,"hello"),
                            Line("<hello> ::= FROM STDIN",1,"-"),
                            Line("<clang> ::= SEGFAULT",1,"world")]

def test_stdin_works_first(monkeypatch, fs):
    monkeypatch.setattr('sys.stdin', io.StringIO('<hello> ::= FROM STDIN'))
    fs.create_file("./hello", contents="<hello> ::= WORLD")
    fs.create_file("./world", contents="<clang> ::= SEGFAULT")
    source = Source(["-","hello","world"])
    assert list(source) == [Line("<hello> ::= FROM STDIN",1,"-"),
                            Line("<hello> ::= WORLD",1,"hello"),
                            Line("<clang> ::= SEGFAULT",1,"world")]

def test_stdin_works_last(monkeypatch, fs):
    monkeypatch.setattr('sys.stdin', io.StringIO('<hello> ::= FROM STDIN'))
    fs.create_file("./hello", contents="<hello> ::= WORLD")
    fs.create_file("./world", contents="<clang> ::= SEGFAULT")
    source = Source(["hello","world", "-"])
    assert list(source) == [Line("<hello> ::= WORLD",1,"hello"),
                            Line("<clang> ::= SEGFAULT",1,"world"),
                            Line("<hello> ::= FROM STDIN",1,"-")]

def test_multi_line_stdin(monkeypatch, fs):
    monkeypatch.setattr('sys.stdin', io.StringIO('''
                                    <stda> ::= HELLO
                                    <stdb> ::= FROM STDIN
                                    '''))
    fs.create_file("./hello", contents="<hello> ::= WORLD")
    source = Source(["hello", "-"])
    assert list(source) == [Line("<hello> ::= WORLD",1,"hello"),
                            Line("<stda> ::= HELLO",1,"-"),
                            Line("<stdb> ::= FROM STDIN",2,"-")]

def test_stdin_escapes(monkeypatch, fs):
    monkeypatch.setattr('sys.stdin', io.StringIO('''<stda> ::= HELLO\n<stdb> ::= FROM STDIN'''))
    fs.create_file("./hello", contents="<hello> ::= WORLD")
    source = Source(["hello", "-"])
    assert list(source) == [Line("<hello> ::= WORLD",1,"hello"),
                            Line("<stda> ::= HELLO",1,"-"),
                            Line("<stdb> ::= FROM STDIN",2,"-")]

def test_next_iterates(monkeypatch, fs):
    monkeypatch.setattr('sys.stdin', io.StringIO('''
                                    <stda> ::= HELLO
                                    <stdb> ::= FROM STDIN
                                    '''))
    fs.create_file("./hello", contents="<hello> ::= WORLD")
    source = Source(["hello", "-"])
    assert next(source) ==  Line("<hello> ::= WORLD",1,"hello")
    assert next(source) ==  Line("<stda> ::= HELLO",1,"-")
    assert next(source) ==  Line("<stdb> ::= FROM STDIN",2,"-")
