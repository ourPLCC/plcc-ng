import json
import subprocess
import sys

import pytest

from plcc.verbose import VerboseContext
from .parse import ParseHandler
from ._test_helpers import (
    _proc, _tree_record, _error_record, _error_record_with_source,
    _eof_error_record,
)


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


def test_feed_prints_error_to_stdout(monkeypatch, handler, capsys):
    procs = iter([_proc(), _proc(stdout=_error_record("oops"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"bad\n", "-")
    out, _ = capsys.readouterr()
    assert "oops" in out


def test_feed_error_shows_location_in_stdout(monkeypatch, handler, capsys):
    procs = iter([_proc(), _proc(stdout=_error_record_with_source("bad char", file="-", line=1, col=1))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"@\n", "-")
    out, _ = capsys.readouterr()
    assert "-:1:1" in out


def test_feed_error_renders_file_line_col(monkeypatch, handler, capsys):
    procs = iter([_proc(), _proc(stdout=_error_record_with_source("bad", file="foo.txt", line=3, col=7))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"bad\n", "-")
    out, _ = capsys.readouterr()
    assert "foo.txt:3:7" in out
    assert "bad" in out


def test_feed_mixed_tree_and_error_renders_both(monkeypatch, handler, capsys):
    combined = _tree_record() + _error_record_with_source("trailing")
    procs = iter([_proc(), _proc(stdout=combined)])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"input\n", "-")
    out, _ = capsys.readouterr()
    assert "program" in out
    assert "trailing" in out
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
    out, _ = capsys.readouterr()
    assert "plcc-tokens: error: bad char" in out


def test_feed_returns_false_for_eof_only_error_when_trial(monkeypatch, handler):
    procs = iter([_proc(), _proc(stdout=_eof_error_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    assert handler.feed(b"1+\n", "-", eof=False) is False


def test_feed_returns_true_for_eof_only_error_when_force_submit(monkeypatch, handler):
    procs = iter([_proc(), _proc(stdout=_eof_error_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    assert handler.feed(b"1+\n", "-", eof=True) is True


def test_feed_suppresses_output_for_eof_error_when_trial(monkeypatch, handler, capsys):
    procs = iter([_proc(), _proc(stdout=_eof_error_record("expected PLUS"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"1+\n", "-", eof=False)
    out, _ = capsys.readouterr()
    assert out == ""


def test_feed_shows_output_for_eof_error_when_force_submit(monkeypatch, handler, capsys):
    procs = iter([_proc(), _proc(stdout=_eof_error_record("expected PLUS"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"1+\n", "-", eof=True)
    out, _ = capsys.readouterr()
    assert "expected PLUS" in out


def test_feed_returns_true_for_genuine_error_regardless_of_eof_param(monkeypatch, handler):
    procs = iter([_proc(), _proc(stdout=_error_record("bad token"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    # _error_record has no "found" field → genuine error → always True
    assert handler.feed(b"@\n", "-", eof=False) is True


def test_feed_prints_empty_annotation_for_childless_tree(monkeypatch, handler, capsys):
    childless_tree = json.dumps({
        "kind": "tree", "rule": "exp2",
        "source": {}, "children": []
    }).encode() + b"\n"
    procs = iter([_proc(), _proc(stdout=childless_tree)])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"1\n", "-")
    out, _ = capsys.readouterr()
    assert "exp2 (empty)" in out


def test_feed_does_not_annotate_tree_with_children(monkeypatch, handler, capsys):
    token_child = {"kind": "token", "name": "NUM", "lexeme": "1",
                   "source": {"file": "-", "line": 1, "column": 1}}
    tree_with_child = json.dumps({
        "kind": "tree", "rule": "exp",
        "source": {}, "children": [["n", token_child]]
    }).encode() + b"\n"
    procs = iter([_proc(), _proc(stdout=tree_with_child)])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"1\n", "-")
    out, _ = capsys.readouterr()
    assert "exp (empty)" not in out
    assert "exp\n" in out or out.startswith("exp")


def test_feed_reformats_child_verbose_events(monkeypatch, capsys):
    verbose = VerboseContext("test", None, level=1, fmt="text")
    handler = ParseHandler(
        spec_path="build/spec.json",
        ll1_path="build/ll1.json",
        child_flags=[],
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
    handler.feed(b"1\n", "-")
    _, err = capsys.readouterr()
    assert "plcc-tokens: started: tokenizing" in err


def test_feed_stops_at_first_error(monkeypatch, handler, capsys):
    # Two error records arrive (e.g. two lex errors from 'ab').
    # Only the first should be printed; the second is silently dropped.
    two_errors = (
        _error_record_with_source("first error", col=1) +
        _error_record_with_source("second error", col=2)
    )
    procs = iter([_proc(), _proc(stdout=two_errors)])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"ab\n", "-")
    out, _ = capsys.readouterr()
    assert "first error" in out
    assert "second error" not in out
