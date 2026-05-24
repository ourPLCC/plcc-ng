import json
import pytest
from pathlib import Path
from plcc.build.staleness import (
    compute_hash, read_sentinel, write_sentinel, delete_sentinel, is_current,
)


def test_compute_hash_returns_hex_string(tmp_path):
    f = tmp_path / "spec.json"
    f.write_text('{"x": 1}')
    h = compute_hash(f)
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_compute_hash_same_content_same_hash(tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text("hello")
    b.write_text("hello")
    assert compute_hash(a) == compute_hash(b)


def test_compute_hash_different_content_different_hash(tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text("hello")
    b.write_text("world")
    assert compute_hash(a) != compute_hash(b)


def test_read_sentinel_returns_none_when_absent(tmp_path):
    assert read_sentinel(tmp_path) is None


def test_read_sentinel_returns_none_on_malformed_json(tmp_path):
    (tmp_path / ".spec-hash").write_text("not json")
    assert read_sentinel(tmp_path) is None


def test_write_then_read_sentinel_roundtrips(tmp_path):
    write_sentinel(tmp_path, "abc123", {"scan", "parse"})
    s = read_sentinel(tmp_path)
    assert s == {"hash": "abc123", "stages": ["parse", "scan"]}  # sorted


def test_delete_sentinel_removes_file(tmp_path):
    write_sentinel(tmp_path, "abc123", {"scan"})
    delete_sentinel(tmp_path)
    assert read_sentinel(tmp_path) is None


def test_delete_sentinel_is_idempotent(tmp_path):
    delete_sentinel(tmp_path)


def test_is_current_false_when_sentinel_none():
    assert not is_current(None, "abc", {"scan"})


def test_is_current_false_when_hash_differs():
    s = {"hash": "old", "stages": ["scan", "parse"]}
    assert not is_current(s, "new", {"scan"})


def test_is_current_true_when_required_stages_are_subset_of_completed():
    s = {"hash": "abc", "stages": ["scan", "parse", "model", "diagram"]}
    assert is_current(s, "abc", {"scan"})
    assert is_current(s, "abc", {"scan", "parse"})
    assert is_current(s, "abc", {"scan", "model", "diagram"})
    assert is_current(s, "abc", {"scan", "parse", "model", "diagram"})


def test_is_current_false_when_required_stage_missing():
    s = {"hash": "abc", "stages": ["scan", "parse"]}
    assert not is_current(s, "abc", {"scan", "parse", "model"})
    assert not is_current(s, "abc", {"scan", "model", "diagram"})


def test_is_current_false_when_unknown_stage_required():
    s = {"hash": "abc", "stages": ["scan", "parse", "model", "diagram"]}
    assert not is_current(s, "abc", {"scan", "java"})


def test_all_stages_present_is_current():
    s = {"hash": "abc", "stages": ["scan", "parse", "model", "diagram", "java"]}
    assert is_current(s, "abc", {"scan", "parse", "model", "diagram", "java"})


def test_diagram_stored_is_not_current_for_all_with_tools():
    s = {"hash": "abc", "stages": ["scan", "model", "diagram"]}
    assert not is_current(s, "abc", {"scan", "parse", "model", "diagram", "java"})


def test_all_stored_is_current_for_diagram():
    s = {"hash": "abc", "stages": ["scan", "parse", "model", "diagram", "java"]}
    assert is_current(s, "abc", {"scan", "model", "diagram"})
