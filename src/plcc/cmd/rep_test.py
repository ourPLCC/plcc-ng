import io
import json as _json
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock as _MagicMock

import pytest

import plcc.cmd.rep as _rep_module
from plcc.verbose import VerboseContext
from .rep import RepHandler
from .source_runner import SubmitOn
from ._test_helpers import (
    _proc, _tree_record, _error_record, _error_record_with_source,
    _eof_error_record,
)


def test_main_uses_eof_submit_mode(monkeypatch, tmp_path):
    """plcc-rep interactive mode must submit on ^D, not Enter (SubmitOn.EOF)."""
    monkeypatch.chdir(tmp_path)
    grammar = tmp_path / "grammar.plcc"
    grammar.write_text("")
    build = tmp_path / "build"
    build.mkdir()
    spec = {"semantics": [{"tool": "calc", "language": "python"}]}
    (build / "spec.json").write_text(_json.dumps(spec))
    (build / "ll1.json").write_text("{}")

    captured = {}

    def capturing_runner(submit_on, **kwargs):
        captured["submit_on"] = submit_on
        m = _MagicMock()
        m.run.return_value = True
        return m

    monkeypatch.setattr(_rep_module, "SourceRunner", capturing_runner)
    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **kw: _MagicMock(returncode=0, stderr=b""),
    )
    monkeypatch.setattr(
        "subprocess.Popen",
        lambda *a, **kw: _MagicMock(stdin=_MagicMock(), wait=_MagicMock()),
    )

    _rep_module.main(["--grammar-file=grammar.plcc", "--tool=calc"])

    assert captured["submit_on"] is SubmitOn.EOF


def _make_interpreter(response=b'{"kind":"result","value":"42"}\n'):
    interp = SimpleNamespace()
    interp.stdin = io.BytesIO()
    interp.stdout = io.BytesIO(response)
    return interp


