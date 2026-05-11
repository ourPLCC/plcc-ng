import hashlib
import json
from pathlib import Path

_SENTINEL = ".spec-hash"
_LEVELS = {"scan": 0, "parse": 1, "all": 2}


def compute_hash(path: Path | str) -> str:
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
    # -1 sentinel: unknown level names are treated as below "scan" (level 0), so unknown
    # level names will produce False (stale), which is the safe default.
    stored = _LEVELS.get(sentinel.get("through", ""), -1)
    requested = _LEVELS.get(through, -1)
    # If either is unknown (-1), treat as stale (False)
    if stored == -1 or requested == -1:
        return False
    return stored >= requested
