import hashlib
import json
from pathlib import Path

_SENTINEL = ".spec-hash"


def compute_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_sentinel(build_dir):
    p = Path(build_dir) / _SENTINEL
    try:
        return json.loads(p.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def write_sentinel(build_dir, hash_, stages):
    (Path(build_dir) / _SENTINEL).write_text(
        json.dumps({"hash": hash_, "stages": sorted(stages)})
    )


def delete_sentinel(build_dir):
    try:
        (Path(build_dir) / _SENTINEL).unlink()
    except FileNotFoundError:
        pass


def is_current(sentinel, hash_, required_stages):
    if sentinel is None:
        return False
    if sentinel.get("hash") != hash_:
        return False
    completed = set(sentinel.get("stages", []))
    return required_stages.issubset(completed)
