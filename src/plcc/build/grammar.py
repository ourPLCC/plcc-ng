# src/plcc/build/grammar.py
from pathlib import Path

_GRAMMAR_FILE = ".grammar"
DEFAULT_GRAMMAR_FILE = "spec.plcc"


def read_grammar(build_dir):
    p = Path(build_dir) / _GRAMMAR_FILE
    try:
        return p.read_text().strip() or None
    except FileNotFoundError:
        return None


def write_grammar(build_dir, path):
    (Path(build_dir) / _GRAMMAR_FILE).write_text(path)


def resolve_grammar_path(explicit, stored):
    if explicit is not None:
        return explicit
    elif stored is not None:
        return stored
    else:
        return DEFAULT_GRAMMAR_FILE
