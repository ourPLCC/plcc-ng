import io
from source import (
    Source,
    Line
    )
import os

def test_none_returns_empty():
    assert Source(None).lines == []

def test_empty_returns_empty():
    assert Source([]).lines == []

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
    monkeypatch.setattr('sys.stdin', io.StringIO('my input'))
