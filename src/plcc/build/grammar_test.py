# src/plcc/build/grammar_test.py
from pathlib import Path
import pytest
from plcc.build.grammar import read_grammar, write_grammar


def test_read_grammar_returns_none_when_absent(tmp_path):
    assert read_grammar(tmp_path) is None


def test_read_grammar_returns_stored_path(tmp_path):
    (tmp_path / ".grammar").write_text("a.plcc")
    assert read_grammar(tmp_path) == "a.plcc"


def test_write_grammar_creates_file(tmp_path):
    write_grammar(tmp_path, "a.plcc")
    assert (tmp_path / ".grammar").read_text() == "a.plcc"


def test_write_grammar_overwrites_existing(tmp_path):
    write_grammar(tmp_path, "a.plcc")
    write_grammar(tmp_path, "b.plcc")
    assert read_grammar(tmp_path) == "b.plcc"
