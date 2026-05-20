import json
import subprocess
import sys

import pytest

from .pipeline import TreePipeline, print_parse_error
from ._test_helpers import (
    _proc, _tree_record, _error_record, _error_record_with_source,
    _eof_error_record,
)


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


# --- print_parse_error ---

def test_print_parse_error_shows_location(capsys):
    record = {"kind": "error", "message": "bad char",
              "source": {"file": "foo.txt", "line": 3, "column": 7}}
    print_parse_error(record, default_stage="plcc-test")
    _, err = capsys.readouterr()
    assert "plcc-test: foo.txt:3:7: error: bad char" in err


def test_print_parse_error_normalises_stdin_to_dash(capsys):
    record = {"kind": "error", "message": "oops",
              "source": {"file": "-", "line": 1, "column": 1}}
    print_parse_error(record, default_stage="plcc-test")
    _, err = capsys.readouterr()
    assert "plcc-test: -:1:1: error: oops" in err


def test_print_parse_error_shows_stage_and_location_together(capsys):
    record = {"kind": "error", "stage": "plcc-tokens", "message": "unrecognized character 'a'",
              "source": {"file": "-", "line": 1, "column": 1}}
    print_parse_error(record, default_stage="plcc-parse")
    _, err = capsys.readouterr()
    assert "plcc-tokens: -:1:1: error: unrecognized character 'a'" in err


def test_print_parse_error_uses_stage_when_no_location(capsys):
    record = {"kind": "error", "message": "bad", "stage": "plcc-tokens"}
    print_parse_error(record, default_stage="plcc-test")
    _, err = capsys.readouterr()
    assert "plcc-tokens: error: bad" in err


def test_print_parse_error_uses_default_stage_when_no_stage_and_no_location(capsys):
    record = {"kind": "error", "message": "bad"}
    print_parse_error(record, default_stage="plcc-test")
    _, err = capsys.readouterr()
    assert "plcc-test: error: bad" in err