def _make_dead_interpreter(returncode):
    """Simulate an interpreter whose stdout is closed (empty) and has exited."""
    interp = SimpleNamespace()
    interp.stdin = io.BytesIO()
    interp.stdout = io.BytesIO(b"")   # empty — readline() returns b""
    interp.poll = lambda: returncode
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
    procs = iter([_proc(), _proc(stdout=_tree_record())])
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
    procs = iter([_proc(), _proc(stdout=_tree_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    h.feed(b"42\n", "-")
    written = interp.stdin.getvalue()
    assert b"tree" in written


def test_feed_prints_result(monkeypatch, handler, capsys):
    h, _ = handler
    procs = iter([_proc(), _proc(stdout=_tree_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    h.feed(b"42\n", "-")
    out, _ = capsys.readouterr()
    assert "42" in out


def test_feed_returns_true_on_error_record(monkeypatch, handler):
    h, _ = handler
    procs = iter([_proc(), _proc(stdout=_error_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    assert h.feed(b"bad\n", "-") is True


def test_feed_accepts_eof_kwarg(monkeypatch, handler):
    h, _ = handler
    procs = iter([_proc(), _proc(stdout=b"")])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    assert h.feed(b"\n", "-", eof=True) is False


def test_feed_handles_non_dict_json_number_from_interpreter(monkeypatch, handler, capsys):
    # Interpreter emits a bare JSON number then a proper result record.
    response = b'42\n{"kind":"result","value":"ok"}\n'
    h, _ = handler
    h._interpreter.stdout = io.BytesIO(response)
    procs = iter([_proc(), _proc(stdout=_tree_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    h.feed(b"1\n", "-")
    out, _ = capsys.readouterr()
    assert "42" in out
    assert "ok" in out


def test_feed_handles_non_dict_json_array_from_interpreter(monkeypatch, handler, capsys):
    # Interpreter emits a JSON array then a proper result record.
    response = b'[1,2,3]\n{"kind":"result","value":"done"}\n'
    h, _ = handler
    h._interpreter.stdout = io.BytesIO(response)
    procs = iter([_proc(), _proc(stdout=_tree_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    h.feed(b"1\n", "-")
    out, _ = capsys.readouterr()
    assert "[1, 2, 3]" in out or "[1,2,3]" in out
    assert "done" in out


# --- EOF error detection ---

def test_feed_returns_false_for_eof_only_error_when_trial(monkeypatch, handler):
    h, _ = handler
    procs = iter([_proc(), _proc(stdout=_eof_error_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    assert h.feed(b"1+\n", "-", eof=False) is False


def test_feed_returns_true_for_eof_only_error_when_force_submit(monkeypatch, handler):
    h, _ = handler
    procs = iter([_proc(), _proc(stdout=_eof_error_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    assert h.feed(b"1+\n", "-", eof=True) is True


def test_feed_suppresses_output_for_eof_error_when_trial(monkeypatch, handler, capsys):
    h, _ = handler
    procs = iter([_proc(), _proc(stdout=_eof_error_record("expected PLUS"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    h.feed(b"1+\n", "-", eof=False)
    out, _ = capsys.readouterr()
    assert out == ""


def test_feed_shows_output_for_eof_error_when_force_submit(monkeypatch, handler, capsys):
    h, _ = handler
    procs = iter([_proc(), _proc(stdout=_eof_error_record("expected PLUS"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    h.feed(b"1+\n", "-", eof=True)
    out, _ = capsys.readouterr()
    assert "expected PLUS" in out


def test_feed_returns_true_for_genuine_error_regardless_of_eof(monkeypatch, handler):
    h, _ = handler
    procs = iter([_proc(), _proc(stdout=_error_record("bad token"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    assert h.feed(b"@\n", "-", eof=False) is True


# --- child_flags propagation ---

def test_feed_passes_child_flags_to_subprocesses(monkeypatch):
    calls = []

    def mock_popen(args, **kwargs):
        calls.append(list(args))
        return _proc()

    monkeypatch.setattr(subprocess, "Popen", mock_popen)
    h = RepHandler(
        spec_path="s", ll1_path="l",
        interpreter=_make_interpreter(),
        verbose_format="text",
        child_flags=["--verbose"],
    )
    h.feed(b"x\n", "-")
    assert any("--verbose" in c for c in calls)


def test_feed_reformats_child_verbose_events(monkeypatch, capsys):
    verbose = VerboseContext("test", None, level=1, fmt="text")
    h = RepHandler(
        spec_path="build/spec.json",
        ll1_path="build/ll1.json",
        interpreter=_make_interpreter(),
        verbose_format="text",
        verbose=verbose,
    )
    tokens_stderr = (
        b'{"stage": "plcc-tokens", "event": "started", "message": "tokenizing"}\n'
    )
    procs = iter([
        _proc(stderr=tokens_stderr),
        _proc(stdout=_tree_record(), stderr=b""),
    ])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    h.feed(b"42\n", "-")
    _, err = capsys.readouterr()
    assert "plcc-tokens: started: tokenizing" in err


# --- error location format ---

def test_feed_error_shows_location_in_stdout(monkeypatch, handler, capsys):
    h, _ = handler
    procs = iter([_proc(), _proc(stdout=_error_record_with_source("bad char", file="-", line=1, col=1))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    h.feed(b"@\n", "-")
    out, _ = capsys.readouterr()
    assert "-:1:1" in out


def test_feed_error_renders_file_line_col(monkeypatch, handler, capsys):
    h, _ = handler
    procs = iter([_proc(), _proc(stdout=_error_record_with_source("bad", file="foo.txt", line=3, col=7))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    h.feed(b"bad\n", "-")
    out, _ = capsys.readouterr()
    assert "foo.txt:3:7" in out
    assert "bad" in out


def test_feed_error_with_no_location_shows_stage(monkeypatch, handler, capsys):
    h, _ = handler
    procs = iter([_proc(), _proc(stdout=_error_record("bad char", stage="plcc-tokens"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    h.feed(b"@\n", "-")
    out, _ = capsys.readouterr()
    assert "plcc-tokens: error: bad char" in out


def test_feed_exits_130_when_interpreter_killed_by_signal(monkeypatch, capsys):
    interp = _make_dead_interpreter(returncode=-2)  # SIGINT on Unix
    h = RepHandler(
        spec_path="build/spec.json",
        ll1_path="build/ll1.json",
        interpreter=interp,
        verbose_format="text",
    )
    procs = iter([_proc(), _proc(stdout=_tree_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    with pytest.raises(SystemExit) as exc_info:
        h.feed(b"42\n", "-")
    assert exc_info.value.code == 130
    _, err = capsys.readouterr()
    assert "unexpectedly" not in err


def test_feed_exits_130_when_interpreter_exits_130(monkeypatch, capsys):
    interp = _make_dead_interpreter(returncode=130)
    h = RepHandler(
        spec_path="build/spec.json",
        ll1_path="build/ll1.json",
        interpreter=interp,
        verbose_format="text",
    )
    procs = iter([_proc(), _proc(stdout=_tree_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    with pytest.raises(SystemExit) as exc_info:
        h.feed(b"42\n", "-")
    assert exc_info.value.code == 130
    _, err = capsys.readouterr()
    assert "unexpectedly" not in err


def test_feed_stops_at_first_error(monkeypatch, handler, capsys):
    # Two error records arrive. Only the first should be printed.
    h, _ = handler
    two_errors = (
        _error_record_with_source("first error", col=1) +
        _error_record_with_source("second error", col=2)
    )
    procs = iter([_proc(), _proc(stdout=two_errors)])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    h.feed(b"ab\n", "-")
    out, _ = capsys.readouterr()
    assert "first error" in out
    assert "second error" not in out


def test_render_record_interpreter_error_writes_to_stdout(capsys):
    record = {"kind": "error", "type": "TypeError", "message": "bad value"}
    _rep_module._render_record(record, "text")
    out, err = capsys.readouterr()
    assert "TypeError" in out
    assert "bad value" in out
    assert err == ""
