# src/plcc/build/spec.py
from pathlib import Path

_SPEC_FILE = ".spec"
DEFAULT_SPEC_FILE = "spec.plcc"


def read_spec(build_dir):
    p = Path(build_dir) / _SPEC_FILE
    try:
        return p.read_text().strip() or None
    except FileNotFoundError:
        return None


def write_spec(build_dir, path):
    (Path(build_dir) / _SPEC_FILE).write_text(path)


def resolve_spec_path(explicit, stored):
    if explicit is not None:
        return explicit
    elif stored is not None:
        return stored
    else:
        return DEFAULT_SPEC_FILE
