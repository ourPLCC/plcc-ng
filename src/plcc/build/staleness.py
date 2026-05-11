import hashlib
import json
from pathlib import Path

_SENTINEL = ".spec-hash"
_LEVELS = {"scan": 0, "parse": 1, "all": 2}


def compute_hash(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_sentinel(build_dir) -> dict | None:
    p = Path(build_dir) / _SENTINEL
    try:
        return json.loads(p.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def write_sentinel(build_dir, hash_: str, through: str) -> None:
    (Path(build_dir) / _SENTINEL).write_text(
        json.dumps({"hash": hash_, "through": through})
    )


def delete_sentinel(build_dir) -> None:
    try:
        (Path(build_dir) / _SENTINEL).unlink()
    except FileNotFoundError:
        pass


def is_current(sentinel: dict | None, new_hash: str, through: str) -> bool:
    if sentinel is None:
        return False
    if sentinel.get("hash") != new_hash:
        return False
    stored = _LEVELS.get(sentinel.get("through", ""), -1)
    requested = _LEVELS.get(through, -1)
    return stored >= requested
