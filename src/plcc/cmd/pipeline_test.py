import json
import subprocess
import sys

import pytest

from .pipeline import TreePipeline, print_parse_error, split_committed, slice_from_source
from ._test_helpers import (
    _proc, _tree_record, _error_record, _error_record_with_source,
    _eof_error_record, _hold_record,
)
from plcc.verbose import VerboseContext


@pytest.fixture()
def pipeline():
    return TreePipeline(spec_path="build/spec.json", ll1_path="build/ll1.json")


# --- TreePipeline.run() ---

def test_run_returns_none_when_no_output(monkeypatch, pipeline):
    procs = iter([_proc(), _proc(stdout=b"")])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    assert pipeline.run(b"x\n") is None


def test_run_returns_none_for_eof_only_error_when_trial(monkeypatch, pipeline):
    procs = iter([_proc(), _proc(stdout=_eof_error_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    assert pipeline.run(b"1+\n", eof=False) is None


def test_run_returns_list_for_eof_only_error_when_force_submit(monkeypatch, pipeline):
    procs = iter([_proc(), _proc(stdout=_eof_error_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    result = pipeline.run(b"1+\n", eof=True)
    assert result is not None
    assert len(result) == 1
    assert result[0][0].get("kind") == "error"


def test_run_returns_list_for_genuine_error_when_trial(monkeypatch, pipeline):
    procs = iter([_proc(), _proc(stdout=_error_record("bad token"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    result = pipeline.run(b"@\n", eof=False)
    assert result is not None
    assert result[0][0].get("kind") == "error"


def test_run_returns_list_for_tree(monkeypatch, pipeline):
    procs = iter([_proc(), _proc(stdout=_tree_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    result = pipeline.run(b"1\n")
    assert result is not None
    assert result[0][0].get("kind") == "tree"


def test_run_preserves_raw_bytes_for_tree(monkeypatch, pipeline):
    raw = _tree_record()
    procs = iter([_proc(), _proc(stdout=raw)])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    result = pipeline.run(b"1\n")
    record, raw_bytes = result[0]
    assert b"tree" in raw_bytes
    assert json.loads(raw_bytes) == record


def test_run_passes_child_flags_to_subprocesses(monkeypatch):
    calls = []

    def mock_popen(args, **kwargs):
        calls.append(list(args))
        return _proc()

    monkeypatch.setattr(subprocess, "Popen", mock_popen)
    p = TreePipeline(spec_path="s", ll1_path="l", child_flags=["--flag"])
    p.run(b"x\n")
    assert all("--flag" in c for c in calls)


def test_run_returns_multiple_records(monkeypatch, pipeline):
    combined = _tree_record() + _error_record_with_source("trailing")
    procs = iter([_proc(), _proc(stdout=combined)])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    result = pipeline.run(b"x\n")
    assert result is not None
    assert len(result) == 2


def test_run_reformats_child_verbose_events_when_verbose_set(monkeypatch, capsys):
    verbose = VerboseContext("test", None, level=1, fmt="text")
    tokens_stderr = (
        b'{"stage": "plcc-tokens", "event": "started", "message": "tokenizing"}\n'
    )
    procs = iter([
        _proc(stderr=tokens_stderr),
        _proc(stdout=_tree_record(), stderr=b""),
    ])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    p = TreePipeline(spec_path="s", ll1_path="l", verbose=verbose)
    p.run(b"1\n")
    _, err = capsys.readouterr()
    assert "plcc-tokens: started: tokenizing" in err


def test_run_suppresses_child_verbose_events_on_eof_probe(monkeypatch, capsys):
    verbose = VerboseContext("test", None, level=1, fmt="text")
    tokens_stderr = (
        b'{"stage": "plcc-tokens", "event": "started", "message": "tokenizing"}\n'
    )
    procs = iter([
        _proc(stderr=tokens_stderr),
        _proc(stdout=_eof_error_record(), stderr=b""),
    ])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    p = TreePipeline(spec_path="s", ll1_path="l", verbose=verbose)
    result = p.run(b"1+\n", eof=False)
    assert result is None
    _, err = capsys.readouterr()
    assert err == ""


def test_run_does_not_reformat_when_verbose_is_none(monkeypatch, capsys):
    tokens_stderr = (
        b'{"stage": "plcc-tokens", "event": "started", "message": "tokenizing"}\n'
    )
    procs = iter([
        _proc(stderr=tokens_stderr),
        _proc(stdout=_tree_record(), stderr=b""),
    ])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    p = TreePipeline(spec_path="s", ll1_path="l")  # verbose=None default
    result = p.run(b"1\n")
    assert result is not None
    _, err = capsys.readouterr()
    assert err == ""


def test_run_does_not_pipe_stderr_when_verbose_is_none(monkeypatch):
    popen_kwargs = []

    def mock_popen(args, **kwargs):
        popen_kwargs.append(kwargs)
        return _proc()

    monkeypatch.setattr(subprocess, "Popen", mock_popen)
    TreePipeline(spec_path="s", ll1_path="l").run(b"x\n")
    assert all(kw.get("stderr") is None for kw in popen_kwargs)


def test_run_pipes_stderr_when_verbose_is_set(monkeypatch):
    verbose = VerboseContext("test", None, level=1, fmt="text")
    popen_kwargs = []

    def mock_popen(args, **kwargs):
        popen_kwargs.append(kwargs)
        return _proc(stdout=_tree_record() if "plcc-trees" in args[0] else b"")

    monkeypatch.setattr(subprocess, "Popen", mock_popen)
    TreePipeline(spec_path="s", ll1_path="l", verbose=verbose).run(b"1\n")
    assert all(kw.get("stderr") is subprocess.PIPE for kw in popen_kwargs)


# --- print_parse_error ---

def test_print_parse_error_shows_location(capsys):
    record = {"kind": "error", "message": "bad char",
              "source": {"file": "foo.txt", "line": 3, "column": 7}}
    print_parse_error(record, default_stage="plcc-test")
    out, _ = capsys.readouterr()
    assert "plcc-test: foo.txt:3:7: error: bad char" in out


def test_print_parse_error_normalises_stdin_to_dash(capsys):
    record = {"kind": "error", "message": "oops",
              "source": {"file": "-", "line": 1, "column": 1}}
    print_parse_error(record, default_stage="plcc-test")
    out, _ = capsys.readouterr()
    assert "plcc-test: -:1:1: error: oops" in out


def test_print_parse_error_shows_stage_and_location_together(capsys):
    record = {"kind": "error", "stage": "plcc-tokens", "message": "unrecognized character 'a'",
              "source": {"file": "-", "line": 1, "column": 1}}
    print_parse_error(record, default_stage="plcc-parse")
    out, _ = capsys.readouterr()
    assert "plcc-tokens: -:1:1: error: unrecognized character 'a'" in out


def test_print_parse_error_uses_stage_when_no_location(capsys):
    record = {"kind": "error", "message": "bad", "stage": "plcc-tokens"}
    print_parse_error(record, default_stage="plcc-test")
    out, _ = capsys.readouterr()
    assert "plcc-tokens: error: bad" in out


def test_print_parse_error_uses_default_stage_when_no_stage_and_no_location(capsys):
    record = {"kind": "error", "message": "bad"}
    print_parse_error(record, default_stage="plcc-test")
    out, _ = capsys.readouterr()
    assert "plcc-test: error: bad" in out


# --- split_committed and slice_from_source ---


def _items(*raws):
    """Build (record, raw) pairs from raw JSONL byte chunks (one record each)."""
    out = []
    for raw in raws:
        line = raw.strip()
        out.append((json.loads(line), line))
    return out


def test_slice_from_source_single_line():
    assert slice_from_source(b"3 + 4\n", {"line": 1, "column": 5}) == b"4\n"


def test_slice_from_source_multiline():
    assert slice_from_source(b"a\nbc\n", {"line": 2, "column": 2}) == b"c\n"


def test_slice_from_source_without_position_returns_all():
    assert slice_from_source(b"abc", {}) == b"abc"


def test_split_eof_dispatches_all_and_strips_hold():
    items = _items(_tree_record(), _hold_record())
    dispatch, remainder = split_committed(items, b"3\n", eof=True)
    assert [r.get("kind") for r, _ in dispatch] == ["tree"]
    assert remainder == b""


def test_split_trial_holds_trailing_extensible_tree():
    items = _items(_tree_record(), _hold_record(line=1, col=1))
    dispatch, remainder = split_committed(items, b"3\n", eof=False)
    assert dispatch == []           # the extensible tree is held, not dispatched
    assert remainder == b"3\n"


def test_split_trial_commits_leading_tree_holds_incomplete():
    # A committed final tree followed by a trailing incomplete fragment at col 3.
    eof_err = json.dumps({
        "kind": "error", "stage": "plcc-parser-table", "found": "eof",
        "message": "unexpected end of input",
        "source": {"file": "-", "line": 1, "column": 4},
        "start": {"file": "-", "line": 1, "column": 3},
    }).encode() + b"\n"
    items = _items(_tree_record(), eof_err)
    dispatch, remainder = split_committed(items, b"5;1+\n", eof=False)
    assert [r.get("kind") for r, _ in dispatch] == ["tree"]
    assert remainder == b"1+\n"


def test_split_trial_commits_final_tree_no_remainder():
    items = _items(_tree_record())   # final tree, no hold marker
    dispatch, remainder = split_committed(items, b"42\n", eof=False)
    assert [r.get("kind") for r, _ in dispatch] == ["tree"]
    assert remainder == b""


def test_split_trial_commits_genuine_error_no_remainder():
    items = _items(_error_record("bad token"))
    dispatch, remainder = split_committed(items, b"@\n", eof=False)
    assert [r.get("kind") for r, _ in dispatch] == ["error"]
    assert remainder == b""
