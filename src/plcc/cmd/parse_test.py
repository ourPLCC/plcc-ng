import io
import json
import subprocess
import sys
from types import SimpleNamespace

import pytest

from .parse import ParseHandler


def _proc(stdout=b"", returncode=0):
    p = SimpleNamespace(returncode=returncode)
    p.communicate = lambda: (stdout, b"")
    p.wait = lambda: None
    p.stdin = io.BytesIO()
    p.stdout = io.BytesIO(stdout)
    return p


def _tree_record():
    return json.dumps({
        "kind": "tree", "rule": "program",
        "source": {}, "children": []
    }).encode() + b"\n"


def _error_record(msg="syntax error", stage="plcc-tokens"):
    return json.dumps({"kind": "error", "message": msg, "stage": stage}).encode() + b"\n"


def _error_record_with_source(msg="syntax error", stage="plcc-parser-table",
                               file="-", line=2, col=5):
    return json.dumps({
        "kind": "error", "message": msg, "stage": stage,
        "source": {"file": file, "line": line, "column": col},
    }).encode() + b"\n"


@pytest.fixture()
def handler():
    return ParseHandler(spec_path="build/spec.json", ll1_path="build/ll1.json",
                        child_flags=[])


def test_feed_returns_true_when_tree_produced(monkeypatch, handler):
    procs = iter([_proc(), _proc(stdout=_tree_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    assert handler.feed(b"1+2\n", "-") is True


def test_feed_returns_false_when_stdout_empty(monkeypatch, handler):
    procs = iter([_proc(), _proc(stdout=b"")])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    assert handler.feed(b"1+\n", "-") is False


def test_feed_returns_true_on_error_record(monkeypatch, handler):
    procs = iter([_proc(), _proc(stdout=_error_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    assert handler.feed(b"bad input\n", "-") is True


def test_feed_prints_tree(monkeypatch, handler, capsys):
    procs = iter([_proc(), _proc(stdout=_tree_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"1\n", "-")
    out, _ = capsys.readouterr()
    assert "program" in out


def test_feed_prints_error_to_stderr(monkeypatch, handler, capsys):
    procs = iter([_proc(), _proc(stdout=_error_record("oops"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"bad\n", "-")
    _, err = capsys.readouterr()
    assert "oops" in err


def test_feed_error_shows_location_in_stderr(monkeypatch, handler, capsys):
    procs = iter([_proc(), _proc(stdout=_error_record_with_source("bad char", file="-", line=1, col=1))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"@\n", "-")
    _, err = capsys.readouterr()
    assert "-:1:1" in err


def test_feed_error_renders_file_line_col(monkeypatch, handler, capsys):
    procs = iter([_proc(), _proc(stdout=_error_record_with_source("bad", file="foo.txt", line=3, col=7))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"bad\n", "-")
    _, err = capsys.readouterr()
    assert "foo.txt:3:7" in err
    assert "bad" in err


def test_feed_mixed_tree_and_error_renders_both(monkeypatch, handler, capsys):
    combined = _tree_record() + _error_record_with_source("trailing")
    procs = iter([_proc(), _proc(stdout=combined)])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"input\n", "-")
    out, err = capsys.readouterr()
    assert "program" in out
    assert "trailing" in err
    assert handler.had_error is True


def test_feed_sets_had_error_on_error_record(monkeypatch, handler):
    procs = iter([_proc(), _proc(stdout=_error_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"bad\n", "-")
    assert handler.had_error is True


def test_feed_does_not_set_had_error_on_success(monkeypatch, handler):
    procs = iter([_proc(), _proc(stdout=_tree_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"ok\n", "-")
    assert handler.had_error is False


def test_feed_error_with_no_location_shows_stage(monkeypatch, handler, capsys):
    procs = iter([_proc(), _proc(stdout=_error_record("bad char", stage="plcc-tokens"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"@\n", "-")
    _, err = capsys.readouterr()
    assert "plcc-tokens: error: bad char" in err


def _eof_error_record(msg="unexpected end of input: expected 'PLUS'",
                      stage="plcc-parser-table", line=1, col=1):
    return json.dumps({
        "kind": "error", "message": msg, "stage": stage,
        "found": "eof",
        "source": {"file": "-", "line": line, "column": col},
    }).encode() + b"\n"


def test_feed_returns_false_for_eof_only_error_when_trial(monkeypatch, handler):
    procs = iter([_proc(), _proc(stdout=_eof_error_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    assert handler.feed(b"1+\n", "-", eof=False) is False


def test_feed_returns_true_for_eof_only_error_when_force_submit(monkeypatch, handler):
    procs = iter([_proc(), _proc(stdout=_eof_error_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    assert handler.feed(b"1+\n", "-", eof=True) is True


def test_feed_suppresses_stderr_for_eof_error_when_trial(monkeypatch, handler, capsys):
    procs = iter([_proc(), _proc(stdout=_eof_error_record("expected PLUS"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"1+\n", "-", eof=False)
    _, err = capsys.readouterr()
    assert err == ""


def test_feed_shows_stderr_for_eof_error_when_force_submit(monkeypatch, handler, capsys):
    procs = iter([_proc(), _proc(stdout=_eof_error_record("expected PLUS"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"1+\n", "-", eof=True)
    _, err = capsys.readouterr()
    assert "expected PLUS" in err


def test_feed_returns_true_for_genuine_error_regardless_of_eof_param(monkeypatch, handler):
    procs = iter([_proc(), _proc(stdout=_error_record("bad token"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    # _error_record has no "found" field → genuine error → always True
    assert handler.feed(b"@\n", "-", eof=False) is True
