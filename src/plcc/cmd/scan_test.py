import io
import subprocess
import sys
from types import SimpleNamespace

import pytest

from .scan import main as run_main

HINT = "Enter input. Press ^D (EOF) when done."


def _make_proc():
    return SimpleNamespace(
        stdout=io.BytesIO(b""),
        returncode=0,
        wait=lambda: None,
    )


@pytest.fixture(autouse=True)
def grammar(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "grammar.plcc").write_text("")


@pytest.fixture(autouse=True)
def stub_subprocesses(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0))
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: _make_proc())


def test_hint_printed_for_implicit_stdin_when_tty(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(isatty=lambda: True))
    run_main([])
    _, err = capsys.readouterr()
    assert err.count(HINT) == 1


def test_hint_printed_for_explicit_dash_source_when_tty(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(isatty=lambda: True))
    run_main(["-"])
    _, err = capsys.readouterr()
    assert err.count(HINT) == 1


def test_hint_printed_twice_for_two_dash_sources_when_tty(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(isatty=lambda: True))
    run_main(["-", "-"])
    _, err = capsys.readouterr()
    assert err.count(HINT) == 2


def test_hint_absent_when_not_tty(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(isatty=lambda: False))
    run_main([])
    _, err = capsys.readouterr()
    assert HINT not in err


def test_hint_absent_for_file_source_even_when_tty(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(isatty=lambda: True))
    run_main(["somefile.txt"])
    _, err = capsys.readouterr()
    assert HINT not in err
