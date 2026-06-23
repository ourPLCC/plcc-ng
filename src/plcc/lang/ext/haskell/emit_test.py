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


def test_emit_writes_module_for_abstract_rule(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    assert (tmp_path / 'Expr.hs').exists()


def test_abstract_module_contains_data_declaration(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert 'data Expr' in text


def test_abstract_module_contains_concrete_constructor(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert 'NumExpr' in text


def test_concrete_constructor_has_token_field(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert 'num :: Token' in text


def test_emit_writes_module_for_lone_concrete(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    assert (tmp_path / 'Prog.hs').exists()


def test_lone_concrete_module_contains_data_declaration(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Prog.hs').read_text()
    assert 'data Prog' in text


def test_lone_concrete_field_uses_class_type(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Prog.hs').read_text()
    assert 'expr :: Expr' in text


def test_all_types_derive_show_and_eq(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    for path in [tmp_path / 'Expr.hs', tmp_path / 'Prog.hs']:
        text = path.read_text()
        assert 'deriving (Show, Eq)' in text


def test_abstract_module_has_from_json_instance(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert 'instance FromJSON Expr' in text


def test_from_json_matches_on_rule_name(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert '"expr"' in text


def test_from_json_matches_constructor_by_sorted_field_names(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert '["num"]' in text
    assert 'NumExpr' in text


def test_lone_concrete_has_from_json_instance(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Prog.hs').read_text()
    assert 'instance FromJSON Prog' in text


def test_from_json_uses_parse_field(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert 'parseField' in text


def test_from_json_parses_children_as_pairs(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert 'parseChildren' in text


def test_list_field_uses_bracket_type(monkeypatch, tmp_path):
    model = {
        "start": "stmts",
        "classes": [
            {
                "name": "Stmts",
                "extends": None,
                "abstract": False,
                "rule_name": "stmts",
                "fields": [{"name": "items", "type": "Token", "is_list": True}],
            }
        ],
        "semantic_sections": [],
    }
    _run_emit(monkeypatch, tmp_path, model)
    text = (tmp_path / 'Stmts.hs').read_text()
    assert 'items :: [Token]' in text
