import io
import json
import subprocess
import sys
from types import SimpleNamespace

import pytest

from .rep import RepHandler


def _proc(stdout=b"", returncode=0):
    p = SimpleNamespace(returncode=returncode)
    p.communicate = lambda: (stdout, b"")
    p.wait = lambda: None
    p.stdin = io.BytesIO()
    p.stdout = io.BytesIO(stdout)
    return p


def _tree():
    return json.dumps({
        "kind": "tree", "rule": "program",
        "source": {}, "children": []
    }).encode() + b"\n"


def _error_record():
    return json.dumps({"kind": "error", "message": "bad"}).encode() + b"\n"


def _make_interpreter(response=b'{"kind":"result","value":"42"}\n'):
    interp = SimpleNamespace()
    interp.stdin = io.BytesIO()
    interp.stdout = io.BytesIO(response)
    return interp


@pytest.fixture()
def handler(monkeypatch):
    interp = _make_interpreter()
    return RepHandler(
        spec_path="build/spec.json",
        ll1_path="build/ll1.json",
        interpreter=interp,
        verbose_format="text",
    ), interp


def test_feed_returns_false_when_no_tree(monkeypatch, handler):
    h, _ = handler
    procs = iter([_proc(), _proc(stdout=b"")])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    assert h.feed(b"1+\n", "-") is False


def test_feed_returns_true_when_tree_produced(monkeypatch, handler):
    h, _ = handler
    procs = iter([_proc(), _proc(stdout=_tree())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    assert h.feed(b"42\n", "-") is True


def test_feed_does_not_contact_interpreter_when_no_tree(monkeypatch, handler):
    h, interp = handler
    procs = iter([_proc(), _proc(stdout=b"")])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    h.feed(b"1+\n", "-")
    assert interp.stdin.tell() == 0  # nothing written to interpreter


def test_feed_sends_tree_to_interpreter(monkeypatch, handler):
    h, interp = handler
    procs = iter([_proc(), _proc(stdout=_tree())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    h.feed(b"42\n", "-")
    written = interp.stdin.getvalue()
    assert b"tree" in written


def test_feed_prints_result(monkeypatch, handler, capsys):
    h, _ = handler
    procs = iter([_proc(), _proc(stdout=_tree())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    h.feed(b"42\n", "-")
    out, _ = capsys.readouterr()
    assert "42" in out


def test_feed_returns_true_on_error_record(monkeypatch, handler):
    h, _ = handler
    procs = iter([_proc(), _proc(stdout=_error_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    assert h.feed(b"bad\n", "-") is True
