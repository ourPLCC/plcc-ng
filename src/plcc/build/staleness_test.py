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
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    a.write_text("hello")
    b.write_text("hello")
    assert compute_hash(a) == compute_hash(b)


def test_compute_hash_different_content_different_hash(tmp_path):
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    a.write_text("hello")
    b.write_text("world")
    assert compute_hash(a) != compute_hash(b)


def test_read_sentinel_returns_none_when_absent(tmp_path):
    assert read_sentinel(tmp_path) is None


def test_read_sentinel_returns_none_on_malformed_json(tmp_path):
    (tmp_path / ".spec-hash").write_text("not json")
    assert read_sentinel(tmp_path) is None


def test_write_then_read_sentinel_roundtrips(tmp_path):
    write_sentinel(tmp_path, "abc123", "all")
    s = read_sentinel(tmp_path)
    assert s == {"hash": "abc123", "through": "all"}


def test_delete_sentinel_removes_file(tmp_path):
    write_sentinel(tmp_path, "abc123", "all")
    delete_sentinel(tmp_path)
    assert read_sentinel(tmp_path) is None


def test_delete_sentinel_is_idempotent(tmp_path):
    delete_sentinel(tmp_path)  # no error when absent


def test_is_current_false_when_sentinel_none():
    assert not is_current(None, "abc", "all")


def test_is_current_false_when_hash_differs():
    s = {"hash": "old", "through": "all"}
    assert not is_current(s, "new", "all")


def test_is_current_true_when_hash_matches_and_level_sufficient():
    s = {"hash": "abc", "through": "all"}
    assert is_current(s, "abc", "scan")
    assert is_current(s, "abc", "parse")
    assert is_current(s, "abc", "all")


def test_is_current_false_when_stored_level_insufficient():
    s = {"hash": "abc", "through": "scan"}
    assert not is_current(s, "abc", "parse")
    assert not is_current(s, "abc", "all")


def test_is_current_scan_satisfies_scan():
    s = {"hash": "abc", "through": "scan"}
    assert is_current(s, "abc", "scan")


def test_is_current_parse_satisfies_scan_and_parse():
    s = {"hash": "abc", "through": "parse"}
    assert is_current(s, "abc", "scan")
    assert is_current(s, "abc", "parse")
    assert not is_current(s, "abc", "all")
