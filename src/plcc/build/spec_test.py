# src/plcc/build/spec_test.py
from plcc.build.spec import read_spec, write_spec, resolve_spec_path, DEFAULT_SPEC_FILE


def test_read_spec_returns_none_when_absent(tmp_path):
    assert read_spec(tmp_path) is None


def test_read_spec_returns_stored_path(tmp_path):
    (tmp_path / ".spec").write_text("a.plcc")
    assert read_spec(tmp_path) == "a.plcc"


def test_write_spec_creates_file(tmp_path):
    write_spec(tmp_path, "a.plcc")
    assert (tmp_path / ".spec").read_text() == "a.plcc"


def test_write_spec_overwrites_existing(tmp_path):
    write_spec(tmp_path, "a.plcc")
    write_spec(tmp_path, "b.plcc")
    assert read_spec(tmp_path) == "b.plcc"


def test_read_spec_returns_none_when_empty(tmp_path):
    (tmp_path / ".spec").write_text("   ")
    assert read_spec(tmp_path) is None


def test_resolve_spec_path_explicit_wins():
    assert resolve_spec_path('explicit.plcc', 'stored.plcc') == 'explicit.plcc'


def test_resolve_spec_path_uses_stored_when_no_explicit():
    assert resolve_spec_path(None, 'stored.plcc') == 'stored.plcc'


def test_resolve_spec_path_falls_back_to_default():
    assert resolve_spec_path(None, None) == DEFAULT_SPEC_FILE
