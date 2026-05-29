# src/plcc/build/grammar.py
from pathlib import Path

_GRAMMAR_FILE = ".grammar"


def read_grammar(build_dir):
    p = Path(build_dir) / _GRAMMAR_FILE
    try:
        return p.read_text().strip()
    except FileNotFoundError:
        return None


def write_grammar(build_dir, path):
    (Path(build_dir) / _GRAMMAR_FILE).write_text(path)
