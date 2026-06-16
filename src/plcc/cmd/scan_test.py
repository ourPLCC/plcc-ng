import io
import json
import subprocess
import sys
from types import SimpleNamespace

import pytest

from .scan import ScanHandler, main as run_main
from .source_runner import SubmitOn
import plcc.cmd.scan as _scan_module


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


def test_scan_handler_renders_error_records(monkeypatch, capsys):
    error = json.dumps({
        "kind": "error", "stage": "plcc-tokens", "severity": "error",
        "source": {"file": "-", "line": 1, "column": 1},
        "lexeme": "@", "message": "unrecognized character '@'"
    }).encode() + b"\n"
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: _make_proc([error]))
    handler = ScanHandler(spec_path="build/spec.json", tokens_flags=[])
    handler.feed(b"@\n", "-")
    out, _ = capsys.readouterr()
    assert "-:1:1: error: unrecognized character '@'" in out
    assert out.count("'@'") == 1


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


# --- main() banner ---


def test_main_uses_eof_submit_mode(monkeypatch, tmp_path):
    build = tmp_path / "build"
    build.mkdir()
    (build / ".spec").write_text(str(tmp_path / "grammar.plcc"))
    captured = {}
    def fake_runner(**kw):
        captured.update(kw)
        return type("R", (), {"run": lambda self, s, h: True})()
    monkeypatch.setattr(_scan_module, "SourceRunner", fake_runner)
    monkeypatch.setattr("plcc.cmd.scan.get_version", lambda: "0")
    run_main([])
    assert captured.get("submit_on") == SubmitOn.EOF



def test_main_default_prints_no_banner_to_stdout(monkeypatch, capsys):
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=1))
    monkeypatch.setattr("plcc.cmd.scan.get_version", lambda: "1.2.3")
    with pytest.raises(SystemExit):
        run_main([])
    out, _ = capsys.readouterr()
    assert "plcc-ng" not in out


def test_main_banner_prints_version_to_stderr(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    build = tmp_path / "build"
    build.mkdir()
    (build / ".spec").write_text(str(tmp_path / "grammar.plcc"))
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0))
    monkeypatch.setattr(_scan_module, "SourceRunner",
                        lambda **kw: type("R", (), {"run": lambda self, s, h: True})())
    monkeypatch.setattr("plcc.cmd.scan.get_version", lambda: "1.2.3")
    run_main(["--banner"])
    _, err = capsys.readouterr()
    assert "plcc-ng 1.2.3" in err


def test_main_banner_prints_grammar_to_stderr(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    build = tmp_path / "build"
    build.mkdir()
    (build / ".spec").write_text(str(tmp_path / "grammar.plcc"))
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0))
    monkeypatch.setattr(_scan_module, "SourceRunner",
                        lambda **kw: type("R", (), {"run": lambda self, s, h: True})())
    monkeypatch.setattr("plcc.cmd.scan.get_version", lambda: "1.2.3")
    run_main(["--banner"])
    _, err = capsys.readouterr()
    assert "spec:" in err
    assert str(tmp_path / "grammar.plcc") in err
