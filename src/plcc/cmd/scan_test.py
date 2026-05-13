import io
import json
import subprocess
import sys
from types import SimpleNamespace

import pytest

from .scan import ScanHandler, main as run_main


def _make_proc(stdout_lines=None):
    data = b"".join(stdout_lines or [])
    return SimpleNamespace(
        stdout=io.BytesIO(data),
        returncode=0,
        wait=lambda: None,
        communicate=lambda inp=None: (data, b""),
    )


@pytest.fixture(autouse=True)
def grammar(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "grammar.plcc").write_text("")


@pytest.fixture(autouse=True)
def stub_make(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0))


# --- ScanHandler.feed() ---

def test_scan_handler_passes_source_name_to_plcc_tokens(monkeypatch):
    calls = []
    def fake_popen(cmd, **kw):
        calls.append(cmd)
        return _make_proc()
    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    handler = ScanHandler(spec_path="build/spec.json", tokens_flags=[])
    handler.feed(b"hello\n", "myfile.txt")
    assert any("--source-name=myfile.txt" in arg for arg in calls[0])


def test_scan_handler_always_returns_true(monkeypatch):
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: _make_proc())
    handler = ScanHandler(spec_path="build/spec.json", tokens_flags=[])
    assert handler.feed(b"", "-") is True
    assert handler.feed(b"anything\n", "foo.txt") is True


def test_scan_handler_renders_token_records(monkeypatch, capsys):
    token = json.dumps({
        "kind": "token", "name": "NUM", "lexeme": "42",
        "source": {"file": "-", "line": 1, "column": 1}
    }).encode() + b"\n"
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: _make_proc([token]))
    handler = ScanHandler(spec_path="build/spec.json", tokens_flags=[])
    handler.feed(b"42\n", "-")
    out, _ = capsys.readouterr()
    assert "NUM" in out
    assert "42" in out
