import io
import json

import pytest

from .emit import main as run_main


def _run_emit(monkeypatch, tmp_path, model):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])


def _minimal_model():
    return {
        "start": "prog",
        "classes": [
            {
                "name": "Prog",
                "extends": None,
                "abstract": False,
                "rule_name": "prog",
                "fields": [{"name": "expr", "type": "Expr", "is_list": False}],
            },
            {
                "name": "Expr",
                "extends": None,
                "abstract": True,
                "rule_name": "expr",
                "fields": [],
            },
            {
                "name": "NumExpr",
                "extends": "Expr",
                "abstract": False,
                "rule_name": "expr",
                "fields": [{"name": "num", "type": "Token", "is_list": False}],
            },
        ],
        "semantic_sections": [],
    }


def test_emit_writes_cabal_file(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    assert (tmp_path / 'interpreter.cabal').exists()


def test_cabal_file_contains_executable(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'interpreter.cabal').read_text()
    assert 'executable interpreter' in text


def test_cabal_file_contains_aeson_dep(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'interpreter.cabal').read_text()
    assert 'aeson' in text


def test_cabal_file_lists_token_module(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'interpreter.cabal').read_text()
    assert 'Token' in text


def test_emit_copies_token_hs(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    assert (tmp_path / 'Token.hs').exists()


def test_token_hs_contains_token_module(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Token.hs').read_text()
    assert 'module Token' in text
