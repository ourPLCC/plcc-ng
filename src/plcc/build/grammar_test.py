# src/plcc/build/grammar_test.py
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


def test_read_grammar_returns_none_when_empty(tmp_path):
    (tmp_path / ".grammar").write_text("   ")
    assert read_grammar(tmp_path) is None


from plcc.build.grammar import resolve_grammar_path, DEFAULT_GRAMMAR_FILE


def test_resolve_grammar_path_explicit_wins():
    assert resolve_grammar_path('explicit.plcc', 'stored.plcc') == 'explicit.plcc'


def test_resolve_grammar_path_uses_stored_when_no_explicit():
    assert resolve_grammar_path(None, 'stored.plcc') == 'stored.plcc'


def test_resolve_grammar_path_falls_back_to_default():
    assert resolve_grammar_path(None, None) == DEFAULT_GRAMMAR_FILE
